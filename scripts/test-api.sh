#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/../apps/api"
source .venv/bin/activate
ruff check .
pytest
