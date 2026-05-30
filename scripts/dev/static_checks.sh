#!/usr/bin/env bash
set -euo pipefail

python -m compileall app DB scripts tests
python -m ruff check .
python -m pytest --collect-only
