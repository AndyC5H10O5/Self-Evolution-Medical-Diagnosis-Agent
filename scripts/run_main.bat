@echo off
setlocal

set "PROJECT_ROOT=%~dp0.."
set "PYCACHE_DIR=%PROJECT_ROOT%\.cache\pycache"

if not exist "%PYCACHE_DIR%" mkdir "%PYCACHE_DIR%"
set "PYTHONPYCACHEPREFIX=%PYCACHE_DIR%"

python "%PROJECT_ROOT%\src\agent_core\main.py"
