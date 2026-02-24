"""
Routes for student management
"""
from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
from db import db
from utils.helpers import (
    success_response, error_response, validate_json, 
    object_id_to_string, generate_filename, add_student_stats
)
from utils.face_utils import (
    save_uploaded_image, extract_face_encoding, 
    get_image_base64, cleanup_image, resize_image
)

students_bp = Blueprint("students", __name__)

@students_bp.route("/add", methods=["POST"])
@validate_json("name", "student_id", "department", "email")
def add_student():
    """
    Add a new student with face capture
    
    Request JSON:
    {
        "name": "Student Name",
        "student_id": "22034001",
        "email": "student@example.com",
        "department": "Computer Science",
        "phone": "9876543210",
        "face_image": "base64_encoded_image"
    }
    """
    try:
        data = request.get_json()
        
        # Check if student already exists
        existing = db.students.find_one({"student_id": data["student_id"]})
        if existing:
            return error_response("Student ID already exists", 400)
        
        # Check email uniqueness
        email_exists = db.students.find_one({"email": data["email"]})
        if email_exists:
            return error_response("Email already exists", 400)
        
        student_data = {
            "name": data.get("name"),
            "student_id": data.get("student_id"),
            "email": data.get("email"),
            "department": data.get("department"),
            "phone": data.get("phone", ""),
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Handle face image if provided
        if data.get("face_image"):
            try:
                filename = generate_filename()
                image_path = save_uploaded_image(data["face_image"], filename)
                
                # Resize image to ensure faster processing
                resize_image(image_path)
                
                # Extract face encoding
                encoding = extract_face_encoding(image_path)
                
                if encoding:
                    student_data["face_encoding"] = encoding
                    student_data["face_image_path"] = image_path
                    student_data["face_image_base64"] = get_image_base64(image_path)
                else:
                    return error_response("No face detected in image", 400)
            except Exception as e:
                return error_response(f"Error processing face image: {str(e)}", 400)
        
        result = db.students.insert_one(student_data)
        student_data["_id"] = str(result.inserted_id)
        
        return success_response(
            object_id_to_string(student_data),
            "Student added successfully",
            201
        )
    except Exception as e:
        return error_response(f"Error adding student: {str(e)}", 500)

@students_bp.route("/<student_id>", methods=["GET"])
def get_student(student_id):
    """
    Get a specific student by ID
    """
    try:
        student = db.students.find_one({"student_id": student_id})
        
        if not student:
            return error_response("Student not found", 404)
        
        student = add_student_stats(student)
        return success_response(object_id_to_string(student))
    except Exception as e:
        return error_response(f"Error fetching student: {str(e)}", 500)

@students_bp.route("/", methods=["GET"])
def get_all_students():
    """
    Get all students with pagination
    
    Query parameters:
    - page: Page number (default: 1)
    - per_page: Results per page (default: 10)
    - department: Filter by department
    - status: Filter by status (active/inactive)
    """
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        department = request.args.get("department", type=str)
        status = request.args.get("status", type=str)
        
        # Build filter
        filter_criteria = {}
        if department:
            filter_criteria["department"] = department
        if status:
            filter_criteria["status"] = status
        
        # Query and paginate
        total = db.students.count_documents(filter_criteria)
        skip = (page - 1) * per_page
        
        students = list(
            db.students.find(filter_criteria)
            .skip(skip)
            .limit(per_page)
            .sort("created_at", -1)
        )
        
        return success_response({
            "students": [object_id_to_string(add_student_stats(s)) for s in students],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
        })
    except Exception as e:
        return error_response(f"Error fetching students: {str(e)}", 500)

@students_bp.route("/<student_id>", methods=["PUT"])
@validate_json()
def update_student(student_id):
    """
    Update student information
    """
    try:
        data = request.get_json()
        
        student = db.students.find_one({"student_id": student_id})
        if not student:
            return error_response("Student not found", 404)
        
        # Prepare update data
        update_data = {}
        allowed_fields = ["name", "email", "phone", "department", "status"]
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        # Handle face image update
        if data.get("face_image"):
            try:
                # Remove old image if exists
                if student.get("face_image_path"):
                    cleanup_image(student["face_image_path"])
                
                filename = generate_filename()
                image_path = save_uploaded_image(data["face_image"], filename)
                
                # Resize image
                resize_image(image_path)
                
                encoding = extract_face_encoding(image_path)
                
                if encoding:
                    update_data["face_encoding"] = encoding
                    update_data["face_image_path"] = image_path
                    update_data["face_image_base64"] = get_image_base64(image_path)
                else:
                    return error_response("No face detected in image", 400)
            except Exception as e:
                return error_response(f"Error processing face image: {str(e)}", 400)
        
        update_data["updated_at"] = datetime.utcnow()
        
        db.students.update_one(
            {"student_id": student_id},
            {"$set": update_data}
        )
        
        updated_student = db.students.find_one({"student_id": student_id})
        return success_response(
            object_id_to_string(updated_student),
            "Student updated successfully"
        )
    except Exception as e:
        return error_response(f"Error updating student: {str(e)}", 500)

@students_bp.route("/<student_id>", methods=["DELETE"])
def delete_student(student_id):
    """
    Delete a student (soft delete)
    """
    try:
        student = db.students.find_one({"student_id": student_id})
        if not student:
            return error_response("Student not found", 404)
        
        # Cleanup face image
        if student.get("face_image_path"):
            cleanup_image(student["face_image_path"])
        
        # Soft delete
        db.students.update_one(
            {"student_id": student_id},
            {"$set": {"status": "deleted", "updated_at": datetime.utcnow()}}
        )
        
        return success_response(message="Student deleted successfully")
    except Exception as e:
        return error_response(f"Error deleting student: {str(e)}", 500)

@students_bp.route("/attendance/<student_id>", methods=["GET"])
def get_student_attendance(student_id):
    """
    Get attendance records for a specific student
    
    Query parameters:
    - start_date: Start date (ISO format)
    - end_date: End date (ISO format)
    """
    try:
        student = db.students.find_one({"student_id": student_id})
        if not student:
            return error_response("Student not found", 404)
        
        # Build filter
        filter_criteria = {"student_id": student_id}
        
        start_date = request.args.get("start_date", type=str)
        end_date = request.args.get("end_date", type=str)
        
        if start_date or end_date:
            filter_criteria["date"] = {}
            if start_date:
                filter_criteria["date"]["$gte"] = datetime.fromisoformat(start_date)
            if end_date:
                filter_criteria["date"]["$lte"] = datetime.fromisoformat(end_date)
        
        # Get attendance records
        records = list(
            db.attendance.find(filter_criteria)
            .sort("date", -1)
        )
        
        return success_response({
            "student_id": student_id,
            "records": [object_id_to_string(r) for r in records],
            "total": len(records)
        })
    except Exception as e:
        return error_response(f"Error fetching attendance: {str(e)}", 500)

@students_bp.route("/search", methods=["GET"])
def search_students():
    """
    Search students by name or ID
    
    Query parameters:
    - q: Search query
    """
    try:
        query = request.args.get("q", "", type=str)
        
        if not query or len(query) < 2:
            return error_response("Search query too short", 400)
        
        results = list(
            db.students.find({
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"student_id": {"$regex": query, "$options": "i"}},
                    {"email": {"$regex": query, "$options": "i"}}
                ]
            }).limit(10)
        )
        
        return success_response({
            "query": query,
            "results": [object_id_to_string(s) for s in results],
            "count": len(results)
        })
    except Exception as e:
        return error_response(f"Error searching students: {str(e)}", 500)

