@echo off
echo Starting Research Agent (backend + frontend)...

start "Backend" cmd /k "cd /d C:\Users\Hanney\research-agent\backend && venv\Scripts\activate && uvicorn app.main:app --reload"

timeout /t 3 /nobreak >nul

start "Frontend" cmd /k "cd /d C:\Users\Hanney\research-agent\frontend && npm run dev"

echo Both servers starting in separate windows.
echo Backend: http://127.0.0.1:8000
echo Frontend: check the Frontend window for the exact port (5173/5174/5175...)