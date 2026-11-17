#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/../apps/api"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -e .
[ -f .env ] || cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
