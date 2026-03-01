# RefineX — Build Status & Testing Guide

> Last updated: February 20, 2026  
> GitHub: https://github.com/hwkxhh/refine-x

---

## What Has Been Built

### Phase 1 — Infrastructure & Authentication (Complete)

| Component | Details |
|---|---|
| Docker environment | PostgreSQL 16, Redis 7, MinIO, pgAdmin 4 |
| FastAPI backend | Running at `localhost:8000` |
| Celery worker | Async task processing with Redis as broker |
| Database | Alembic migrations, `users` + `upload_jobs` tables |
| Auth system | Register, Login (JWT), protected routes |

### Phase 2 — File Upload Pipeline (Complete)

| Component | Details |
|---|---|
| File upload endpoint | `POST /upload` — accepts CSV, XLSX, JSON (max 50MB) |
| MinIO storage | Files stored at `s3://refinex-uploads/<user_id>/<uuid>.<ext>` |
| Background processing | Celery task reads file, runs pandas analysis |
| Quality score | Completeness score (0–100) calculated from non-null values |
| Job tracking | Full status lifecycle: `pending → processing → completed / failed` |
| Upload history | List, retrieve, and delete past upload jobs |

---

## Running the Project

### 1. Start Docker containers (if not already running)

```powershell
cd "c:\Users\mireb\OneDrive\Desktop\Refinex_app"
docker-compose up -d
```

Verify all 4 containers are up:
```powershell
docker ps
# Should show: refinex_postgres, refinex_redis, refinex_minio, refinex_pgadmin
```

### 2. Start the FastAPI server

```powershell
cd "c:\Users\mireb\OneDrive\Desktop\Refinex_app\backend"
.\venv\Scripts\uvicorn.exe app.main:app --port 8000
```

> **Important:** Do NOT use `--reload`. Python 3.14 has a multiprocessing bug on Windows that causes it to crash.

### 3. Start the Celery worker (new terminal)

```powershell
cd "c:\Users\mireb\OneDrive\Desktop\Refinex_app\backend"
.\venv\Scripts\celery.exe -A celery_app worker --pool=solo --loglevel=info
```

> **Important:** `--pool=solo` is required on Windows.

### 4. Verify everything is running

Open your browser: http://localhost:8000/docs

You should see the Swagger UI listing these routes:
- `/auth/register`
- `/auth/login`
- `/auth/me`
- `/upload`
- `/upload/jobs`
- `/upload/jobs/{job_id}`
- `/upload/jobs/{job_id}/status`

---

## Testing — Step by Step

### Test 1: Sign Up (Register)

**Via Swagger UI** → http://localhost:8000/docs → `POST /auth/register` → Try it out

```json
{
  "email": "you@example.com",
  "password": "yourpassword",
  "full_name": "Your Name"
}
```

**Via PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/auth/register" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"email":"you@example.com","password":"yourpassword","full_name":"Your Name"}'
```

**Expected response:**
```json
{
  "id": 1,
  "email": "you@example.com",
  "full_name": "Your Name",
  "is_active": true
}
```

---

### Test 2: Login

**Via Swagger UI** → `POST /auth/login` → Try it out  
Fill in `username` (your email) and `password` form fields.

**Via PowerShell:**
```powershell
$login = Invoke-RestMethod -Uri "http://localhost:8000/auth/login" `
  -Method POST `
  -ContentType "application/x-www-form-urlencoded" `
  -Body "username=you@example.com&password=yourpassword"

$token = $login.access_token
Write-Host "Token: $token"
```

**Expected response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

> **Note:** The login form field is called `username` even though you enter your email. This is the OAuth2 standard.

---

### Test 3: Get Current User (Protected Route)

**Via Swagger UI:**
1. Click the **Authorize** button (top right, padlock icon)
2. Enter your token in the `bearerAuth` field → Authorize
3. Now call `GET /auth/me` → Try it out → Execute

**Via PowerShell:**
```powershell
$headers = @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Uri "http://localhost:8000/auth/me" -Headers $headers
```

**Expected response:**
```json
{
  "id": 1,
  "email": "you@example.com",
  "full_name": "Your Name",
  "is_active": true
}
```

---

### Test 4: Upload a CSV File

