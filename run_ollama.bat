@echo off
title ResumeGrind - Ollama Daemon
echo ====================================================
echo Starting Ollama Local AI Server on http://localhost:11434
echo ====================================================
"%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
pause
