#!/usr/bin/env python3
"""
Backend API Test Script
Tests all major endpoints to verify the backend is functioning correctly
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"
TOKEN = None

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name):
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}{Colors.END}")

def print_success(msg, data=None):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")
    if data:
        print(json.dumps(data, indent=2, default=str))

def print_error(msg, data=None):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")
    if data:
        print(json.dumps(data, indent=2, default=str))

def print_info(msg):
    print(f"{Colors.YELLOW}ℹ {msg}{Colors.END}")

def test_health():
    print_test("Health Check")
    try:
        resp = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if resp.status_code == 200:
            print_success("Server is healthy", resp.json())
            return True
        else:
            print_error(f"Health check failed: {resp.status_code}")
            return False
    except Exception as e:
        print_error(f"Cannot connect to server: {str(e)}")
        print_info(f"Make sure the backend is running: python backend/app.py")
        return False

def test_registration():
    global TOKEN
    print_test("User Registration")
    
    email = f"test_user_{int(time.time())}@example.com"
    payload = {
        "name": "Test Student",
        "email": email,
        "password": "TestPass123!",
        "id": f"TEST{int(time.time())}",
        "role": "student"
    }
    
    try:
        resp = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=payload,
            timeout=5
        )
        
        if resp.status_code == 201:
            data = resp.json()
            TOKEN = data.get("data", {}).get("token")
            print_success("Registration successful", data.get("data", {}).get("user"))
            return True, TOKEN
        else:
            print_error(f"Registration failed: {resp.status_code}", resp.json())
            return False, None
    except Exception as e:
        print_error(f"Registration error: {str(e)}")
        return False, None

def test_login():
    global TOKEN
    print_test("User Login")
    
    # First register a user
    email = f"login_test_{int(time.time())}@example.com"
    register_payload = {
        "name": "Login Test User",
        "email": email,
        "password": "LoginTest123!",
        "id": f"LOGIN{int(time.time())}",
        "role": "teacher"
    }
    
    # Create user first
    reg_resp = requests.post(
        f"{BASE_URL}/api/auth/register",
        json=register_payload,
        timeout=5
    )
    
    if reg_resp.status_code != 201:
        print_error("Failed to create test user for login")
        return False
    
    # Now test login
    login_payload = {
        "email": email,
        "password": "LoginTest123!"
    }
    
    try:
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_payload,
            timeout=5
        )
        
        if resp.status_code == 200:
            data = resp.json()
            TOKEN = data.get("data", {}).get("token")
            print_success("Login successful", data.get("data", {}).get("user"))
            return True
        else:
            print_error(f"Login failed: {resp.status_code}", resp.json())
            return False
    except Exception as e:
        print_error(f"Login error: {str(e)}")
        return False

def test_verify_token():
    print_test("Token Verification")
    
    if not TOKEN:
        print_info("No token available. Skipping token verification test.")
        return False
    
    payload = {"token": TOKEN}
    
    try:
        resp = requests.post(
            f"{BASE_URL}/api/auth/verify-token",
            json=payload,
            timeout=5
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print_success("Token is valid", data.get("data", {}))
            return True
        else:
            print_error(f"Token verification failed: {resp.status_code}", resp.json())
            return False
    except Exception as e:
        print_error(f"Token verification error: {str(e)}")
        return False

def test_get_user():
    print_test("Get User Profile")
    
    # Register a user first
    email = f"profile_test_{int(time.time())}@example.com"
    register_payload = {
        "name": "Profile Test User",
        "email": email,
        "password": "ProfileTest123!",
        "id": f"PROF{int(time.time())}",
        "role": "student"
    }
    
    reg_resp = requests.post(
        f"{BASE_URL}/api/auth/register",
        json=register_payload,
        timeout=5
    )
    
    if reg_resp.status_code != 201:
        print_error("Failed to create test user")
        return False
    
    user_id = reg_resp.json().get("data", {}).get("user", {}).get("_id")
    
    try:
        resp = requests.get(
            f"{BASE_URL}/api/auth/user/{user_id}",
            timeout=5
        )
        
        if resp.status_code == 200:
            print_success("User profile retrieved", resp.json().get("data", {}))
            return True
        else:
            print_error(f"Get user failed: {resp.status_code}", resp.json())
            return False
    except Exception as e:
        print_error(f"Get user error: {str(e)}")
        return False

def test_add_student():
    print_test("Add Student")
    
    payload = {
        "name": "Test Student for Attendance",
        "student_id": f"TEST{int(time.time())}",
        "email": f"student_{int(time.time())}@example.com",
        "department": "Computer Science",
        "phone": "9876543210"
    }
    
    try:
        resp = requests.post(
            f"{BASE_URL}/api/students/add",
            json=payload,
            timeout=5
        )
        
        if resp.status_code == 201:
            print_success("Student added successfully", resp.json().get("data", {}))
            return True, resp.json().get("data", {}).get("_id")
        else:
            print_error(f"Add student failed: {resp.status_code}", resp.json())
            return False, None
    except Exception as e:
        print_error(f"Add student error: {str(e)}")
        return False, None

def test_get_all_students():
    print_test("Get All Students (Paginated)")
    
    try:
        resp = requests.get(
            f"{BASE_URL}/api/students/?page=1&per_page=5",
            timeout=5
        )
        
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            count = len(data.get("students", []))
            pagination = data.get("pagination", {})
            print_success(
                f"Retrieved {count} students",
                {
                    "count": count,
                    "pagination": pagination
                }
            )
            return True
        else:
            print_error(f"Get students failed: {resp.status_code}", resp.json())
            return False
    except Exception as e:
        print_error(f"Get students error: {str(e)}")
        return False

def main():
    print(f"{Colors.BLUE}")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "FACE ATTENDANCE BACKEND TEST" + " "*15 + "║")
    print("╚" + "="*58 + "╝")
    print(f"{Colors.END}")
    
    print_info(f"Testing API at: {BASE_URL}")
    print_info(f"Start time: {datetime.now().isoformat()}")
    
    results = {
        "Health Check": False,
        "User Registration": False,
        "User Login": False,
        "Token Verification": False,
        "Get User Profile": False,
        "Add Student": False,
        "Get All Students": False
    }
    
    # Run tests
    results["Health Check"] = test_health()
    
    if results["Health Check"]:
        results["User Registration"] = test_registration()[0]
        results["User Login"] = test_login()
        results["Token Verification"] = test_verify_token()
        results["Get User Profile"] = test_get_user()
        results["Add Student"] = test_add_student()[0]
        results["Get All Students"] = test_get_all_students()
    
    # Summary
    print(f"\n{Colors.BLUE}")
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"{Colors.END}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}✓ PASS{Colors.END}" if result else f"{Colors.RED}✗ FAIL{Colors.END}"
        print(f"{test_name:<40} {status}")
    
    print(f"\n{Colors.BLUE}Result: {passed}/{total} tests passed{Colors.END}\n")
    
    if passed == total:
        print(f"{Colors.GREEN}All tests passed! Backend is working correctly.{Colors.END}")
    else:
        print(f"{Colors.YELLOW}Some tests failed. Check the backend logs.{Colors.END}")

if __name__ == "__main__":
    main()
