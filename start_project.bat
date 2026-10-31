@echo off
title ResumeGrind Launcher
echo ====================================================
echo Starting ResumeGrind (Backend + Frontend)...
echo ====================================================

start "ResumeGrind Backend" "%~dp0run_backend.bat"
timeout /t 2 /nobreak >nul
start "ResumeGrind Frontend" "%~dp0run_frontend.bat"

echo.
echo Both servers have been launched!
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://localhost:5173
echo.
timeout /t 3 /nobreak >nul
start http://localhost:5173
exit
