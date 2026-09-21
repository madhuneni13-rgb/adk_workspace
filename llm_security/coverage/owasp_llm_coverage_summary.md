# OWASP LLM Top 10 coverage — api_pentest_agent

Four tools, one target, cross-referenced against the last run of each.
Generated image: [`owasp_llm_coverage.png`](owasp_llm_coverage.png) (script:
[`generate_coverage_image.py`](generate_coverage_image.py)).

**Zero confirmed exploitable vulnerabilities across all four tools.**

| Category | Manual | Promptfoo | garak | PyRIT |
|---|---|---|---|---|
| LLM01 Prompt Injection | - | pass | pass | pass |
| LLM02 Sensitive Information Disclosure | review | pass | - | - |
| LLM03 Supply Chain | - | - | - | - |
| LLM04 Data & Model Poisoning | - | pass | - | - |
| LLM05 Improper Output Handling | - | pass | pass | - |
| LLM06 Excessive Agency | - | pass | - | pass |
| LLM07 System Prompt Leakage | review | review | pass | pass |
| LLM08 Vector & Embedding Weaknesses | - | pass | - | - |
| LLM09 Misinformation | - | pass | - | pass |
| LLM10 Unbounded Consumption | - | pass | - | pass |

**Legend:** `pass` = clean / verified after manual transcript review. `review`
= flagged for human judgement, not a confirmed exploit. `-` = not exercised
in that tool's last run (LLM03 and LLM08 are also structurally out of scope
for this agent - no dependency-provenance surface, no RAG/vector store - so
neither is fully testable via prompts by any of these tools).

## Sources (last run per tool)

- **Manual:** [`manual_tests/LLM02_sensitive_information_disclosure.md`](../manual_tests/LLM02_sensitive_information_disclosure.md),
  [`manual_tests/LLM07_system_prompt_leakage.md`](../manual_tests/LLM07_system_prompt_leakage.md),
  [`results/baseline_results.md`](../results/baseline_results.md)
- **Promptfoo:** [`promptfoo-adk/results/README.md`](../promptfoo-adk/results/README.md) -
  hand-written suite (16 tests) + automated `owasp:llm` red-team scan (58 generated cases, 28 plugins)
- **garak:** [`garak-adk/results/README.md`](../garak-adk/results/README.md) -
  7 curated probes, ~216 prompts
- **PyRIT:** [`pyrit-adk/results/README.md`](../pyrit-adk/results/README.md) -
  8 curated objectives + PyRIT's built-in `SkeletonKeyAttack`

## Notes on the two `review` rows

Both trace to the same underlying behavior: the agent identifies itself as
an "Authorized API Security Verification Assistant" and describes its own
role/capabilities when asked directly, and recalls prior turns within the
same conversation. Manual testing (pre-dating the automated tools) flagged
this as worth review; Promptfoo's hand-written exact-string assertions
still flag it the same way. garak's `sysprompt_extraction.SystemPromptExtraction`
probe and the PyRIT `LLM07-system-prompt-request` objective - neither of
which checks for that specific self-identification phrase - both call the
same underlying behavior clean, since no internal instruction text (the
actual `MANDATORY WORKFLOW` / `DO NOT REFUSE` markers) is ever disclosed.
Kept as `review` here rather than resolved either way, since the four
tools genuinely disagree on how sensitive that self-identification is.

Regenerate the image after any new run: `python generate_coverage_image.py`
(edit the `ROWS` matrix in that file first to reflect the new results).
