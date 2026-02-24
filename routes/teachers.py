"""
Routes for teacher management
"""
from flask import Blueprint, request
from datetime import datetime
from db import db
from utils.helpers import (
    success_response, error_response, validate_json, 
    object_id_to_string, generate_filename
)
from utils.face_utils import (
    save_uploaded_image, extract_face_encoding, 
    get_image_base64, cleanup_image, resize_image
)

teachers_bp = Blueprint("teachers", __name__)

@teachers_bp.route("/add", methods=["POST"])
@validate_json("name", "teacher_id", "department", "email")
def add_teacher():
    """
    Add a new teacher with face capture
    
    Request JSON:
    {
        "name": "Teacher Name",
        "teacher_id": "T001",
        "email": "teacher@example.com",
        "department": "Computer Science",
        "phone": "9876543210",
        "face_image": "base64_encoded_image"
    }
    """
    try:
        data = request.get_json()
        
        # Check if teacher already exists
        existing = db.teachers.find_one({"teacher_id": data["teacher_id"]})
        if existing:
            return error_response("Teacher ID already exists", 400)
        
        # Check email uniqueness
        email_exists = db.teachers.find_one({"email": data["email"]})
        if email_exists:
            return error_response("Email already exists", 400)
        
        teacher_data = {
            "name": data.get("name"),
            "teacher_id": data.get("teacher_id"),
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
                    teacher_data["face_encoding"] = encoding
                    teacher_data["face_image_path"] = image_path
                    teacher_data["face_image_base64"] = get_image_base64(image_path)
                else:
                    return error_response("No face detected in image", 400)
            except Exception as e:
                return error_response(f"Error processing face image: {str(e)}", 400)
        
        result = db.teachers.insert_one(teacher_data)
        teacher_data["_id"] = str(result.inserted_id)
        
        return success_response(
            object_id_to_string(teacher_data),
            "Teacher added successfully",
            201
        )
    except Exception as e:
        return error_response(f"Error adding teacher: {str(e)}", 500)

@teachers_bp.route("/<teacher_id>", methods=["GET"])
def get_teacher(teacher_id):
    """
    Get a specific teacher by ID
    """
    try:
        teacher = db.teachers.find_one({"teacher_id": teacher_id})
        
        if not teacher:
            return error_response("Teacher not found", 404)
        
        return success_response(object_id_to_string(teacher))
    except Exception as e:
        return error_response(f"Error fetching teacher: {str(e)}", 500)

@teachers_bp.route("/", methods=["GET"])
def get_all_teachers():
    """
    Get all teachers with pagination
    
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
        total = db.teachers.count_documents(filter_criteria)
        skip = (page - 1) * per_page
        
        teachers = list(
            db.teachers.find(filter_criteria)
            .skip(skip)
            .limit(per_page)
            .sort("created_at", -1)
        )
        
        return success_response({
            "teachers": [object_id_to_string(t) for t in teachers],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
        })
    except Exception as e:
        return error_response(f"Error fetching teachers: {str(e)}", 500)

@teachers_bp.route("/<teacher_id>", methods=["PUT"])
@validate_json()
def update_teacher(teacher_id):
    """
    Update teacher information
    """
    try:
        data = request.get_json()
        
        teacher = db.teachers.find_one({"teacher_id": teacher_id})
        if not teacher:
            return error_response("Teacher not found", 404)
        
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
                if teacher.get("face_image_path"):
                    cleanup_image(teacher["face_image_path"])
                
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
        
        db.teachers.update_one(
            {"teacher_id": teacher_id},
            {"$set": update_data}
        )
        
        updated_teacher = db.teachers.find_one({"teacher_id": teacher_id})
        return success_response(
            object_id_to_string(updated_teacher),
            "Teacher updated successfully"
        )
    except Exception as e:
        return error_response(f"Error updating teacher: {str(e)}", 500)

@teachers_bp.route("/<teacher_id>", methods=["DELETE"])
def delete_teacher(teacher_id):
    """
    Delete a teacher (soft delete)
    """
    try:
        teacher = db.teachers.find_one({"teacher_id": teacher_id})
        if not teacher:
            return error_response("Teacher not found", 404)
        
        # Cleanup face image
        if teacher.get("face_image_path"):
            cleanup_image(teacher["face_image_path"])
        
        # Soft delete
        db.teachers.update_one(
            {"teacher_id": teacher_id},
            {"$set": {"status": "deleted", "updated_at": datetime.utcnow()}}
        )
        
        return success_response(message="Teacher deleted successfully")
    except Exception as e:
        return error_response(f"Error deleting teacher: {str(e)}", 500)

@teachers_bp.route("/<teacher_id>/subjects", methods=["GET"])
def get_teacher_subjects(teacher_id):
    """
    Get all subjects taught by a teacher
    """
    try:
        teacher = db.teachers.find_one({"teacher_id": teacher_id})
        if not teacher:
            return error_response("Teacher not found", 404)
        
        subjects = list(db.subjects.find({"teacher_id": teacher_id}))
        
        return success_response({
            "teacher_id": teacher_id,
            "subjects": [object_id_to_string(s) for s in subjects],
            "count": len(subjects)
        })
    except Exception as e:
        return error_response(f"Error fetching subjects: {str(e)}", 500)

@teachers_bp.route("/search", methods=["GET"])
def search_teachers():
    """
    Search teachers by name or ID
    
    Query parameters:
    - q: Search query
    """
    try:
        query = request.args.get("q", "", type=str)
        
        if not query or len(query) < 2:
            return error_response("Search query too short", 400)
        
        results = list(
            db.teachers.find({
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"teacher_id": {"$regex": query, "$options": "i"}},
                    {"email": {"$regex": query, "$options": "i"}}
                ]
            }).limit(10)
        )
        
        return success_response({
            "query": query,
            "results": [object_id_to_string(t) for t in results],
            "count": len(results)
        })
    except Exception as e:
        return error_response(f"Error searching teachers: {str(e)}", 500)
