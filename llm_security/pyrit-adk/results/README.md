# PyRIT run results

One record per PyRIT run against `api_pentest_agent`, linking to its
published results page and the run's raw JSON output file (PyRIT itself
has no hosted results viewer, unlike Promptfoo's local dashboard or
garak's HTML report - `run_pyrit_scan.py` writes each run to its own JSON
file, and full conversation transcripts also land in PyRIT's local memory
DB via `initialize_pyrit_async`).

Add a row below and a matching `<date>_<output-file>.md` file for every
new run.

| Date | Script | Objectives | Result | Results page |
|---|---|---|---|---|
| 2026-09-21 | `run_pyrit_scan.py` | 8 curated (LLM01/06/07/09/10) + PyRIT's built-in `SkeletonKeyAttack` | 8 clean refusals, 1 blocked at the Gemini API layer (not an agent failure - see run record) | [PyRIT Scan Verdict](https://claude.ai/code/artifact/88d7757d-a958-446d-bba2-569cb46c511a) |
