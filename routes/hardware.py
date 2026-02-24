"""
Routes for hardware/device management (Bluetooth devices)
"""
from flask import Blueprint, request
from datetime import datetime
from db import db
from utils.helpers import (
    success_response, error_response, validate_json, object_id_to_string
)

hardware_bp = Blueprint("hardware", __name__)

@hardware_bp.route("/devices", methods=["GET"])
def get_devices():
    """
    Get all registered hardware devices
    
    Query parameters:
    - type: Filter by device type (teacher_device, attendance_terminal, etc.)
    - status: Filter by status (active/inactive)
    """
    try:
        filter_criteria = {}
        
        device_type = request.args.get("type", type=str)
        if device_type:
            filter_criteria["device_type"] = device_type
        
        status = request.args.get("status", type=str)
        if status:
            filter_criteria["status"] = status
        
        devices = list(
            db.devices.find(filter_criteria)
            .sort("created_at", -1)
        )
        
        return success_response({
            "devices": [object_id_to_string(d) for d in devices],
            "count": len(devices)
        })
    except Exception as e:
        return error_response(f"Error fetching devices: {str(e)}", 500)

@hardware_bp.route("/devices", methods=["POST"])
@validate_json("device_id", "device_name", "device_type")
def register_device():
    """
    Register a new hardware device
    
    Request JSON:
    {
        "device_id": "device_uuid",
        "device_name": "Classroom A Terminal",
        "device_type": "attendance_terminal",
        "location": "Block A, Room 101",
        "mac_address": "00:1A:2B:3C:4D:5E",
        "ip_address": "192.168.1.100"
    }
    """
    try:
        data = request.get_json()
        
        # Check if device already exists
        existing = db.devices.find_one({"device_id": data["device_id"]})
        if existing:
            return error_response("Device already registered", 400)
        
        device_data = {
            "device_id": data.get("device_id"),
            "device_name": data.get("device_name"),
            "device_type": data.get("device_type"),
            "location": data.get("location", ""),
            "mac_address": data.get("mac_address", ""),
            "ip_address": data.get("ip_address", ""),
            "status": "active",
            "last_sync": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = db.devices.insert_one(device_data)
        device_data["_id"] = str(result.inserted_id)
        
        return success_response(
            object_id_to_string(device_data),
            "Device registered successfully",
            201
        )
    except Exception as e:
        return error_response(f"Error registering device: {str(e)}", 500)

@hardware_bp.route("/devices/<device_id>", methods=["GET"])
def get_device(device_id):
    """
    Get specific device details
    """
    try:
        device = db.devices.find_one({"device_id": device_id})
        
        if not device:
            return error_response("Device not found", 404)
        
        return success_response(object_id_to_string(device))
    except Exception as e:
        return error_response(f"Error fetching device: {str(e)}", 500)

@hardware_bp.route("/devices/<device_id>", methods=["PUT"])
@validate_json()
def update_device(device_id):
    """
    Update device information
    """
    try:
        data = request.get_json()
        
        device = db.devices.find_one({"device_id": device_id})
        if not device:
            return error_response("Device not found", 404)
        
        # Prepare update data
        update_data = {}
        allowed_fields = ["device_name", "location", "status", "mac_address", "ip_address"]
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        update_data["updated_at"] = datetime.utcnow()
        
        db.devices.update_one(
            {"device_id": device_id},
            {"$set": update_data}
        )
        
        updated_device = db.devices.find_one({"device_id": device_id})
        return success_response(
            object_id_to_string(updated_device),
            "Device updated successfully"
        )
    except Exception as e:
        return error_response(f"Error updating device: {str(e)}", 500)

@hardware_bp.route("/devices/<device_id>/sync", methods=["POST"])
def sync_device(device_id):
    """
    Update device sync time and status
    """
    try:
        device = db.devices.find_one({"device_id": device_id})
        if not device:
            return error_response("Device not found", 404)
        
        db.devices.update_one(
            {"device_id": device_id},
            {
                "$set": {
                    "last_sync": datetime.utcnow(),
                    "status": "active"
                }
            }
        )
        
        updated_device = db.devices.find_one({"device_id": device_id})
        return success_response(
            object_id_to_string(updated_device),
            "Device synced successfully"
        )
    except Exception as e:
        return error_response(f"Error syncing device: {str(e)}", 500)

@hardware_bp.route("/devices/<device_id>", methods=["DELETE"])
def delete_device(device_id):
    """
    Deregister a device
    """
    try:
        device = db.devices.find_one({"device_id": device_id})
        if not device:
            return error_response("Device not found", 404)
        
        db.devices.delete_one({"device_id": device_id})
        
        return success_response(message="Device deleted successfully")
    except Exception as e:
        return error_response(f"Error deleting device: {str(e)}", 500)

@hardware_bp.route("/teacher-devices", methods=["GET"])
def get_teacher_devices():
    """
    Get all registered teacher devices for Bluetooth proximity checking
    """
    try:
        devices = list(
            db.devices.find({"device_type": "teacher_device", "status": "active"})
        )
        
        return success_response({
            "devices": [object_id_to_string(d) for d in devices],
            "count": len(devices)
        })
    except Exception as e:
        return error_response(f"Error fetching teacher devices: {str(e)}", 500)

@hardware_bp.route("/devices/<device_id>/logs", methods=["GET"])
def get_device_logs(device_id):
    """
    Get logs for a specific device
    
    Query parameters:
    - page: Page number
    - per_page: Results per page
    """
    try:
        device = db.devices.find_one({"device_id": device_id})
        if not device:
            return error_response("Device not found", 404)
        
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        
        total = db.device_logs.count_documents({"device_id": device_id})
        skip = (page - 1) * per_page
        
        logs = list(
            db.device_logs.find({"device_id": device_id})
            .skip(skip)
            .limit(per_page)
            .sort("timestamp", -1)
        )
        
        return success_response({
            "device_id": device_id,
            "logs": [object_id_to_string(l) for l in logs],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
        })
    except Exception as e:
        return error_response(f"Error fetching logs: {str(e)}", 500)
