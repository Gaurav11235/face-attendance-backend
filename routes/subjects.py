"""
Routes for subject management
"""
from flask import Blueprint, request
from datetime import datetime
from bson import ObjectId
from db import db
from utils.helpers import (
    success_response, error_response, validate_json, object_id_to_string
)

subjects_bp = Blueprint("subjects", __name__)

@subjects_bp.route("/", methods=["GET"])
def get_all_subjects():
    """
    Get all subjects
    
    Query parameters:
    - teacher_id: Filter by teacher
    - department: Filter by department
    - page: Page number
    - per_page: Results per page
    """
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        
        filter_criteria = {}
        
        teacher_id = request.args.get("teacher_id", type=str)
        if teacher_id:
            filter_criteria["teacher_id"] = teacher_id
        
        department = request.args.get("department", type=str)
        if department:
            filter_criteria["department"] = department
        
        total = db.subjects.count_documents(filter_criteria)
        skip = (page - 1) * per_page
        
        subjects = list(
            db.subjects.find(filter_criteria)
            .skip(skip)
            .limit(per_page)
            .sort("created_at", -1)
        )
        
        return success_response({
            "subjects": [object_id_to_string(s) for s in subjects],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
        })
    except Exception as e:
        return error_response(f"Error fetching subjects: {str(e)}", 500)

@subjects_bp.route("/", methods=["POST"])
@validate_json("name", "code", "teacher_id", "department")
def create_subject():
    """
    Create a new subject
    
    Request JSON:
    {
        "name": "Mathematics",
        "code": "MATH101",
        "teacher_id": "T001",
        "department": "Computer Science",
        "credits": 4,
        "description": "Introduction to Mathematics"
    }
    """
    try:
        data = request.get_json()
        
        # Check if subject code already exists
        existing = db.subjects.find_one({"code": data["code"]})
        if existing:
            return error_response("Subject code already exists", 400)
        
        # Verify teacher exists
        teacher = db.teachers.find_one({"teacher_id": data["teacher_id"]})
        if not teacher:
            return error_response("Teacher not found", 404)
        
        subject_data = {
            "name": data.get("name"),
            "code": data.get("code"),
            "teacher_id": data.get("teacher_id"),
            "teacher_name": teacher.get("name"),
            "department": data.get("department"),
            "target_class": data.get("target_class", ""),
            "target_division": data.get("target_division", ""),
            "credits": data.get("credits", 0),
            "description": data.get("description", ""),
            "total_classes": 0,
            "syllabus_completion": 0, # New field
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = db.subjects.insert_one(subject_data)
        subject_data["_id"] = str(result.inserted_id)
        
        return success_response(
            object_id_to_string(subject_data),
            "Subject created successfully",
            201
        )
    except Exception as e:
        return error_response(f"Error creating subject: {str(e)}", 500)

@subjects_bp.route("/<subject_id>", methods=["GET"])
def get_subject(subject_id):
    """
    Get a specific subject
    """
    try:
        subject = db.subjects.find_one({"_id": ObjectId(subject_id)})
        
        if not subject:
            return error_response("Subject not found", 404)
        
        return success_response(object_id_to_string(subject))
    except Exception as e:
        return error_response(f"Error fetching subject: {str(e)}", 500)

@subjects_bp.route("/<subject_id>", methods=["PUT"])
@validate_json()
def update_subject(subject_id):
    """
    Update subject information
    """
    try:
        from bson import ObjectId
        
        data = request.get_json()
        subject = db.subjects.find_one({"_id": ObjectId(subject_id)})
        
        if not subject:
            return error_response("Subject not found", 404)
        
        update_data = {}
        allowed_fields = ["name", "description", "credits", "syllabus_completion", "target_class", "target_division"]
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        update_data["updated_at"] = datetime.utcnow()
        
        db.subjects.update_one(
            {"_id": ObjectId(subject_id)},
            {"$set": update_data}
        )
        
        updated_subject = db.subjects.find_one({"_id": ObjectId(subject_id)})
        return success_response(
            object_id_to_string(updated_subject),
            "Subject updated successfully"
        )
    except Exception as e:
        return error_response(f"Error updating subject: {str(e)}", 500)

@subjects_bp.route("/<subject_id>/attendance", methods=["GET"])
def get_subject_attendance(subject_id):
    """
    Get attendance records for a specific subject
    """
    try:
        from bson import ObjectId
        
        subject = db.subjects.find_one({"_id": ObjectId(subject_id)})
        if not subject:
            return error_response("Subject not found", 404)
        
        records = list(
            db.attendance.find({"subject": subject.get("name")})
            .sort("date", -1)
        )
        
        return success_response({
            "subject_id": subject_id,
            "subject_name": subject.get("name"),
            "records": [object_id_to_string(r) for r in records],
            "count": len(records)
        })
    except Exception as e:
        return error_response(f"Error fetching subject attendance: {str(e)}", 500)
