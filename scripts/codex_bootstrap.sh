#!/usr/bin/env bash

set -euo pipefail

CODEX_NPM_PACKAGE="${CODEX_NPM_PACKAGE:-@openai/codex}"

npm install -g "${CODEX_NPM_PACKAGE}"

python3 -m venv .venv

source .venv/bin/activate

if [[ -f requirements.txt ]]; then
  pip install -r requirements.txt
fi

# Optional and explicit: keep llm_lab dependencies outside runtime by default.
if [[ "${INSTALL_LLM_LAB:-0}" == "1" ]] && [[ -f llm_lab/requirements.txt ]]; then
  pip install -r llm_lab/requirements.txt
fi
