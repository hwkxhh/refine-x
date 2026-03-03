# ============================================================
# RefineX Database Reset Script
# Run from:  d:\Program Files\Desktop\Refinex\refine-x\
# Usage:     .\db-reset.ps1
# ============================================================
#
# What this does:
#   1. Stops all Docker containers
#   2. Deletes the postgres_data volume (clean slate)
#   3. Writes a fresh .env WITHOUT BOM (the root cause of past issues)
#   4. Starts all Docker services
#   5. Waits for postgres to be ready
#   6. Runs all Alembic migrations
#
# Credentials:
#   Host:     127.0.0.1:5433  (Docker postgres - avoids conflict with local PG)
#   User:     postgres
#   Password: refinex2026
#   Database: refinex_db
# ============================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$backendDir = "$PSScriptRoot\backend"
$envFile    = "$backendDir\.env"
$python     = "$backendDir\venv\Scripts\python.exe"

Write-Host ""
Write-Host "===  RefineX DB Reset  ===" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Stop containers ────────────────────────────────
Write-Host "[1/5] Stopping Docker containers..." -ForegroundColor Yellow
docker compose down
Write-Host "      Done." -ForegroundColor Green

# ── Step 2: Delete postgres volume ────────────────────────
Write-Host "[2/5] Removing postgres_data volume..." -ForegroundColor Yellow
docker volume rm refine-x_postgres_data 2>$null
Write-Host "      Done." -ForegroundColor Green

# ── Step 3: Write fresh .env (UTF-8 without BOM) ──────────
Write-Host "[3/5] Writing fresh .env (UTF-8 no-BOM)..." -ForegroundColor Yellow
$envLines = @(
    "DATABASE_URL=postgresql://postgres:refinex2026@127.0.0.1:5433/refinex_db",
    "REDIS_URL=redis://localhost:6379/0",
    "S3_ENDPOINT=http://localhost:9000",
    "S3_ACCESS_KEY=minioadmin",
    "S3_SECRET_KEY=minioadmin123",
    "S3_BUCKET=refinex-uploads",
    "S3_USE_SSL=false",
    "SECRET_KEY=ldnZxHUgOl7UfDIXlCxVVJlqF6vfAw7naLNPUVNgG6w",
    "ALGORITHM=HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES=30",
    "OPENAI_API_KEY=sk-proj-placeholder",
    "DEBUG=True"
)
$noBomUtf8 = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($envFile, ($envLines -join "`n"), $noBomUtf8)
Write-Host "      Written to: $envFile" -ForegroundColor Green

# ── Step 4: Start containers ───────────────────────────────
Write-Host "[4/5] Starting Docker services..." -ForegroundColor Yellow
docker compose up -d

Write-Host "      Waiting for postgres to be ready..." -ForegroundColor DarkGray
$maxWait = 30
$waited  = 0
do {
    Start-Sleep -Seconds 2
    $waited += 2
    $ready = docker exec refinex_postgres pg_isready -U postgres 2>&1
} while ($ready -notmatch "accepting connections" -and $waited -lt $maxWait)

if ($ready -match "accepting connections") {
    Write-Host "      PostgreSQL is ready." -ForegroundColor Green
} else {
    Write-Host "      WARNING: PostgreSQL did not become ready in ${maxWait}s" -ForegroundColor Red
}

# ── Step 5: Run migrations ─────────────────────────────────
Write-Host "[5/5] Running Alembic migrations..." -ForegroundColor Yellow
Push-Location $backendDir
& $python -m alembic upgrade head
Pop-Location
Write-Host "      Migrations complete." -ForegroundColor Green

Write-Host ""
Write-Host "===  Done!  ===" -ForegroundColor Cyan
Write-Host "Start the API with:" -ForegroundColor White
Write-Host "  cd backend" -ForegroundColor DarkGray
Write-Host "  .\venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor DarkGray
Write-Host ""
