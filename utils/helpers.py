"""
Utility functions for API responses and common operations
"""
import logging
from datetime import datetime
from functools import wraps
from flask import jsonify, request
from bson import ObjectId

logger = logging.getLogger(__name__)

def success_response(data=None, message="Success", status_code=200):
    """
    Generate a standardized success response
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        
    Returns:
        tuple: (response dict, status_code)
    """
    response = {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    return jsonify(response), status_code

def error_response(message="Error", status_code=400, error_code=None):
    """
    Generate a standardized error response
    
    Args:
        message: Error message
        status_code: HTTP status code
        error_code: Custom error code
        
    Returns:
        tuple: (response dict, status_code)
    """
    response = {
        "success": False,
        "message": message,
        "error_code": error_code,
        "timestamp": datetime.utcnow().isoformat()
    }
    return jsonify(response), status_code

def validate_json(*required_fields):
    """
    Decorator to validate JSON request data
    
    Args:
        *required_fields: Required field names
        
    Returns:
        decorator: Validation decorator
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return error_response("Request must be JSON", 400)
            
            data = request.get_json()
            if data is None:
                return error_response("Invalid JSON data", 400)
            
            for field in required_fields:
                if field not in data:
                    return error_response(f"Missing required field: {field}", 400)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def object_id_to_string(obj):
    """
    Convert MongoDB ObjectId to string in dictionary
    
    Args:
        obj: Dictionary potentially containing ObjectId
        
    Returns:
        dict: Dictionary with ObjectId converted to string
    """
    if isinstance(obj, list):
        return [object_id_to_string(item) for item in obj]
    
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            if isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, dict):
                result[key] = object_id_to_string(value)
            elif isinstance(value, list):
                result[key] = object_id_to_string(value)
            else:
                result[key] = value
        return result
    
    if isinstance(obj, ObjectId):
        return str(obj)
    
    return obj

def paginate_results(query, page=1, per_page=10):
    """
    Paginate database query results
    
    Args:
        query: PyMongo cursor
        page: Page number
        per_page: Results per page
        
    Returns:
        tuple: (results, total_count, pages)
    """
    total_count = query.count_documents({})
    total_pages = (total_count + per_page - 1) // per_page
    
    skip = (page - 1) * per_page
    results = list(query.skip(skip).limit(per_page))
    
    return results, total_count, total_pages

def generate_filename(extension="jpg"):
    """
    Generate a unique filename with timestamp
    
    Args:
        extension: File extension
        
    Returns:
        str: Generated filename
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"img_{timestamp}.{extension}"

def add_student_stats(student):
    """
    Calculate and add attendance statistics to student document
    """
    if not student:
        return student
        
    total_att = student.get("total_attendance", 0)
    total_sessions = student.get("total_sessions", 0)
    
    # Calculate overall percentage
    if total_sessions > 0:
        student["attendance_percentage"] = round((total_att / total_sessions) * 100, 2)
    else:
        student["attendance_percentage"] = 0
        
    return student
