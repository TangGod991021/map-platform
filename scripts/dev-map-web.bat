@echo off
cd /d %~dp0..\apps\map-web
python -m http.server 8081
