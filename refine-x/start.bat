@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  RefineX — Project Launcher
::  Run this AFTER Docker Desktop is already open.
::  Starts containers, runs DB migrations, Celery, and FastAPI.
:: ============================================================

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "VENV=%BACKEND%\venv\Scripts"
set "PYTHON=%VENV%\python.exe"
set "CELERY=%VENV%\celery.exe"
set "UVICORN=%VENV%\uvicorn.exe"

title RefineX Launcher

echo.
echo  ====================================
echo   RefineX — Starting up...
echo  ====================================
echo.

:: ─── Step 1: Check Docker is running ──────────────────────
echo [1/6] Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Docker Desktop is not running.
    echo  Please start Docker Desktop first, then run this file again.
    echo.
    pause
    exit /b 1
)
echo        Docker is running.

:: ─── Step 2: Start Docker Compose services ────────────────
echo.
echo [2/6] Starting Docker containers (postgres, redis, minio, pgadmin)...
cd /d "%ROOT%"
docker compose up -d
if errorlevel 1 (
    echo  ERROR: docker compose failed to start. Check the output above.
    pause
    exit /b 1
)
echo        Containers started.

:: ─── Step 3: Wait for PostgreSQL AND Redis to be ready ────
echo.
echo [3/6] Waiting for PostgreSQL to be ready...
set /a tries=0
:wait_postgres
set /a tries+=1
docker exec refinex_postgres pg_isready -U postgres >nul 2>&1
if errorlevel 1 (
    if !tries! GEQ 30 (
        echo  WARNING: PostgreSQL did not become ready after 60s — continuing anyway.
        goto :wait_redis
    )
    timeout /t 2 /nobreak >nul
    goto :wait_postgres
)
echo        PostgreSQL is ready.

:wait_redis
echo        Waiting for Redis...
set /a rtries=0
:wait_redis_loop
set /a rtries+=1
docker exec refinex_redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    if !rtries! GEQ 15 (
        echo  WARNING: Redis did not respond after 30s — continuing anyway.
        goto :after_wait
    )
    timeout /t 2 /nobreak >nul
    goto :wait_redis_loop
)
echo        Redis is ready.
:after_wait

:: ─── Step 4: Run DB migrations ────────────────────────────
echo.
echo [4/6] Running database migrations (alembic upgrade head)...
cd /d "%BACKEND%"
"%PYTHON%" -m alembic upgrade head
if errorlevel 1 (
    echo  ERROR: Alembic migration failed. Check your database connection.
    pause
    exit /b 1
)
echo        Migrations applied.

:: ─── Step 5: Start Celery worker (new window) ─────────────
echo.
echo [5/6] Starting Celery worker...
start "RefineX — Celery Worker" /d "%BACKEND%" cmd /k ""%CELERY%" -A celery_app worker --pool=solo --loglevel=warning"
timeout /t 3 /nobreak >nul
echo        Celery worker started (new window).

:: ─── Step 6: Start FastAPI / uvicorn (new window) ─────────
echo.
echo [6/6] Starting FastAPI server...
start "RefineX — FastAPI Server" /d "%BACKEND%" cmd /k ""%UVICORN%" app.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 5 /nobreak >nul
echo        FastAPI server started (new window).

:: ─── Health check ─────────────────────────────────────────
echo.
echo  Verifying backend health...
"%PYTHON%" -c "import urllib.request,json,sys; r=urllib.request.urlopen('http://localhost:8000/health',timeout=10); d=json.load(r); s=d.get('services',{}); ok=all(v=='healthy' for v in s.values()); print('  DB:',s.get('database','?'),'  Redis:',s.get('redis','?'),'  Celery:',s.get('celery','?'),'  MinIO:',s.get('minio','?')); sys.exit(0 if ok else 1)" 2>nul
if errorlevel 1 (
    echo  NOTE: Health check could not confirm all services yet — they may still be warming up.
    echo        Check http://localhost:8000/health manually in a few seconds.
) else (
    echo  All services healthy!
)

:: ─── Open browser tabs ─────────────────────────────────────
echo.
echo  Opening browser...
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
echo   To stop Docker:  docker compose down
echo.
pause
