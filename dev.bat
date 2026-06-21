@echo off
:: One-shot launcher: starts backend (FastAPI/uvicorn :8000) and frontend (Vite :5173).
:: Double-click to run. Press Ctrl+C (or close the window) to stop both.
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ============================================================
echo   wod-like-slg dev launcher
echo ============================================================

:: --- pick the Python interpreter -------------------------------------------
set "PY="
if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    where uv >nul 2>nul
    if !errorlevel! == 0 (
        set "PY=uv run python"
    ) else (
        where python >nul 2>nul
        if !errorlevel! == 0 (
            set "PY=python"
        )
    )
)
if "!PY!"=="" (
    echo [ERROR] No Python found. Create a venv ^(python -m venv .venv^) or install uv.
    pause
    exit /b 1
)
echo Using Python: !PY!

:: --- install frontend deps if missing --------------------------------------
if not exist "frontend\node_modules" (
    echo [setup] Installing frontend dependencies...
    pushd frontend
    call npm install
    popd
)

:: --- start backend ----------------------------------------------------------
echo [backend] starting uvicorn on http://127.0.0.1:8000 ...
start "wod-backend" /min !PY! -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

:: --- start frontend ---------------------------------------------------------
echo [frontend] starting vite on http://127.0.0.1:5173 ...
start "wod-frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ============================================================
echo   Both services are starting.
echo   App:        http://127.0.0.1:5173
echo   API:        http://127.0.0.1:8000/docs
echo.
echo   To stop: close this window, or run: dev-stop.bat
echo ============================================================
echo.
echo This window can stay open. Press any key to exit ^(services keep running^).
pause >nul
endlocal
