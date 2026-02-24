"""
Database initialization and MongoDB connection setup
"""

import logging
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from config import MONGODB_URI, DATABASE_NAME

logger = logging.getLogger(__name__)

# Global DB instance
db = None


def connect_db():
    """
    Connect to MongoDB and return database instance.
    Falls back to mock DB if MongoDB not reachable.
    """
    global db
    if db is not None:
        return db

    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")  # Test connection
        db = client[DATABASE_NAME]

        create_indexes(db)
        logger.info("Connected to MongoDB successfully.")

        return db

    except ServerSelectionTimeoutError as e:
        logger.error(f"MongoDB connection failed: {e}")
        logger.warning("Using in-memory mock database.")
        db = create_mock_db()
        return db

    except Exception as e:
        logger.error(f"Unexpected DB error: {e}")
        db = create_mock_db()
        return db


import json
import os

# ---------- MOCK DB (JSON Persistence) ---------- #
def create_mock_db():
    class MockDatabase:
        def __init__(self):
            self.file_path = "mock_db.json"
            self.collections = {}
            self.load()

        def load(self):
            if os.path.exists(self.file_path):
                try:
                    with open(self.file_path, 'r') as f:
                        data = json.load(f)
                        for name, items in data.items():
                            self.collections[name] = MockCollection(name, items, self)
                except Exception as e:
                    print(f"Error loading mock db: {e}")

        def save(self):
            data = {name: col.data for name, col in self.collections.items()}
            try:
                with open(self.file_path, 'w') as f:
                    json.dump(data, f, default=str, indent=2)
            except Exception as e:
                print(f"Error saving mock db: {e}")

        def __getitem__(self, name):
            if name not in self.collections:
                self.collections[name] = MockCollection(name, [], self)
            return self.collections[name]

    class MockCollection:
        def __init__(self, name, data, db_ref):
            self.name = name
            self.data = data
            self.db_ref = db_ref

        def insert_one(self, doc):
            if "_id" not in doc:
                doc["_id"] = str(len(self.data) + 1)
            self.data.append(doc)
            self.db_ref.save()
            return type("Result", (), {"inserted_id": doc["_id"]})()

        def find_one(self, query=None):
            if not query:
                return self.data[0] if self.data else None
            for doc in self.data:
                if all(str(doc.get(k)) == str(v) for k, v in query.items()):
                    return doc
            return None

        def find(self, query=None):
            if not query:
                return self.data
            result = []
            for doc in self.data:
                match = True
                for k, v in query.items():
                    if isinstance(v, dict):
                         # Handle simple $regex or operators if needed, for now skip complex
                         pass 
                    elif str(doc.get(k)) != str(v):
                        match = False
                        break
                if match:
                    result.append(doc)
            return result

        def update_one(self, query, update):
            for doc in self.data:
                 if all(str(doc.get(k)) == str(v) for k, v in query.items()):
                    doc.update(update.get("$set", {}))
                    self.db_ref.save()
                    return type("Result", (), {"modified_count": 1})()
            return type("Result", (), {"modified_count": 0})()
            
        def delete_one(self, query):
             for i, doc in enumerate(self.data):
                if all(str(doc.get(k)) == str(v) for k, v in query.items()):
                    del self.data[i]
                    self.db_ref.save()
                    return type("Result", (), {"deleted_count": 1})()
             return type("Result", (), {"deleted_count": 0})()

        def create_index(self, *args, **kwargs):
            pass
            
        def count_documents(self, query):
             return len(self.find(query))
             
        def skip(self, n):
            return self

        def limit(self, n):
            return self

        def sort(self, *args):
            return self

    return MockDatabase()


# ---------- INDEXES ---------- #
def create_indexes(db):
    """
    Create indexes for performance
    """
    try:
        # Users
        db.users.create_index("email", unique=True)
        db.users.create_index("id", unique=True)
        
        # Students
        db.students.create_index("student_id", unique=True)
        db.students.create_index("email", unique=True)

        # Teachers
        db.teachers.create_index("teacher_id", unique=True)
        db.teachers.create_index("email", unique=True)

        # Attendance
        db.attendance.create_index([("student_id", 1), ("date", 1)])

        # Subjects
        db.subjects.create_index("teacher_id")

        # Face encodings
        db.face_encodings.create_index("student_id", unique=True)
        db.face_encodings.create_index("teacher_id", unique=True)

        logger.info("Indexes created successfully.")

    except Exception as e:
        logger.warning(f"Index creation failed: {e}")


# Initialize connection when file is imported
db = connect_db()
