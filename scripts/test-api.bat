@echo off
cd /d %~dp0..\apps\api
call .venv\Scripts\activate
ruff check .
pytest