First, create a test CSV file on your desktop (or use any real CSV):

```powershell
$csv = "name,age,email,city`nAlice,30,alice@test.com,NYC`nBob,,bob@test.com,LA`nCharlie,25,,Chicago"
[System.IO.File]::WriteAllText("C:\Users\mireb\Desktop\test.csv", $csv)
```

**Via Swagger UI:**
1. Authorize first (Step 3 above)
2. Go to `POST /upload` → Try it out
3. Click **Choose File** → select your CSV
4. Click Execute

**Via PowerShell:**
```powershell
# Assumes $token is set from login step
$headers = @{ Authorization = "Bearer $token" }
$filePath = "C:\Users\mireb\Desktop\test.csv"

Add-Type -AssemblyName System.Net.Http
$form = [System.Net.Http.MultipartFormDataContent]::new()
$fileContent = [System.Net.Http.ByteArrayContent]::new([System.IO.File]::ReadAllBytes($filePath))
$fileContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("text/csv")
$form.Add($fileContent, "file", "test.csv")

$client = [System.Net.Http.HttpClient]::new()
$client.DefaultRequestHeaders.Authorization = [System.Net.Http.Headers.AuthenticationHeaderValue]::new("Bearer", $token)
$response = $client.PostAsync("http://localhost:8000/upload", $form).Result
$response.Content.ReadAsStringAsync().Result
```

**Expected response (201 Created):**
```json
{
  "id": 1,
  "filename": "test.csv",
  "file_size": 88,
  "file_type": "csv",
  "status": "pending",
  "quality_score": null,
  "row_count": null,
  "column_count": null,
  "created_at": "2026-02-20T02:08:48.765633",
  "processed_at": null
}
```

Note the `"id"` — you'll use it in the next step.

---

### Test 5: Check Quality Score (Clarity Score)

Wait 3–5 seconds for Celery to process the file, then:

**Via Swagger UI:** `GET /upload/jobs/{job_id}/status` → Enter `1` as job_id → Execute

**Via PowerShell:**
```powershell
Start-Sleep -Seconds 5
$headers = @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Uri "http://localhost:8000/upload/jobs/1/status" -Headers $headers
```

**Expected response after processing:**
```json
{
  "id": 1,
  "filename": "test.csv",
  "status": "completed",
  "quality_score": 83.33,
  "row_count": 3,
  "column_count": 4,
  "created_at": "2026-02-20T02:08:48.765633",
  "processed_at": "2026-02-20T02:08:52.123456"
}
```

**What the quality score means:**

The `quality_score` is a **data completeness score** (0–100):
- `100.0` = all cells have values, zero missing data
- `83.33` = ~83% of cells are filled (2 missing out of 12)
- `0.0` = completely empty dataset

> This is Phase 2's basic quality metric. Phase 3 will expand this into a full multi-dimensional clarity/quality report.

---

### Test 6: List All Your Upload Jobs

**Via Swagger UI:** `GET /upload/jobs` → Execute (while authorized)

**Via PowerShell:**
```powershell
$headers = @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Uri "http://localhost:8000/upload/jobs" -Headers $headers
```

Returns an array of all your uploads with their current status.

---

### Test 7: Delete an Upload Job

**Via Swagger UI:** `DELETE /upload/jobs/{job_id}` → Enter job id → Execute

**Via PowerShell:**
```powershell
$headers = @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Uri "http://localhost:8000/upload/jobs/1" -Method DELETE -Headers $headers
```

This removes both the DB record and the file from MinIO.

---

## Viewing Data in the Browser

### Swagger UI (API Explorer)
**URL:** http://localhost:8000/docs  
Use this to test every endpoint interactively without writing any code.

### pgAdmin (Database Browser)
**URL:** http://localhost:5050  
**Login:** `admin@refinex.com` / `admin123`

To connect to the database:
1. Click **Add New Server**
2. **Name:** `RefineX`
3. Go to **Connection** tab:
   - **Host:** `postgres` (container name, NOT localhost)
   - **Port:** `5432`
   - **Database:** `refinex_db`
   - **Username:** `postgres`
   - **Password:** `postgres123`
4. Click Save

You can now browse tables:
- `public → Tables → users` — registered users
- `public → Tables → upload_jobs` — all upload jobs with status and quality scores

### MinIO Console (File Storage Browser)
**URL:** http://localhost:9001  
**Login:** `minioadmin` / `minioadmin123`

Navigate to the `refinex-uploads` bucket to see all uploaded files organized by user ID.

### ReDoc (Alternative API Docs)
**URL:** http://localhost:8000/redoc  
Cleaner read-only version of the API documentation.

---

## Project File Structure

```
Refinex_app/
├── docker-compose.yml          # All Docker services
├── plan.md                     # Full project roadmap
├── TESTING_GUIDE.md            # This file
└── backend/
    ├── .env                    # Secrets (not in git)
    ├── .env.example            # Template for secrets
    ├── requirements.txt        # Python dependencies
    ├── celery_app.py           # Celery configuration
    ├── alembic.ini             # Alembic config
    ├── alembic/
    │   └── versions/
    │       ├── 4acf2f1c2184_create_users_table.py
    │       └── 84f306ce690f_add_upload_jobs_table.py
    └── app/
        ├── main.py             # FastAPI entry point, router registration
        ├── config.py           # Settings (env vars)
        ├── database.py         # SQLAlchemy engine + session
        ├── models/
        │   ├── __init__.py
        │   ├── user.py         # User DB model
        │   └── upload_job.py   # UploadJob DB model
        ├── schemas/
        │   ├── user.py         # Auth request/response schemas
        │   └── upload.py       # Upload request/response schemas
        ├── services/
        │   ├── auth.py         # bcrypt hashing, JWT, get_current_user
        │   └── storage.py      # MinIO via boto3 (upload/download/delete)
        ├── routes/
        │   ├── auth.py         # /auth/* endpoints
        │   └── upload.py       # /upload/* endpoints
        └── tasks/
            └── process_csv.py  # Celery task: download → pandas → quality score
