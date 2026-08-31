### 2026-08-28 by @plant-simulation-expert — probe pipeline 在大模型上 3 个隐性 quirk

- **症状 1 (`render_library.py` RENDER-1)**:library dump JSON 里 `program` 字段只剩**首行注释**,但 `program_len` 是正确的完整长度 → 后续分析全错位。
- **症状 2 (`bfs_one_level.py` 大 Frame 截断)**:对 >~130 子节点的 Frame(如 Factory51 142 children),stdout JSON 在 ~12 KB 处被截断 → 缺失的 child 没人发现。
- **症状 3 (readlog v15+ batch degradation)**:连续发 `probe_methods.py` batch-8 时,前 17/25 抓干净,后 8 个 EnergyAnalyzer 方法 metadata 全空(META_TYPE=Method 但其他字段空白)→ 方法全空视图。
- **根因**:
  1. `probe_methods.py` 写 program body 用**真 newline**;`render_library.py` 用 `for ln in f: ln.split("\t")` 把每行当新 row → multi-line program 拆碎,只保留首注释。
  2. `bfs_one_level.py` 单 round-trip 用 `simtalk_run`(inline code),命中 v15+ readlog buffer ceiling(本文件 §四 Top 10)。
  3. v15+ readlog buffer 是按 statement 切片的;长 batch 的后段 metadata 在 buffer 重新分配时丢失。
- **Workaround / 结论**:
  1. **RENDER-1**:自定义 TSV re-parser(`/tmp/learning_library_full.json`),recognize header line(path + tab + name + tab + type + tab + ≥6 more tabs),accumulate body until next header。**Upstream 修法待提**:`probe_methods.py` 用 sentinel (`\x1e`) 替换 `\n` 后再写 TSV,renderer 还原;或整体改 quoted-CSV。
  2. **`bfs_one_level.py`**:改用 `bfs_full.py <path> 1 <out>.json`(depth-by-depth,每 round-trip ≤1 帧)避开 readlog ceiling。
  3. **readlog degradation**:batch 限制 ≤7 个方法;超出后改逐个 re-probe via `simtalk_send.py run` + readlog 提取(`/tmp/probe_with_log_capture.py`)。
  4. **re-parser 副作用**:`parse_analyzer_tsv.py` 会把空 row 附加到前一个 method → 修法:detect path-pattern 行(如 `.Models.`)即停积累。
- **tags**:`render_library`, `RENDER-1`, `bfs_one_level`, `readlog-v15-degradation`, `probe-pipeline`, `large-frame`, `multi-line-program`
- **see also**:本文件 §四 Top 10(readlog buffer ceiling);`skills/local-simtalk-get-folder-tree/log/2026-08-27_basis-depth4-full-and-factory51-types.md`(Factory51 142 children 截断案例);`skills/local-simtalk-read-library/log/2026-08-27_learn-assembly-model-bottleneckAnalyzer-energyAnalyzer.md`(re-probe 工作流)
- **反思**:probe pipeline 是**默认信任链路**,但实际有 3 处会让 dump 看起来"成功"而内容破碎——**任何 library dump 后必须做完整性校验**(method count vs inventory、`program_len > 0` 占比、path 格式)。可考虑加 `library_dump_validator.py` 自动跑。

> 这条经验教会我：
> - "successful exit" ≠ "successful capture"——任何 stdout-redirect 的工具链默认不验证 round-trip 完整性,默认信任会让 silent corruption 累积到下游才发现。
> - batch size 上限(≤7)是经验值,不是任意挑的——`readlog buffer ceiling` 是 hard 限制;过 7 必有 metadata 丢失。

> [curator-audited 2026-08-28 by @plant-simulation-experience-curator — pre-curator entry; see `agents/curator-reports/2026-08-28-curator-report.md` audit-009]