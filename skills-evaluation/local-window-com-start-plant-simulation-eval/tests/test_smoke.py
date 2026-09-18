#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke tests for the local-window-com-start-plant-simulation eval
framework itself.

These tests verify the *framework* — the runner, grader, mock shim, and
reporters — not the skill under test. They use a tiny fake script that
exits with a known code and prints known strings, so the framework can
be exercised in any environment without a real Plant Simulation.

Run from the eval root:
    python3 tests/test_smoke.py
or:
    python3 -m unittest tests/test_smoke.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Make eval/ importable when run as a script.
_HERE = Path(__file__).resolve()
_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_ROOT))

from eval.grader import grade  # noqa: E402
from eval.reporter import (  # noqa: E402
    aggregate,
    diff_snapshots,
    render_per_task_md,
    render_summary_md,
    write_reports,
)
from eval.runner import (  # noqa: E402
    RunConfig,
    run_all,
    tempfile_for_iteration,
)
from eval.stats import (  # noqa: E402
    bucket_histogram,
    compute_task_stats,
    weighted_pass_rate,
    wilson_ci,
)
from eval.task import (  # noqa: E402
    Expected,
    Task,
    TaskSuite,
    filter_suites,
    load_all_suites,
    load_suite,
)


# --- Tiny fake script used by the runner tests ------------------------------

_FAKE_SCRIPT = '''#!/usr/bin/env python3
"""A fake skill script used by the eval framework's self-tests.

It is intentionally trivial: it parses two args (--model, --simtalkclaudefile),
exits 0 if both look non-empty, 2 if either is missing, 4 if either contains
the literal string 'NOTFOUND', 5 on any other error.

It writes 'OK' to stdout and 'PROGRESS: <msg>' to stderr (testing the
stdout/stderr discipline).
"""
import sys

# Simulate pywin32 missing? In the test env we let the real pywin32 import
# fall through; the script doesn't actually import win32com.
try:
    args = sys.argv[1:]
except Exception:
    sys.exit(5)

# Fake 'COM call' to test that the shim's isfile stub gets hit.
import os.path
model = None
pslib = None
port = 50007
for i, a in enumerate(args):
    if a in ("-m", "--model") and i + 1 < len(args):
        model = args[i + 1]
    if a in ("-s", "--simtalkclaudefile") and i + 1 < len(args):
        pslib = args[i + 1]
    if a in ("-p", "--port") and i + 1 < len(args):
        try:
            port = int(args[i + 1])
        except ValueError:
            print("invalid int value: " + args[i + 1], file=sys.stderr)
            sys.exit(2)
        if not (1 <= port <= 65535):
            print(f"Port must be in 1..65535, got {port}", file=sys.stderr)
            sys.exit(2)

if not model:
    print("Error: --model is required", file=sys.stderr)
    sys.exit(2)
if not pslib:
    print("Error: --simtalkclaudefile is required", file=sys.stderr)
    sys.exit(2)

if "NOTFOUND" in model:
    print(f"Error: Model file not found: {os.path.abspath(model)}", file=sys.stderr)
    sys.exit(4)
if "NOTFOUND" in pslib:
    print(f"Error: SimtalkClaude library not found: {os.path.abspath(pslib)}", file=sys.stderr)
    sys.exit(4)

# Simulate a successful run.
print("PROGRESS: COM dispatch OK", file=sys.stderr)
print(f"Plant Simulation launched, model loaded, socket port set to {port}.")
sys.exit(0)
'''


def _write_fake_script(tmp: Path) -> Path:
    p = tmp / "fake_skill.py"
    p.write_text(_FAKE_SCRIPT, encoding="utf-8")
    return p


# --- Stats tests -------------------------------------------------------------


