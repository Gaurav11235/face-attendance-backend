"""
Routes for device management (keeping 'devices' Blueprint name for imports)
"""
from flask import Blueprint

# Import from hardware module
from routes.hardware import hardware_bp

# Create alias for backward compatibility
devices_bp = hardware_bp
