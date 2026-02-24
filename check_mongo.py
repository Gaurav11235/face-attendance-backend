import sys
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Add current directory to path so we can import config if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import MONGODB_URI
except ImportError:
    MONGODB_URI = "mongodb://localhost:27017"

def check_mongo():
    print(f"Attempting to connect to MongoDB at: {MONGODB_URI}")
    print("---------------------------------------------------")
    
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        print("✅ SUCCESS: Connected to MongoDB!")
        print(f"   Server version: {client.server_info()['version']}")
        return True
    except ServerSelectionTimeoutError:
        print("❌ FAILURE: Could not connect to MongoDB.")
        print("   Reason: Connection timed out.")
        print("\n   Troubleshooting:")
        print("   1. Is the MongoDB service running?")
        print("   2. Can you connect with MongoDB Compass?")
        print("   3. Is it listening on localhost:27017?")
        return False
    except ConnectionFailure:
        print("❌ FAILURE: Connection refused.")
        return False
    except Exception as e:
        print(f"❌ ERROR: An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    check_mongo()
