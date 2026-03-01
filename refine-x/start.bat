@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  RefineX — Project Launcher
::  Starts Docker, FastAPI, and Celery worker
:: ============================================================

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "VENV=%BACKEND%\venv\Scripts"

title RefineX Launcher

echo.
echo  ====================================
echo   RefineX — Starting up...
echo  ====================================
echo.

:: ─── Step 1: Check Docker is running ──────────────────────
echo [1/5] Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Docker Desktop is not running.
    echo  Please start Docker Desktop and run this file again.
    echo.
    pause
    exit /b 1
)
echo        Docker is running.

:: ─── Step 2: Start Docker Compose services ────────────────
echo.
echo [2/5] Starting Docker containers (postgres, redis, minio, pgadmin)...
cd /d "%ROOT%"
docker-compose up -d >nul 2>&1
if errorlevel 1 (
    echo  ERROR: docker-compose failed to start.
    pause
    exit /b 1
)
echo        Containers started.

:: ─── Step 3: Wait for PostgreSQL to be ready ──────────────
echo.
echo [3/5] Waiting for PostgreSQL to be ready...
set /a tries=0
:wait_postgres
set /a tries+=1
docker exec refinex_postgres pg_isready -U postgres >nul 2>&1
if errorlevel 1 (
    if !tries! GEQ 20 (
        echo  WARNING: PostgreSQL did not become ready in time.
        echo  It may still be starting — continuing anyway.
        goto :after_wait
    )
    timeout /t 2 /nobreak >nul
    goto :wait_postgres
)
echo        PostgreSQL is ready.
:after_wait

:: ─── Step 4: Start Celery worker (new window) ─────────────
echo.
echo [4/5] Starting Celery worker...
start "RefineX — Celery Worker" /d "%BACKEND%" cmd /k ""%VENV%\activate.bat" && celery -A celery_app worker --pool=solo --loglevel=info"
timeout /t 3 /nobreak >nul
echo        Celery worker started (new window).

:: ─── Step 5: Start FastAPI / uvicorn (new window) ─────────
echo.
echo [5/5] Starting FastAPI server...
start "RefineX — FastAPI Server" /d "%BACKEND%" cmd /k ""%VENV%\activate.bat" && uvicorn app.main:app --port 8000"
timeout /t 4 /nobreak >nul
echo        FastAPI server started (new window).

:: ─── Open browser tabs ─────────────────────────────────────
echo.
echo  Opening Swagger UI in browser...
timeout /t 2 /nobreak >nul
start "" "http://localhost:8000/docs"

:: ─── Summary ───────────────────────────────────────────────
echo.
echo  ====================================
echo   RefineX is running!
echo  ====================================
echo.
echo   API + Swagger:  http://localhost:8000/docs
echo   pgAdmin:        http://localhost:5050
echo   MinIO Console:  http://localhost:9001
echo.
echo   pgAdmin login:  admin@refinex.com / admin123
echo   MinIO login:    minioadmin / minioadmin123
echo.
echo   Close the Celery and FastAPI windows to stop the app.
echo   To stop Docker:  docker-compose down
echo.
pause
