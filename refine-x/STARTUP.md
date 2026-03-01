# RefineX Startup Checklist

## Prerequisites
- Docker Desktop running
- Python 3.10+ installed

---

## 1. Start Docker services (PostgreSQL + Redis + MinIO)
```bash
docker-compose up -d
```

Verify containers are running:
```bash
docker-compose ps
```

---

## 2. Activate Python virtual environment
```bash
cd backend
venv\Scripts\activate
```

---

## 3. Start FastAPI development server
```bash
uvicorn app.main:app --reload
```

API available at: http://loca   lhost:8000  
Swagger docs at: http://localhost:8000/docs

---

## 4. Start Celery worker (open a separate terminal, activate venv first)
```bash
cd backend
venv\Scripts\activate
celery -A celery_app worker --pool=solo --loglevel=info
```

---

## 5. Access MinIO Console
URL: http://localhost:9001  
User: minioadmin  
Password: minioadmin123  

Create bucket `refinex-uploads` on first run.

---

## 6. Stop all Docker services
```bash
docker-compose down
```

To also remove volumes (wipes DB data):
```bash
docker-compose down -v
```

---

## Database Migrations

Run migrations:
```bash
cd backend
venv\Scripts\activate
alembic upgrade head
```

Create a new migration after model changes:
```bash
alembic revision --autogenerate -m "description of change"
alembic upgrade head
```

Check current revision:
```bash
alembic current
```
