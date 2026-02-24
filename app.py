"""
Face Attendance System - Flask Backend API
Main application entry point
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load configuration
from config import SECRET_KEY, DEBUG, API_HOST, API_PORT
app.config['SECRET_KEY'] = SECRET_KEY
app.config['DEBUG'] = DEBUG

# Initialize database
from db import connect_db
try:
    connect_db()
    logger.info("Database initialized")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")

# Import blueprints
from routes.students import students_bp
from routes.attendance import attendance_bp
from routes.hardware import hardware_bp
from routes.teachers import teachers_bp
from routes.subjects import subjects_bp
from routes.auth import auth_bp
from routes.notices import notices_bp

# Register blueprints
app.register_blueprint(students_bp, url_prefix="/api/students")
app.register_blueprint(teachers_bp, url_prefix="/api/teachers")
app.register_blueprint(attendance_bp, url_prefix="/api/attendance")
app.register_blueprint(hardware_bp, url_prefix="/api/hardware")
app.register_blueprint(hardware_bp, url_prefix="/api/devices", name="devices")  # Alias for backward compatibility
app.register_blueprint(subjects_bp, url_prefix="/api/subjects")
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(notices_bp, url_prefix="/api/notices")

# ------------------ HEALTH CHECK ------------------
@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Face Attendance System API"
    }), 200

# ------------------ ROOT ENDPOINT ------------------
@app.route("/", methods=["GET"])
def index():
    """Root endpoint with API information"""
    return jsonify({
        "service": "Face Attendance System API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "auth": "/api/auth",
            "students": "/api/students",
            "teachers": "/api/teachers",
            "subjects": "/api/subjects",
            "attendance": "/api/attendance",
            "hardware": "/api/hardware",
            "devices": "/api/devices"
        }
    }), 200

# ------------------ ERROR HANDLERS ------------------
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "message": "Endpoint not found",
        "timestamp": datetime.utcnow().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "success": False,
        "message": "Internal server error",
        "timestamp": datetime.utcnow().isoformat()
    }), 500

# ------------------ LOG ALL REQUESTS ------------------
@app.before_request
def log_request():
    logger.info(f"{request.method} {request.path}")

# ------------------ START SERVER ------------------
if __name__ == '__main__':
    # Use 0.0.0.0 to allow access from other devices on the network
    app.run(host='0.0.0.0', port=5000, debug=True)
