@echo off
rem CarWatch v2 launcher. ASCII only - see tools/menu.py for messages.
rem Batch files are parsed with the OEM codepage, so no Korean text here.
chcp 65001 >nul 2>&1
cd /d "%~dp0"
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY (where python >nul 2>&1 && set "PY=python")
if not defined PY (
  echo [X] Python not found. Install Python 3.10+ and add it to PATH.
  pause
  exit /b 2
)
%PY% tools\menu.py %*
if "%~1"=="" pause