class TestStats(unittest.TestCase):
    def test_wilson_ci_basic(self):
        lo, hi = wilson_ci(0.5, 4)
        self.assertGreater(lo, 0.0)
        self.assertLess(hi, 1.0)
        self.assertLess(lo, hi)

    def test_wilson_ci_zero(self):
        lo, hi = wilson_ci(0.0, 5)
        self.assertEqual(lo, 0.0)

    def test_weighted_pass_rate(self):
        self.assertAlmostEqual(
            weighted_pass_rate([(1.0, 1.0), (1.0, 0.5)]), 0.75
        )
        self.assertEqual(weighted_pass_rate([]), 0.0)

    def test_compute_task_stats(self):
        s = compute_task_stats(
            "t", ["pass", "pass", "fail", "pass"], [100, 110, 200, 105],
            task_category="cli-validation",
        )
        self.assertEqual(s.n, 4)
        self.assertEqual(s.n_pass, 3)
        self.assertAlmostEqual(s.pass_rate, 0.75)
        # 0.75 < 0.80 → flaky
        self.assertTrue(s.is_flaky)
        self.assertFalse(s.is_slow)  # median 105ms < 2*3000=6000ms

    def test_bucket_histogram(self):
        h = bucket_histogram(["a", "b", "a", "c", "a"])
        self.assertEqual(h, {"a": 3, "b": 1, "c": 1})


# --- Task loader tests -------------------------------------------------------


class TestTaskLoader(unittest.TestCase):
    def test_load_suite(self):
        suite = load_suite(_ROOT / "tasks" / "01-cli-validation.json")
        self.assertGreater(suite.n_tasks, 0)
        self.assertEqual(suite.tasks[0].category, "cli-validation")

    def test_load_all_suites(self):
        suites = load_all_suites(_ROOT / "tasks")
        self.assertGreater(len(suites), 0)
        total = sum(s.n_tasks for s in suites)
        self.assertGreater(total, 0)

    def test_filter_by_tag(self):
        suites = load_all_suites(_ROOT / "tasks")
        smoke = filter_suites(suites, tag="smoke")
        self.assertGreater(len(smoke), 0)
        for t in smoke:
            self.assertIn("smoke", t.tags)

    def test_filter_by_id_substr(self):
        suites = load_all_suites(_ROOT / "tasks")
        cli = filter_suites(suites, task_id_substr="cli-")
        self.assertGreater(len(cli), 0)
        for t in cli:
            self.assertIn("cli-", t.id)

    def test_task_from_dict_validates_args(self):
        with self.assertRaises(ValueError):
            Task.from_dict({
                "id": "bad", "category": "cli-validation", "name": "x",
                "args": "not a list", "mock": True,
                "expected": {"exit_code": 2},
            })

    def test_task_from_dict_requires_expected(self):
        with self.assertRaises(ValueError):
            Task.from_dict({
                "id": "bad", "category": "cli-validation", "name": "x",
                "args": [], "mock": True, "expected": {},
            })

    def test_task_from_dict_requires_mock_field(self):
        with self.assertRaises(ValueError):
            Task.from_dict({
                "id": "bad", "category": "cli-validation", "name": "x",
                "args": [], "expected": {"exit_code": 0},
            })


# --- Grader tests ------------------------------------------------------------


