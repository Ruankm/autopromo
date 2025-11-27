# Backend API Tests - Manual Verification

## Prerequisites
- Docker containers running: `docker compose ps`
- Backend running: `python -m uvicorn main:app --reload --port 8000`

## Test 1: Register New User (with full_name)

**Method**: POST  
**URL**: `http://localhost:8000/api/v1/users/register`  
**Headers**: `Content-Type: application/json`

**Body**:
```json
{
  "email": "teste@autopromo.com",
  "password": "senha12345678",
  "full_name": "Teste Silva"
}
```

**Expected Response** (201 Created):
```json
{
  "id": "...",
  "email": "teste@autopromo.com",
  "full_name": "Teste Silva",
  "config_json": {...},
  "is_active": true,
  "created_at": "2025-11-26T..."
}
```

---

## Test 2: Register User (WITHOUT full_name)

**Body**:
```json
{
  "email": "teste2@autopromo.com",
  "password": "senha12345678"
}
```

**Expected**: Should work (full_name defaults to empty string)

---

## Test 3: Login

**Method**: POST  
**URL**: `http://localhost:8000/api/v1/users/login`  
**Headers**: `Content-Type: application/x-www-form-urlencoded`

**Body** (form-urlencoded):
```
username=teste@autopromo.com&password=senha12345678
```

**Expected Response** (200 OK):
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "email": "teste@autopromo.com",
    "full_name": "Teste Silva",
    ...
  }
}
```

---

## Test 4: Get Current User

**Method**: GET  
**URL**: `http://localhost:8000/api/v1/users/me`  
**Headers**: `Authorization: Bearer {token}`

**Expected Response** (200 OK):
```json
{
  "id": "...",
  "email": "teste@autopromo.com",
  "full_name": "Teste Silva",
  "config_json": {...},
  "is_active": true,
  "created_at": "..."
}
```

---

## How to Test

### Option A: Using Postman or Insomnia
1. Import these requests
2. Execute in order (Register → Login → Get User)

### Option B: Using VS Code REST Client
1. Install "REST Client" extension
2. Create a `.http` file with these requests
3. Click "Send Request" above each test

### Option C: Using curl (CMD, not PowerShell)
```cmd
curl -X POST http://localhost:8000/api/v1/users/register -H "Content-Type: application/json" -d "{\"email\":\"teste@autopromo.com\",\"password\":\"senha12345678\",\"full_name\":\"Teste Silva\"}"
```

### Option D: Visit FastAPI Docs
1. Open http://localhost:8000/docs
2. Use the interactive Swagger UI
3. Try the `/api/v1/users/register` endpoint
