@echo off
REM AutoPromo Cloud - System Validation Script (Windows)
REM Run this from C:\Users\Ruan\Desktop\autopromo

echo ========================================
echo AutoPromo Cloud - System Validation
echo ========================================
echo.

REM Step 1: Check Docker services
echo [1/6] Checking Docker services...
docker ps | findstr autopromo-postgres
if errorlevel 1 (
    echo ERROR: PostgreSQL not running. Start with: docker compose up -d postgres redis
    exit /b 1
)
docker ps | findstr autopromo-redis
if errorlevel 1 (
    echo ERROR: Redis not running. Start with: docker compose up -d postgres redis
    exit /b 1
)
echo OK: Docker services running
echo.

REM Step 2: Apply migrations
echo [2/6] Applying database migrations...
cd backend
python -m alembic upgrade head
if errorlevel 1 (
    echo ERROR: Migration failed
    cd ..
    exit /b 1
)
echo OK: Migrations applied
echo.

REM Step 3: Validate database schema
echo [3/6] Validating database schema...
python -c "import asyncio; from core.database import engine; from sqlalchemy import text; async def test(): async with engine.connect() as conn: result = await conn.execute(text('SELECT COUNT(*) FROM whatsapp_instances')); print(f'whatsapp_instances table exists: {result.scalar()} rows'); await engine.dispose(); asyncio.run(test())"
echo.

REM Step 4: Create test data
echo [4/6] Creating test data (if needed)...
python setup_test_data.py
echo.

REM Step 5: Validate pipeline code
echo [5/6] Validating pipeline code...
python validate_pipeline.py
if errorlevel 1 (
    echo WARNING: Pipeline validation failed
)
echo.

REM Step 6: Summary
echo [6/6] Validation Summary
echo ========================================
echo.
echo Next Steps:
echo 1. Start backend: python -m uvicorn main:app --reload --port 8000
echo 2. Start worker: python -m workers.worker
echo 3. Start dispatcher: python -m workers.dispatcher
echo 4. Access API docs: http://localhost:8000/docs
echo.

cd ..
