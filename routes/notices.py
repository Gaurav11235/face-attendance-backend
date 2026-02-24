"""
Routes for notice management
"""
from flask import Blueprint, request
from datetime import datetime
from bson import ObjectId
from db import db
from utils.helpers import (
    success_response, error_response, validate_json, object_id_to_string
)

notices_bp = Blueprint("notices", __name__)

@notices_bp.route("/", methods=["GET"])
def get_notices():
    """Get all notices"""
    try:
        notices = list(db.notices.find().sort("created_at", -1))
        return success_response([object_id_to_string(n) for n in notices])
    except Exception as e:
        return error_response(f"Error fetching notices: {str(e)}", 500)

@notices_bp.route("/", methods=["POST"])
@validate_json("title", "description", "target_class")
def create_notice():
    """Create a new notice"""
    try:
        data = request.get_json()
        notice_data = {
            "title": data.get("title"),
            "description": data.get("description"),
            "target_class": data.get("target_class"),
            "created_at": datetime.utcnow(),
            "date_str": datetime.now().strftime("%b %d, %Y")
        }
        result = db.notices.insert_one(notice_data)
        notice_data["_id"] = str(result.inserted_id)
        return success_response(object_id_to_string(notice_data), "Notice created", 201)
    except Exception as e:
        return error_response(f"Error creating notice: {str(e)}", 500)

@notices_bp.route("/<notice_id>", methods=["PUT"])
@validate_json()
def update_notice(notice_id):
    """Update an existing notice"""
    try:
        data = request.get_json()
        update_data = {}
        for field in ["title", "description", "target_class"]:
            if field in data:
                update_data[field] = data[field]
        
        update_data["updated_at"] = datetime.utcnow()
        db.notices.update_one({"_id": ObjectId(notice_id)}, {"$set": update_data})
        return success_response(None, "Notice updated")
    except Exception as e:
        return error_response(f"Error updating notice: {str(e)}", 500)

@notices_bp.route("/<notice_id>", methods=["DELETE"])
def delete_notice(notice_id):
    """Delete a notice"""
    try:
        db.notices.delete_one({"_id": ObjectId(notice_id)})
        return success_response(None, "Notice deleted")
    except Exception as e:
        return error_response(f"Error deleting notice: {str(e)}", 500)
