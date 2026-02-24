# Backend Setup Guide

## Step-by-Step Installation Instructions

### Step 1: Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Expected output:
```
Successfully installed flask-2.3.3 flask-cors-4.0.0 pymongo-4.5.0 dnspython-2.4.2 numpy-1.24.3 opencv-python-4.8.1.78 face-recognition-1.3.5 Pillow-10.0.0 python-dotenv-1.0.0
```

### Step 2: Setup MongoDB

#### Option A: MongoDB Atlas (Recommended)
1. Visit [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create free account
3. Create new cluster
4. Get connection string
5. Set environment variable:

```bash
# Windows (PowerShell)
$env:MONGODB_URI = "mongodb+srv://username:password@cluster.mongodb.net/face_attendance"

# Linux/Mac
export MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/face_attendance"
```

#### Option B: Local MongoDB
1. [Download MongoDB](https://www.mongodb.com/try/download/community)
2. Install and start MongoDB service
3. Connection string: `mongodb://localhost:27017/face_attendance`

### Step 3: Update Configuration

Edit `config.py` with your MongoDB connection:

```python
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://your_username:your_password@cluster.mongodb.net/face_attendance"
)
```

### Step 4: Start the Server

```bash
python app.py
```

You should see:
```
Starting Face Attendance System API on 0.0.0.0:5000
 * Running on http://0.0.0.0:5000
```

### Step 5: Verify Installation

Test the health endpoint:

```bash
# Using curl
curl http://localhost:5000/api/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "Face Attendance System API",
#   "timestamp": "2024-02-07T10:30:00"
# }
```

Or visit: http://localhost:5000/api/health in browser

## Troubleshooting Installation

### Issue: ModuleNotFoundError

**Error**: `ModuleNotFoundError: No module named 'flask'`

**Solution**:
```bash
# Ensure you're in the backend directory
cd backend

# Install dependencies again
pip install -r requirements.txt

# Verify Flask installation
python -c "import flask; print(flask.__version__)"
```

### Issue: MongoDB Connection Error

**Error**: `ServerSelectionTimeoutError: No servers found yet`

**Solution**:
```bash
# Check connection string in config.py
# Verify MongoDB service is running
# For Atlas: Check IP whitelist includes your IP
# For Local: Start MongoDB service

# Windows
net start MongoDB

# Linux/Mac
brew services start mongodb-community

# Test connection
python -c "from pymongo import MongoClient; client = MongoClient('your_connection_string'); print(client.admin.command('ping'))"
```

### Issue: Face Recognition Library Error

**Error**: `ImportError: No module named 'face_recognition'`

**Solution**:
```bash
# Install face-recognition with dependencies
pip install face-recognition dlib --no-cache-dir

# Verify installation
python -c "import face_recognition; print(face_recognition.__file__)"
```

### Issue: OpenCV Not Found

**Error**: `ImportError: No module named 'cv2'`

**Solution**:
```bash
# Install OpenCV
pip install opencv-python --upgrade

# Verify
python -c "import cv2; print(cv2.__version__)"
```

## Testing API Endpoints

### Test 1: Health Check
```bash
curl -X GET http://localhost:5000/api/health
```

### Test 2: Add Student
```bash
curl -X POST http://localhost:5000/api/students/add \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Student",
    "student_id": "TEST001",
    "email": "test@example.com",
    "department": "Computer Science"
  }'
```

### Test 3: List Students
```bash
curl -X GET "http://localhost:5000/api/students/?page=1&per_page=10"
```

### Test 4: Add Teacher
```bash
curl -X POST http://localhost:5000/api/teachers/add \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Teacher",
    "teacher_id": "T001",
    "email": "teacher@example.com",
    "department": "Computer Science"
  }'
```

## Using Postman for API Testing

1. Download [Postman](https://www.postman.com/downloads/)
2. Create new workspace
3. Create requests for each endpoint
4. Save request collections for team

### Sample Postman Collection

```json
{
  "info": {
    "name": "Face Attendance API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "http://localhost:5000/api/health"
      }
    },
    {
      "name": "Add Student",
      "request": {
        "method": "POST",
        "url": "http://localhost:5000/api/students/add",
        "header": [
          {"key": "Content-Type", "value": "application/json"}
        ],
        "body": {
          "mode": "raw",
          "raw": "{\"name\": \"John\", \"student_id\": \"001\", \"email\": \"john@example.com\", \"department\": \"CS\"}"
        }
      }
    }
  ]
}
```

## Environment Variables

Create `.env` file in backend directory:

```bash
# MongoDB
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/face_attendance

# Flask
SECRET_KEY=your-secret-key-here
DEBUG=True

# Face Recognition
FACE_RECOGNITION_THRESHOLD=0.6

# API
API_HOST=0.0.0.0
API_PORT=5000
```

Load with python-dotenv:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Production Deployment Checklist

- [ ] Update SECRET_KEY with strong value
- [ ] Set DEBUG=False
- [ ] Use Gunicorn or uWSGI
- [ ] Set up HTTPS/SSL
- [ ] Configure proper CORS domains
- [ ] Set up MongoDB backups
- [ ] Configure logging
- [ ] Setup monitoring
- [ ] Rate limiting
- [ ] IP whitelist for MongoDB

## Performance Optimization

### 1. Gunicorn Workers
```bash
# 4 workers for 4-core system
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 2. MongoDB Indexes
Already created automatically, but verify:
```python
python -c "from db import db; print(db.students.list_indexes())"
```

### 3. Image Compression
Already implemented in config.py

## Development Tools

### Visual Studio Code Extensions
- Python
- Pylance
- MongoDB for VS Code
- REST Client
- Thunder Client

### Recommended Setup
```bash
# Install dev dependencies
pip install flask-debugtoolbar flask-shell-ipython

# Run with hot reload
flask run --reload
```

## Next Steps

1. ✅ Backend is installed and running
2. Configure Flutter app to connect to backend
3. Test face registration
4. Test attendance marking
5. Deploy to production server

## Quick Reference

```bash
# Start backend
python app.py

# Test health
curl http://localhost:5000/api/health

# View logs
tail -f logs/app.log

# Restart MongoDB
net stop MongoDB && net start MongoDB

# Check Python version
python --version

# Verify installations
pip list | grep -E "flask|pymongo|face-recognition|opencv"
```

## Common Commands

```bash
# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (Linux/Mac)
source venv/bin/activate

# Install single package
pip install package-name

# Update all packages
pip install -U pip setuptools wheel

# Generate requirements file
pip freeze > requirements.txt

# Run specific file
python -m routes.students

# Python interactive shell
python -i app.py
```

## Support Resources

- API Documentation: See `API_DOCUMENTATION.md`
- Implementation Details: See `IMPLEMENTATION_SUMMARY.md`
- Flask Docs: https://flask.palletsprojects.com/
- MongoDB Docs: https://docs.mongodb.com/
- Face Recognition: https://github.com/ageitgey/face_recognition

## Contact & Issues

For setup issues:
1. Check logs for error messages
2. Verify MongoDB connection
3. Check Python version (3.8+)
4. Ensure all dependencies installed
5. Check firewall/port settings

---

**Setup Complete!** Your backend is ready for development and testing.
