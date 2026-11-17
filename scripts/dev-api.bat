@echo off
cd /d %~dp0..\apps\api
if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate
pip install -e .
if not exist .env (
  copy .env.example .env
)
alembic upgrade head
uvicorn app.main:app --reload --port 8000
