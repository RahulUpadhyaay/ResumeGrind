@echo off
title ResumeGrind - Frontend Server
echo ====================================================
echo Starting React Vite Frontend on http://localhost:5173
echo ====================================================
cd /d "%~dp0frontend"
npm run dev
pause
