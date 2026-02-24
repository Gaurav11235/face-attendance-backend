"""
Routes for authentication (login and registration)
"""
from flask import Blueprint, request
from datetime import datetime, timedelta
import bcrypt
import jwt
from bson import ObjectId
from db import db
from utils.helpers import success_response, error_response, validate_json
from config import JWT_SECRET

auth_bp = Blueprint("auth", __name__)

def hash_password(password):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt(rounds=10)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, hashed):
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        return False

def generate_token(user_id, role, email):
    """Generate JWT token"""
    payload = {
        'user_id': str(user_id),
        'role': role,
        'email': email,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

@auth_bp.route("/register", methods=["POST"])
@validate_json("name", "email", "password", "id", "role")
def register():
    """
    Register a new user (Student or Teacher)
    Automatically creates entries in both users and profession-specific collections
    
    Request JSON:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "securepassword",
        "id": "22034001",
        "role": "Student",
        "department": "Computer Science"  (optional, defaults to "General")
    }
    """
    try:
        data = request.get_json()
        email = data.get("email").lower().strip()
        role = data.get("role", "").lower()
        user_id = data.get("id")  # Student ID or Teacher ID
        department = data.get("department", "General").strip()
        
        # Validate role
        if role not in ["student", "teacher"]:
            return error_response("Invalid role. Must be 'student' or 'teacher'", 400)
        
        # Check if email already exists in users collection
        existing_user = db.users.find_one({"email": email})
        if existing_user:
            return error_response("Email already registered", 400)
        
        # Check if ID already exists in profession-specific collection
        collection_name = "students" if role == "student" else "teachers"
        id_field = "student_id" if role == "student" else "teacher_id"
        existing_prof = db[collection_name].find_one({id_field: user_id})
        if existing_prof:
            return error_response(f"{role.capitalize()} ID already registered", 400)
        
        # Hash password
        hashed_password = hash_password(data.get("password"))
        
        # Create user document in users collection
        user_data = {
            "name": data.get("name"),
            "email": email,
            "password": hashed_password,
            "id": user_id,
            "role": role,
            "status": "active",
            "last_login": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        user_result = db.users.insert_one(user_data)
        
        # Create profession-specific entry
        prof_data = {
            "name": data.get("name"),
            id_field: user_id,
            "email": email,
            "department": department,
            "student_class": data.get("student_class", "").strip() if role == "student" else None,
            "division": data.get("division", "").strip() if role == "student" else None,
            "phone": data.get("phone", ""),
            "status": "active",
            "user_id": str(user_result.inserted_id),  # Link to users collection
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        prof_result = db[collection_name].insert_one(prof_data)
        
        # Update users collection with reference to profession-specific record
        db.users.update_one(
            {"_id": user_result.inserted_id},
            {"$set": {
                f"{role}_id": str(prof_result.inserted_id)
            }}
        )
        
        # Generate token
        token = generate_token(user_result.inserted_id, role, email)
        
        # Return response (don't include password)
        response_data = {
            "_id": str(user_result.inserted_id),
            "name": user_data["name"],
            "email": user_data["email"],
            "id": user_data["id"],
            "role": user_data["role"],
            "status": user_data["status"],
            "department": department,
            "student_class": data.get("student_class", "") if role == "student" else None,
            "division": data.get("division", "") if role == "student" else None
        }
        
        return success_response({
            "user": response_data,
            "token": token
        }, f"{role.capitalize()} registration successful", 201)
        
    except Exception as e:
        return error_response(f"Registration error: {str(e)}", 500)

@auth_bp.route("/login", methods=["POST"])
@validate_json("email", "password")
def login():
    """
    Login with email and password
    
    Request JSON:
    {
        "email": "john@example.com",
        "password": "securepassword"
    }
    """
    try:
        data = request.get_json()
        email = data.get("email").lower().strip()
        password = data.get("password")
        
        # Find user by email
        user = db.users.find_one({"email": email})
        
        if not user:
            return error_response("Invalid email or password", 401)
        
        # Verify password
        if not verify_password(password, user.get("password", "")):
            return error_response("Invalid email or password", 401)
        
        # Check if user is active
        if user.get("status") != "active":
            return error_response("User account is inactive", 403)
        
        # Generate token
        token = generate_token(user["_id"], user.get("role"), email)
        
        # Update last login
        db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Get department and face registration status from profession-specific collection
        role = user.get("role", "")
        dept = "General"
        face_registered = False
        if role == "student":
            student = db.students.find_one({"student_id": user.get("id")})
            if student:
                dept = student.get("department", "General")
                face_registered = "face_encoding" in student and student["face_encoding"] is not None
        elif role == "teacher":
            teacher = db.teachers.find_one({"teacher_id": user.get("id")})
            if teacher:
                dept = teacher.get("department", "General")
                face_registered = "face_encoding" in teacher and teacher["face_encoding"] is not None
        
        # Return user data without password
        user_data = {
            "_id": str(user["_id"]),
            "name": user.get("name"),
            "email": user.get("email"),
            "id": user.get("id"),
            "role": user.get("role"),
            "status": user.get("status"),
            "department": dept,
            "face_registered": face_registered
        }
        
        return success_response({
            "user": user_data,
            "token": token
        }, "Login successful", 200)
        
    except Exception as e:
        return error_response(f"Login error: {str(e)}", 500)

@auth_bp.route("/verify-token", methods=["POST"])
def verify_token():
    """
    Verify if a JWT token is valid
    
    Request JSON:
    {
        "token": "jwt_token_here"
    }
    """
    try:
        data = request.get_json()
        token = data.get("token")
        
        if not token:
            return error_response("Token required", 400)
        
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            return success_response({
                "valid": True,
                "user_id": payload.get("user_id"),
                "role": payload.get("role"),
                "email": payload.get("email")
            }, "Token is valid", 200)
        except jwt.ExpiredSignatureError:
            return error_response("Token has expired", 401)
        except jwt.InvalidTokenError:
            return error_response("Invalid token", 401)
            
    except Exception as e:
        return error_response(f"Token verification error: {str(e)}", 500)

@auth_bp.route("/refresh-token", methods=["POST"])
def refresh_token():
    """
    Refresh an expired token
    
    Request JSON:
    {
        "token": "jwt_token_here"
    }
    """
    try:
        data = request.get_json()
        token = data.get("token")
        
        if not token:
            return error_response("Token required", 400)
        
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'], options={"verify_exp": False})
            
            try:
                user_id = ObjectId(payload.get("user_id"))
            except:
                return error_response("Invalid user ID in token", 401)
            
            user = db.users.find_one({"_id": user_id})
            if not user:
                return error_response("User not found", 404)
            
            # Generate new token
            new_token = generate_token(user_id, payload.get("role"), payload.get("email"))
            
            return success_response({
                "token": new_token
            }, "Token refreshed successfully", 200)
            
        except jwt.InvalidTokenError:
            return error_response("Invalid token", 401)
            
    except Exception as e:
        return error_response(f"Token refresh error: {str(e)}", 500)

@auth_bp.route("/change-password", methods=["POST"])
@validate_json("email", "old_password", "new_password")
def change_password():
    """
    Change user password
    
    Request JSON:
    {
        "email": "john@example.com",
        "old_password": "old_password",
        "new_password": "new_password"
    }
    """
    try:
        data = request.get_json()
        email = data.get("email").lower().strip()
        
        user = db.users.find_one({"email": email})
        if not user:
            return error_response("User not found", 404)
        
        # Verify old password
        if not verify_password(data.get("old_password"), user.get("password", "")):
            return error_response("Incorrect old password", 401)
        
        # Hash new password
        new_hashed = hash_password(data.get("new_password"))
        
        # Update password
        db.users.update_one(
            {"email": email},
            {"$set": {
                "password": new_hashed,
                "updated_at": datetime.utcnow()
            }}
        )
        
        return success_response(message="Password changed successfully", status_code=200)
        
    except Exception as e:
        return error_response(f"Password change error: {str(e)}", 500)

@auth_bp.route("/user/<user_id>", methods=["GET"])
def get_user(user_id):
    """
    Get user profile information
    """
    try:
        try:
            user_obj_id = ObjectId(user_id)
        except:
            return error_response("Invalid user ID format", 400)
        
        user = db.users.find_one({"_id": user_obj_id})
        if not user:
            return error_response("User not found", 404)
        
        # Don't return password
        user_data = {
            "_id": str(user["_id"]),
            "name": user.get("name"),
            "email": user.get("email"),
            "id": user.get("id"),
            "role": user.get("role"),
            "status": user.get("status"),
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login")
        }
        
        return success_response(user_data)
        
    except Exception as e:
        return error_response(f"Error fetching user: {str(e)}", 500)
