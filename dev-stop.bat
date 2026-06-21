@echo off
:: Stops the dev services started by dev.bat (kills listeners on :8000 and :5173).
echo Stopping dev services on :8000 and :5173 ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /pid %%a /f >nul 2>nul
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 " ^| findstr "LISTENING"') do (
    taskkill /pid %%a /f >nul 2*nul
)
:: Also close the spawned window titles if any remain.
taskkill /fi "WINDOWTITLE eq wod-frontend*" /f >nul 2>nul
echo Done.
