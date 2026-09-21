# Promptfoo run results

One record per promptfoo run against `api_pentest_agent`, linking to its
results page on the local Promptfoo viewer
(`npx promptfoo@latest view`, served at `http://localhost:15500`) and the
eval file it was written to.

Promptfoo assigns every run an eval ID (`eval-<id>-<timestamp>`, printed at
the end of the run and stored in the output JSON's `evalId` field). The
viewer serves each run at its own deep link, `/eval/<evalId>` - not just
the general `/evals` listing - so link directly to that when you have it.
These links are to your local viewer process; they only resolve while
`promptfoo view` is running on this machine, or after `promptfoo view` is
started again (the eval history is saved in `~/.promptfoo/promptfoo.db`
independent of the server process, so IDs stay valid across restarts).

Add a row below and a matching `<date>_<evalId>.md` file for every new run.

| Date | Config | Tests | Result | Eval link |
|---|---|---|---|---|
| 2026-09-20 | `promptfooconfig.yaml` (hand-written) | 16 | 13 pass / 0 fail / 3 error (2 pre-existing brittle assertions, 1 flaky Gemini-safety-layer block - see run record) | [eval-DCR-2026-09-21T00:06:07](http://localhost:15500/eval/eval-DCR-2026-09-21T00:06:07) |
| 2026-09-20 | `redteam.source.yaml` -> `redteam.yaml` (automated owasp:llm scan) | 58 | 45 pass / 0 fail / 13 blocked at the Gemini API layer (verified, not agent failures) | [eval-KJR-2026-09-20T22:58:46](http://localhost:15500/eval/eval-KJR-2026-09-20T22:58:46) |