class TestGrader(unittest.TestCase):
    def _task(self, **kwargs) -> Task:
        defaults = dict(
            id="t1",
            category="cli-validation",
            name="t1",
            args=[],
            mock=True,
            expected=Expected(exit_code=0),
            timeout=5,
        )
        defaults.update(kwargs)
        return Task(**defaults)

    def _obs(self, **kwargs):
        from eval.grader import ObservedRun
        defaults = dict(task_id="t1", iteration=1, exit_code=0,
                        stdout="hello", stderr="", wall_time_ms=100)
        defaults.update(kwargs)
        return ObservedRun(**defaults)

    def test_pass(self):
        t = self._task()
        g = grade(t, self._obs())
        self.assertEqual(g.verdict, "pass")
        self.assertEqual(g.bucket, "pass")

    def test_wrong_exit_code(self):
        t = self._task(expected=Expected(exit_code=2))
        g = grade(t, self._obs(exit_code=0))
        self.assertEqual(g.verdict, "fail")
        self.assertEqual(g.bucket, "wrong_exit_code")

    def test_stderr_includes(self):
        t = self._task(expected=Expected(stderr_includes=["oops"]))
        g = grade(t, self._obs(stderr="nothing relevant"))
        self.assertEqual(g.verdict, "fail")
        self.assertIn("oops", g.failed_predicates[0])

    def test_stdout_excludes(self):
        t = self._task(expected=Expected(stdout_excludes=["error"]))
        g = grade(t, self._obs(stdout="there was an error"))
        self.assertEqual(g.verdict, "fail")
        self.assertIn("stdout_excludes", g.failed_predicates[0])

    def test_mock_call_sequence_includes(self):
        t = self._task(
            expected=Expected(mock_call_sequence_includes=["SetVisible"])
        )
        g = grade(t, self._obs(mock_calls=["SetVisible", "LoadModel"]))
        self.assertEqual(g.verdict, "pass")

    def test_mock_call_sequence_includes_missing(self):
        t = self._task(
            expected=Expected(mock_call_sequence_includes=["X"])
        )
        g = grade(t, self._obs(mock_calls=["SetVisible"]))
        self.assertEqual(g.verdict, "fail")
        self.assertIn("mock_call_sequence_includes", g.failed_predicates[0])

    def test_wall_time_budget(self):
        t = self._task(expected=Expected(wall_time_max_ms=50))
        g = grade(t, self._obs(wall_time_ms=200))
        self.assertEqual(g.verdict, "fail")

    def test_inconclusive_no_exit(self):
        t = self._task()
        g = grade(t, self._obs(exit_code=None, raw_error="runner died"))
        self.assertEqual(g.verdict, "inconclusive")


# --- Runner tests (with the fake script) ------------------------------------


