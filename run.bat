@echo off
REM Aktivace venv a spuštění skriptu na Windows
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python src\qqq_gap_analysis.py %*