```

---

## Key Technical Decisions & Why

| Decision | Reason |
|---|---|
| `bcrypt` directly (not `passlib`) | passlib is incompatible with bcrypt 5.x — causes `ValueError` |
| uvicorn WITHOUT `--reload` | Python 3.14 has a multiprocessing/pipe bug on Windows that crashes on reload |
| Celery `--pool=solo` | Windows does not support the default `prefork` multiprocessing pool |
| `postgres` as DB host in pgAdmin | pgAdmin runs inside Docker; use container name, not `localhost` |
| `OPENAI_API_KEY` in `.env` | Swapped from Anthropic — OpenAI will be used in Phase 3 for AI cleaning suggestions |

---

## What's Next — Phase 3

Per `plan.md`, Phase 3 covers:
- **4-phase data cleaning pipeline:** structural fixes → value standardization → deduplication → integrity validation
- **`CleanedDataset` model** to store cleaned versions
- **Cleaning routes:** `POST /clean/{job_id}`, `GET /clean/{job_id}/preview`, `POST /clean/{job_id}/apply`
- **Redis caching** for cleaning previews
- **Export endpoint:** download cleaned file as CSV/XLSX

---

## Quick Reference — All Service URLs

| Service | URL | Credentials |
|---|---|---|
| FastAPI Swagger | http://localhost:8000/docs | — |
| FastAPI ReDoc | http://localhost:8000/redoc | — |
| pgAdmin | http://localhost:5050 | `admin@refinex.com` / `admin123` |
| MinIO Console | http://localhost:9001 | `minioadmin` / `minioadmin123` |

---

## Quick Reference — All API Endpoints

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/` | No | Health check |
| `GET` | `/health` | No | Detailed health status |
| `POST` | `/auth/register` | No | Create account |
| `POST` | `/auth/login` | No | Login, get JWT token |
| `GET` | `/auth/me` | Yes | Get current user info |
| `POST` | `/upload` | Yes | Upload CSV/XLSX/JSON file |
| `GET` | `/upload/jobs` | Yes | List all your upload jobs |
| `GET` | `/upload/jobs/{id}` | Yes | Get full job details |
| `GET` | `/upload/jobs/{id}/status` | Yes | Get job status + quality score |
| `DELETE` | `/upload/jobs/{id}` | Yes | Delete job + file from MinIO |
