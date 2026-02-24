"""
Configuration file for the Face Attendance System Backend
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# -----------------------------
# Flask Configuration
# -----------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# -----------------------------
# MongoDB Configuration
# -----------------------------
# Example URI in .env:
# MONGODB_URI=mongodb://localhost:27017
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "face_attendance")

# -----------------------------
# Upload Configuration
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload size
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# Ensure uploads folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -----------------------------
# Face Recognition Settings
# -----------------------------
FACE_RECOGNITION_THRESHOLD = 0.6   # Lower = more strict matching
MIN_FACE_SIZE = 20                 # Minimum face size in pixels

# -----------------------------
# JWT Configuration
# -----------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "jwt-secret-key-here")
JWT_EXPIRATION = timedelta(days=7)

# -----------------------------
# API Host Configuration
# -----------------------------
API_HOST = "0.0.0.0"
API_PORT = 5000
