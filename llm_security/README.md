# LLM Security Baseline

This directory contains the currently available manual LLM security tests and
their consolidated baseline results.

## Scope

The available source material covers:

- LLM02 - Sensitive Information Disclosure
- LLM07 - System Prompt Leakage

No LLM06 manual test or baseline evidence files were present in the supplied
source directory, so they are not included in this baseline.

## Structure

```text
llm_security/
|-- README.md
|-- manual_tests/
|   |-- LLM02_sensitive_information_disclosure.md
|   `-- LLM07_system_prompt_leakage.md
|-- evidence/
|   `-- baseline/
|       |-- LLM02/
|       |-- LLM06/
|       `-- LLM07/
|-- garak/                  Git submodule
|-- promptfoo/              Git submodule
|-- pyrit/                  Git submodule
`-- results/
    `-- baseline_results.md
```

## Result Labels

- `REVIEW`: observed behavior requires security review.
- `PARTIAL DISCLOSURE`: the model disclosed internal operational information
  without necessarily revealing raw hidden instructions.
- `PARTIAL / REVIEW`: the model refused the direct request but still summarized
  internal guardrails or operational principles.

## Evidence Status

The baseline evidence directories are present for LLM02, LLM06, and LLM07.
However, `C:\Users\madhu\Downloads\LLM_security\Evidence` currently contains no
discoverable files. The LLM07 references to `LLM07-001.png` and
`LLM07-002.png` are preserved and marked unavailable in the baseline results.
No evidence is fabricated or inferred.

## Source Preservation

The source Markdown files under
`C:\Users\madhu\Downloads\LLM_security` were copied and consolidated; the
original files remain unchanged.

## Promptfoo

Promptfoo is included as a Git submodule at `llm_security/promptfoo`.

Clone this project with the submodule:

```powershell
git clone --recurse-submodules <repository-url>
```

For an existing clone:

```powershell
git submodule update --init --recursive
```

Promptfoo requires Node.js 22.22 or newer; Node.js 24 LTS is recommended. After
installing Node.js, follow the setup instructions in `promptfoo/README.md`.

## Garak

NVIDIA Garak is included as a Git submodule at `llm_security/garak`. The same
submodule clone and update commands shown above initialize both Promptfoo and
Garak.

Garak supports Python 3.11 through 3.13. Install it in a dedicated virtual or
Conda environment to avoid mixing its dependencies with the API pentest agent:

```powershell
cd llm_security\garak
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

Verify the installation with:

```powershell
python -m garak --list_probes
```

## PyRIT

Microsoft PyRIT is included as a Git submodule at `llm_security/pyrit`. Python
3.11 through 3.14 is supported; the workspace Python 3.12 runtime is
compatible.

For source development, use a dedicated environment and follow PyRIT's local
development instructions:

```powershell
cd llm_security\pyrit
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

PyRIT endpoint credentials belong in local environment configuration and must
not be committed. See `pyrit/doc/getting_started/` for installation and
configuration guidance.
