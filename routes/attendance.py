"""
Routes for attendance management
"""
from flask import Blueprint, request
from datetime import datetime, timedelta
from db import db
from utils.helpers import (
    success_response, error_response, validate_json, object_id_to_string
)
from utils.face_utils import extract_face_encoding, compare_face_encodings

attendance_bp = Blueprint("attendance", __name__)

@attendance_bp.route("/mark", methods=["POST"])
@validate_json("student_id", "face_image")
def mark_attendance():
    """
    Mark attendance using face recognition
    
    Request JSON:
    {
        "student_id": "22034001",
        "face_image": "base64_encoded_image",
        "location": "Classroom A",
        "subject": "Mathematics"
    }
    """
    try:
        data = request.get_json()
        student_id = data.get("student_id")
        
        # Get student
        student = db.students.find_one({"student_id": student_id})
        if not student:
            return error_response("Student not found", 404)
        
        # Check if already marked today for this specific subject
        subject_name = data.get("subject", "General")
        today = datetime.utcnow().date()
        existing = db.attendance.find_one({
            "student_id": student_id,
            "subject": subject_name,
            "date": {
                "$gte": datetime(today.year, today.month, today.day),
                "$lt": datetime(today.year, today.month, today.day) + timedelta(days=1)
            }
        })
        
        if existing:
            return error_response(f"Attendance already marked for {subject_name} today", 400)
        
        # Extract face encoding from image
        from utils.face_utils import save_uploaded_image, cleanup_image
        from config import UPLOAD_FOLDER
        import os
        
        filename = f"temp_{datetime.utcnow().timestamp()}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        try:
            from utils.face_utils import save_uploaded_image
            image_path = save_uploaded_image(data["face_image"], filename)
            unknown_encoding = extract_face_encoding(image_path)
            
            if not unknown_encoding:
                cleanup_image(image_path)
                return error_response("No face detected in image", 400)
            
            # Compare with student's face encoding
            student_encoding = student.get("face_encoding")
            
            # Lazy Registration: If student has no face encoding, save this one!
            if not student_encoding:
                # Update student record with this face
                db.students.update_one(
                    {"student_id": student_id},
                    {
                        "$set": {
                            "face_encoding": unknown_encoding,
                            "face_image_path": image_path,
                            "face_image_base64": data["face_image"],
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                match_found = True
                distance = 0.0 # Exact match since it's the reference
                print(f"Lazy registration for student {student_id}")
            else:
                # Standard comparison
                match_found, distance = compare_face_encodings(
                    [student_encoding], 
                    unknown_encoding
                )
            
            cleanup_image(image_path)
            
            if not match_found:
                return error_response("Face does not match student record", 401)
            
        except Exception as e:
            if os.path.exists(filepath):
                cleanup_image(filepath)
            return error_response(f"Face recognition error: {str(e)}", 400)
        
        # Mark attendance
        attendance_record = {
            "student_id": student_id,
            "student_name": student.get("name"),
            "date": datetime.utcnow(),
            "time": datetime.utcnow(),
            "status": "Present",
            "location": data.get("location", ""),
            "subject": data.get("subject", ""),
            "face_match_distance": distance,
            "created_at": datetime.utcnow()
        }
        
        result = db.attendance.insert_one(attendance_record)
        attendance_record["_id"] = str(result.inserted_id)
        
        # Update student's total attendance and subject-wise attendance
        subject_name = attendance_record.get('subject', 'General')
        update_query = {
            "$inc": {
                "total_attendance": 1,
                "total_sessions": 1,
                f"subjects_attendance.{subject_name}": 1,
                f"subjects_total.{subject_name}": 1
            },
            "$set": {"updated_at": datetime.utcnow()}
        }
        db.students.update_one({"student_id": student_id}, update_query)
        
        return success_response(
            object_id_to_string(attendance_record),
            "Attendance marked successfully",
            201
        )
    except Exception as e:
        return error_response(f"Error marking attendance: {str(e)}", 500)

@attendance_bp.route("/records", methods=["GET"])
def get_attendance_records():
    """
    Get attendance records with filters
    
    Query parameters:
    - student_id: Filter by student
    - date: Filter by date (ISO format)
    - start_date: Filter from date
    - end_date: Filter to date
    - status: Filter by status
    - page: Page number
    - per_page: Results per page
    """
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        
        filter_criteria = {}
        
        # Add filters
        student_id = request.args.get("student_id", type=str)
        if student_id:
            filter_criteria["student_id"] = student_id
        
        date_str = request.args.get("date", type=str)
        if date_str:
            date = datetime.fromisoformat(date_str).date()
            filter_criteria["date"] = {
                "$gte": datetime(date.year, date.month, date.day),
                "$lt": datetime(date.year, date.month, date.day) + timedelta(days=1)
            }
        else:
            start_date = request.args.get("start_date", type=str)
            end_date = request.args.get("end_date", type=str)
            
            if start_date or end_date:
                filter_criteria["date"] = {}
                if start_date:
                    filter_criteria["date"]["$gte"] = datetime.fromisoformat(start_date)
                if end_date:
                    filter_criteria["date"]["$lte"] = datetime.fromisoformat(end_date)
        
        status = request.args.get("status", type=str)
        if status:
            filter_criteria["status"] = status
        
        # Query and paginate
        total = db.attendance.count_documents(filter_criteria)
        skip = (page - 1) * per_page
        
        records = list(
            db.attendance.find(filter_criteria)
            .skip(skip)
            .limit(per_page)
            .sort("date", -1)
        )
        
        return success_response({
            "records": [object_id_to_string(r) for r in records],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
        })
    except Exception as e:
        return error_response(f"Error fetching records: {str(e)}", 500)

@attendance_bp.route("/statistics", methods=["GET"])
def get_attendance_statistics():
    """
    Get attendance statistics
    
    Query parameters:
    - student_id: Filter by student
    - start_date: Filter from date
    - end_date: Filter to date
    """
    try:
        filter_criteria = {}
        
        student_id = request.args.get("student_id", type=str)
        if student_id:
            filter_criteria["student_id"] = student_id
        
        start_date = request.args.get("start_date", type=str)
        end_date = request.args.get("end_date", type=str)
        
        if start_date or end_date:
            filter_criteria["date"] = {}
            if start_date:
                filter_criteria["date"]["$gte"] = datetime.fromisoformat(start_date)
            if end_date:
                filter_criteria["date"]["$lte"] = datetime.fromisoformat(end_date)
        
        # Get total and present count
        total_records = db.attendance.count_documents(filter_criteria)
        present_records = db.attendance.count_documents({
            **filter_criteria,
            "status": "Present"
        })
        
        # Calculate percentage
        attendance_percentage = (present_records / total_records * 100) if total_records > 0 else 0
        
        return success_response({
            "total_classes": total_records,
            "present_count": present_records,
            "absent_count": total_records - present_records,
            "attendance_percentage": round(attendance_percentage, 2)
        })
    except Exception as e:
        return error_response(f"Error calculating statistics: {str(e)}", 500)

@attendance_bp.route("/summary", methods=["GET"])
def get_attendance_summary():
    """
    Get attendance summary for all students
    
    Query parameters:
    - date: Specific date (ISO format)
    - department: Filter by department
    """
    try:
        filter_criteria = {}
        
        date_str = request.args.get("date", type=str)
        if date_str:
            date = datetime.fromisoformat(date_str).date()
            filter_criteria["date"] = {
                "$gte": datetime(date.year, date.month, date.day),
                "$lt": datetime(date.year, date.month, date.day) + timedelta(days=1)
            }
        else:
            # Default to today
            today = datetime.utcnow().date()
            filter_criteria["date"] = {
                "$gte": datetime(today.year, today.month, today.day),
                "$lt": datetime(today.year, today.month, today.day) + timedelta(days=1)
            }
        
        # Get all attendance records for the date
        records = list(db.attendance.find(filter_criteria))
        
        # Group by department if available
        summary = {}
        total_present = 0
        total_absent = 0
        
        for record in records:
            if record.get("status") == "Present":
                total_present += 1
            else:
                total_absent += 1
        
        return success_response({
            "date": date_str or datetime.utcnow().date().isoformat(),
            "total_present": total_present,
            "total_absent": total_absent,
            "total_records": len(records),
            "records": [object_id_to_string(r) for r in records]
        })
    except Exception as e:
        return error_response(f"Error generating summary: {str(e)}", 500)

@attendance_bp.route("/<attendance_id>", methods=["PUT"])
def update_attendance(attendance_id):
    """Update an attendance record (Override)"""
    try:
        data = request.get_json()
        update_data = {}
        if "status" in data: update_data["status"] = data["status"]
        if "reason" in data: update_data["reason"] = data["reason"]
        
        update_data["updated_at"] = datetime.utcnow()
        db.attendance.update_one({"_id": ObjectId(attendance_id)}, {"$set": update_data})
        return success_response(None, "Attendance record updated")
    except Exception as e:
        return error_response(f"Error updating attendance: {str(e)}", 500)

@attendance_bp.route("/manual", methods=["POST"])
@validate_json("student_id", "date", "status", "subject")
def mark_attendance_manual():
    """
    Manually mark attendance
    """
    try:
        data = request.get_json()
        student_id = data.get("student_id")
        subject_name = data.get("subject")
        
        # Get student
        student = db.students.find_one({"student_id": student_id})
        if not student:
            return error_response("Student not found", 404)
        
        # Parse date
        attendance_date = datetime.fromisoformat(data.get("date"))
        date_only = attendance_date.date()
        
        # Check if already marked for this subject on this date
        existing = db.attendance.find_one({
            "student_id": student_id,
            "subject": subject_name,
            "date": {
                "$gte": datetime(date_only.year, date_only.month, date_only.day),
                "$lt": datetime(date_only.year, date_only.month, date_only.day) + timedelta(days=1)
            }
        })
        
        if existing:
            return error_response(f"Attendance already marked for {subject_name} today", 400)
        
        # Mark attendance
        attendance_record = {
            "student_id": student_id,
            "student_name": student.get("name"),
            "subject": subject_name,
            "date": attendance_date,
            "status": data.get("status", "Present"),
            "reason": data.get("reason", ""),
            "marked_by": "teacher",
            "marked_at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        
        result = db.attendance.insert_one(attendance_record)
        attendance_record["_id"] = str(result.inserted_id)
        
        # Update student's total attendance and subject-wise attendance
        update_query = {
            "$inc": {
                "total_attendance": 1,
                "total_sessions": 1,
                f"subjects_attendance.{subject_name}": 1,
                f"subjects_total.{subject_name}": 1
            },
            "$set": {"updated_at": datetime.utcnow()}
        }
        db.students.update_one({"student_id": student_id}, update_query)
        
        return success_response(
            object_id_to_string(attendance_record),
            "Attendance marked successfully",
            201
        )
    except Exception as e:
        return error_response(f"Error marking attendance: {str(e)}", 500)