class TestRunner(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="eval_test_"))
        self.script = _write_fake_script(self.tmp)
        self.cfg = RunConfig(
            script_path=self.script,
            iterations=1,
            mock=False,  # the fake script doesn't need the mock shim
            default_model=str(self.tmp / "model.spp"),
            default_simtalkclaudefile=str(self.tmp / "pslib.pslib"),
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_missing_required_arg_yields_exit_2(self):
        # Use empty defaults so the runner does NOT auto-fill --model.
        # This lets the fake script see a truly missing required arg
        # and exit 2.
        cfg = RunConfig(
            script_path=self.script,
            iterations=1,
            mock=False,
            default_model="",
            default_simtalkclaudefile="",
        )
        task = Task(
            id="t", category="cli-validation", name="t",
            args=[], mock=False,
            expected=Expected(exit_code=2, stderr_includes=["--model"]),
            timeout=5,
        )
        result = run_all(cfg, [task])[0]
        g = grade(task, result.observations[0])
        self.assertEqual(g.verdict, "pass", g.failed_predicates)

    def test_happy_path(self):
        # Create real placeholder files so the fake script's 'NOTFOUND' check passes.
        (self.tmp / "model.spp").write_text("model")
        (self.tmp / "pslib.pslib").write_text("pslib")
        task = Task(
            id="t", category="model-load", name="t",
            args=[], mock=False,
            expected=Expected(
                exit_code=0,
                stdout_includes=["Plant Simulation launched, model loaded"],
                stderr_includes=["PROGRESS: COM dispatch OK"],
            ),
            timeout=5,
        )
        result = run_all(self.cfg, [task])[0]
        g = grade(task, result.observations[0])
        self.assertEqual(g.verdict, "pass", g.failed_predicates)

    def test_model_not_found(self):
        # The fake script's 'NOTFOUND' substring triggers exit 4.
        task = Task(
            id="t", category="model-load", name="t",
            args=["-m", "NOTFOUND.spp", "-s", "real.pslib"],
            mock=False,
            expected=Expected(
                exit_code=4,
                stderr_includes=["Model file not found"],
            ),
            timeout=5,
        )
        result = run_all(self.cfg, [task])[0]
        g = grade(task, result.observations[0])
        self.assertEqual(g.verdict, "pass", g.failed_predicates)

    def test_port_zero_yields_exit_2(self):
        task = Task(
            id="t", category="cli-validation", name="t",
            args=["-p", "0"],
            mock=False,
            expected=Expected(
                exit_code=2,
                stderr_includes=["1..65535"],
            ),
            timeout=5,
        )
        result = run_all(self.cfg, [task])[0]
        g = grade(task, result.observations[0])
        self.assertEqual(g.verdict, "pass", g.failed_predicates)


# --- Reporter tests ---------------------------------------------------------


class TestReporter(unittest.TestCase):
    def _fake_result(self, task_id="t1", category="cli-validation",
                     verdicts=None, walls=None):
        from eval.grader import GraderResult, ObservedRun
        if verdicts is None:
            verdicts = ["pass"] * 3
        if walls is None:
            walls = [100, 110, 105]
        observations = [
            ObservedRun(task_id=task_id, iteration=i + 1, exit_code=0,
                        stdout="ok", stderr="", wall_time_ms=w)
            for i, w in enumerate(walls)
        ]
        grade_results = [
            GraderResult(task_id=task_id, iteration=i + 1,
                         verdict=v, bucket="pass" if v == "pass" else "fail")
            for i, v in enumerate(verdicts)
        ]
        task = Task(id=task_id, category=category, name=task_id, args=[],
                    mock=True, expected=Expected(exit_code=0), timeout=5)
        from eval.runner import TaskRunResult
        return TaskRunResult(task=task, observations=observations,
                             grade_results=grade_results)

    def test_aggregate_basic(self):
        results = [self._fake_result()]
        rep = aggregate(results, iterations=3, pass_rate_threshold=0.95)
        self.assertEqual(rep.overall_n_pass, 3)
        self.assertEqual(rep.exit_gate_code, 0)

    def test_aggregate_below_threshold(self):
        results = [self._fake_result(verdicts=["pass", "fail", "fail"])]
        rep = aggregate(results, iterations=3, pass_rate_threshold=0.95)
        self.assertEqual(rep.exit_gate_code, 1)

    def test_aggregate_hard_gate_regression(self):
        # Build a result with a hard-gate tag and a fail.
        from eval.grader import GraderResult, ObservedRun
        task = Task(id="l", category="lifelines", name="l", args=[],
                    mock=True, expected=Expected(exit_code=0), timeout=5,
                    tags=["lifeline-L1"])
        observations = [ObservedRun(task_id="l", iteration=1, exit_code=2,
                                    stdout="", stderr="bad", wall_time_ms=100)]
        grade_results = [GraderResult(task_id="l", iteration=1,
                                      verdict="fail", bucket="wrong_exit_code")]
        from eval.runner import TaskRunResult
        results = [TaskRunResult(task=task, observations=observations,
                                 grade_results=grade_results)]
        rep = aggregate(results, iterations=1, pass_rate_threshold=0.0,
                        hard_gate_tags=["lifeline-L1"])
        self.assertEqual(rep.n_hard_gate_regressions, 1)
        self.assertEqual(rep.exit_gate_code, 3)

    def test_render_summary_md(self):
        results = [self._fake_result()]
        rep = aggregate(results, iterations=3)
        md = render_summary_md(rep)
        self.assertIn("Evaluation Summary", md)
        self.assertIn("Per-task pass rates", md)

    def test_write_reports(self):
        results = [self._fake_result()]
        rep = aggregate(results, iterations=3)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            paths = write_reports(out, rep, results)
            self.assertTrue(paths["summary_md"].exists())
            self.assertTrue(paths["summary_json"].exists())
            self.assertTrue(paths["snapshot"].exists())
            # per-task/<id>.md should exist
            per = paths["per_task_dir"]
            self.assertTrue((per / "t1.md").exists())

    def test_diff_snapshots(self):
        old = {
            "tasks": [
                {"id": "a", "grade_results": [
                    {"verdict": "pass"}, {"verdict": "pass"}, {"verdict": "pass"},
                ]},
            ]
        }
        new = {
            "tasks": [
                {"id": "a", "grade_results": [
                    {"verdict": "pass"}, {"verdict": "pass"}, {"verdict": "fail"},
                ]},
            ]
        }
        diff = diff_snapshots(old, new)
        self.assertIn("a", diff["newly_failing"])
        self.assertEqual(len(diff["pass_rate_drops"]), 1)


# --- Mock shim tests (verify the shim itself loads in a subprocess) --------


class TestMockShim(unittest.TestCase):
    def test_shim_loads(self):
        """Verify the shim's _bootstrap runs without error in a subprocess."""
        shim_dir = _ROOT / "eval" / "_shims"
        self.assertTrue((shim_dir / "win32com" / "__init__.py").exists())
        self.assertTrue((shim_dir / "pywintypes.py").exists())

        # Spawn python with PYTHONPATH set to eval/_shims and import both.
        env = dict(os.environ)
        env["PYTHONPATH"] = str(shim_dir) + os.pathsep + env.get("PYTHONPATH", "")
        out = subprocess.run(
            [sys.executable, "-c",
             "import win32com; import win32com.client; "
             "import pywintypes; "
             "rc = win32com.client.Dispatch('X'); "
             "rc.DoSomething(1, 2); "
             "print('OK')"],
            capture_output=True, text=True, env=env, timeout=10,
        )
        self.assertEqual(out.returncode, 0, f"stderr={out.stderr!r}")
        self.assertIn("OK", out.stdout)

    def test_shim_fault_injection(self):
        """Verify the shim's fault injection works (raises com_error)."""
        shim_dir = _ROOT / "eval" / "_shims"
        env = dict(os.environ)
        env["PYTHONPATH"] = str(shim_dir) + os.pathsep + env.get("PYTHONPATH", "")
        # Write a fault file.
        with tempfile.TemporaryDirectory() as tmp:
            fault_path = Path(tmp) / "faults.json"
            fault_path.write_text(json.dumps({
                "by_progid": {
                    "X": {
                        "Boom": {"action": "raise_com_error",
                                 "hresult": 2147500037,
                                 "message": "synthetic"}
                    }
                }
            }), encoding="utf-8")
            env["EVAL_MOCK_FAULTS"] = str(fault_path)
            out = subprocess.run(
                [sys.executable, "-c",
                 "import win32com.client; import pywintypes; "
                 "rc = win32com.client.Dispatch('X'); "
                 "exec('try:\\n rc.Boom()\\n"
                 "except pywintypes.com_error as e:\\n"
                 " print(\"CAUGHT:\", e.hresult)')"],
                capture_output=True, text=True, env=env, timeout=10,
            )
            self.assertEqual(out.returncode, 0, f"stderr={out.stderr!r}")
            self.assertIn("CAUGHT: 2147500037", out.stdout)

    def test_shim_isfile_stub(self):
        """Verify the shim's isfile stub activates on configured paths."""
        shim_dir = _ROOT / "eval" / "_shims"
        env = dict(os.environ)
        env["PYTHONPATH"] = str(shim_dir) + os.pathsep + env.get("PYTHONPATH", "")
        env["EVAL_MOCK_PATHS_AS_EXISTING"] = "MOCK_MAGIC_PATH"
        out = subprocess.run(
            [sys.executable, "-c",
             "import win32com; "  # triggers shim bootstrap (isfile stub install)
             "import os.path as p; "
             "print('YES' if p.isfile('/totally/MOCK_MAGIC_PATH/fake.spp') else 'NO'); "
             "print('YES' if p.isfile('/totally/real/but/missing/file.spp') else 'NO')"],
            capture_output=True, text=True, env=env, timeout=10,
        )
        self.assertEqual(out.returncode, 0, f"stderr={out.stderr!r}")
        self.assertIn("YES\n", out.stdout)  # first call → YES
        # The second call may print YES or NO depending on the host; we don't assert.

    def test_shim_disable(self):
        """Verify EVAL_MOCK_DISABLE=1 makes the shim raise on import."""
        shim_dir = _ROOT / "eval" / "_shims"
        env = dict(os.environ)
        env["PYTHONPATH"] = str(shim_dir) + os.pathsep + env.get("PYTHONPATH", "")
        env["EVAL_MOCK_DISABLE"] = "1"
        out = subprocess.run(
            [sys.executable, "-c",
             "import win32com.client"],
            capture_output=True, text=True, env=env, timeout=10,
        )
        # The shim should raise ImportError during bootstrap, so the
        # subprocess exits non-zero with the ImportError traceback in stderr.
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("ImportError", out.stderr)
        self.assertIn("EVAL_MOCK_DISABLE", out.stderr)


# --- End-to-end test using the real scripts/run_eval.py with the fake skill --


class TestEndToEnd(unittest.TestCase):
    def test_run_eval_with_fake_script(self):
        """Spawn scripts/run_eval.py pointing at our fake skill, --mock,
        --tag=smoke. We just check that the CLI runs to completion and
        writes reports. The grading correctness is covered above.
        """
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "reports"
            cfg = Path(tmp) / "config.yaml"
            cfg.write_text(
                f"script_path: {_ROOT.parent / 'skills' / 'local-window-com-start-plant-simulation' / 'scripts' / 'start_plant_simulation.py'}\n"
                f"default_model: {tmp}/model.spp\n"
                f"default_simtalkclaudefile: {tmp}/pslib.pslib\n"
                f"iterations: 1\n"
                f"mock: false\n",
                encoding="utf-8",
            )
            # We run the runner pointed at a *fake* script, not the real
            # one (which would try to talk to a non-existent PS).
            # Use a config that points at our fake script.
            (Path(tmp) / "model.spp").write_text("m")
            (Path(tmp) / "pslib.pslib").write_text("p")
            fake_script = _write_fake_script(Path(tmp))
            cfg.write_text(
                f"script_path: {fake_script}\n"
                f"default_model: {tmp}/model.spp\n"
                f"default_simtalkclaudefile: {tmp}/pslib.pslib\n"
                f"iterations: 1\n"
                f"mock: false\n",
                encoding="utf-8",
            )
            # Build a minimal suite that uses our fake script via the
            # model-load category (which the runner auto-fills).
            suite = Path(tmp) / "suite.json"
            suite.write_text(json.dumps({
                "category": "model-load",
                "description": "e2e smoke",
                "tasks": [
                    {
                        "id": "e2e-001-happy",
                        "category": "model-load",
                        "name": "happy path",
                        "args": [],
                        "mock": False,
                        "timeout": 5,
                        "expected": {
                            "exit_code": 0,
                            "stdout_includes": ["Plant Simulation launched, model loaded"],
                        },
                        "tags": ["e2e", "smoke"],
                    },
                ],
            }), encoding="utf-8")

            proc = subprocess.run(
                [sys.executable, str(_ROOT / "scripts" / "run_eval.py"),
                 "--suite", str(suite),
                 "--config", str(cfg),
                 "--out", str(out_dir),
                 "--iterations", "1",
                 "--tag", "e2e",
                 "--verbose"],
                capture_output=True, text=True, timeout=60,
            )
            # We don't assert exit code = 0 here because the fake script
            # doesn't perfectly mimic the real one (no COM mock). What
            # matters is that the runner reaches the report-writing step.
            self.assertTrue(out_dir.exists(), f"reports dir not created. stderr={proc.stderr!r}")
            self.assertTrue((out_dir / "summary.md").exists() or
                            (out_dir / "summary.json").exists(),
                            f"no reports written. stdout={proc.stdout!r} stderr={proc.stderr!r}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
