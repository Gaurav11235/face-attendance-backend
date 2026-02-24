# Quick Start Guide - Backend API

## Prerequisites ✅
- [x] MongoDB running on `localhost:27017`
- [x] Python 3.8+
- [x] Virtual environment activated
- [x] Dependencies installed

## Quick Setup (2 minutes)

### 1. Install Requirements
```bash
pip install -r backend/requirements.txt
```

### 2. Start Backend
```bash
cd backend
python app.py
```

You should see:
```
Starting Face Attendance System API on 0.0.0.0:5000
Database initialized
```

### 3. Test Backend (Optional)
```bash
python test_backend.py
```

---

## Basic API Usage

### Register a User
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "SecurePass123",
    "id": "22034001",
    "role": "student"
  }'
```

Response:
```json
{
  "success": true,
  "message": "Registration successful",
  "data": {
    "user": { ... },
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123"
  }'
```

### Health Check
```bash
curl http://localhost:5000/api/health
```

---

## API Documentation

See full documentation: [`BACKEND_SETUP_COMPLETE.md`](BACKEND_SETUP_COMPLETE.md)

## Issues Fixed

See detailed fixes: [`BACKEND_ISSUES_FIXED.md`](BACKEND_ISSUES_FIXED.md)

---

## Troubleshooting

**Server won't start:**
```
Make sure MongoDB is running: mongod
Check port 5000 is available
Check .env file exists
```

**Import errors:**
```
pip install -r backend/requirements.txt --upgrade
```

**MongoDB connection failed:**
```
Backend will use in-memory mock database automatically
Update MONGODB_URI in .env if using remote MongoDB
```

---

**API is running at:** `http://localhost:5000`  
**API Status:** ✅ Ready for use
