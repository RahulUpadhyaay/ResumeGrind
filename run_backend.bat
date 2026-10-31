@echo off
title ResumeGrind - Backend Server
echo ====================================================
echo Starting FastAPI Backend on http://127.0.0.1:8000
echo ====================================================
cd /d "%~dp0backend"
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)
uvicorn app.main:app --reload --port 8000
pause
