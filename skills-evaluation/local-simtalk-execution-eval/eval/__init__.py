"""local-simtalk-execution evaluation framework.

Public surface:
    eval.task        Task dataclass + JSON loader
    eval.grader      predicate-based auto-grader
    eval.stats       variance / pass-rate stats
    eval.runner      runs each task N times, collects observations
    eval.reporter    Markdown + JSON report writers
"""

__version__ = "0.1.0"