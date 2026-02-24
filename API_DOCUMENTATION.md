# Face Attendance System - Backend API Documentation

## Overview
Comprehensive REST API backend for a Face Recognition-based Attendance System built with Flask and MongoDB. The system enables automated attendance marking using facial recognition technology.

## Features
- ✅ Student and Teacher Management
- ✅ Face Recognition-based Attendance Marking
- ✅ Real-time Attendance Tracking
- ✅ Bluetooth Device Proximity Detection
- ✅ Attendance Statistics and Reports
- ✅ Subject Management
- ✅ Hardware Device Management
- ✅ Comprehensive Error Handling

## Technology Stack
- **Framework**: Flask 2.3.3
- **Database**: MongoDB
- **Face Recognition**: face_recognition library
- **Image Processing**: OpenCV, Pillow
- **Data Handling**: NumPy, PyMongo

## Project Structure

```
backend/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── db.py                 # Database connection and initialization
├── requirements.txt      # Python dependencies
├── routes/
│   ├── __init__.py
│   ├── students.py       # Student management endpoints
│   ├── teachers.py       # Teacher management endpoints
│   ├── attendance.py     # Attendance marking and tracking
│   ├── hardware.py       # Hardware device management
│   ├── subjects.py       # Subject management
│   └── devices.py        # Device routes wrapper
├── utils/
│   ├── __init__.py
│   ├── face_utils.py     # Face recognition utilities
│   └── helpers.py        # Helper functions and decorators
└── uploads/              # Uploaded face images storage
```

## Installation

### Prerequisites
- Python 3.8+
- MongoDB Atlas account (or local MongoDB)
- pip (Python package manager)

### Setup Steps

1. **Install Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

2. **Configure MongoDB Connection**
   - Update `config.py` or set environment variables:
   ```bash
   export MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/face_attendance"
   ```

3. **Run the Server**
```bash
python app.py
```

The API will start on `http://0.0.0.0:5000`

## API Endpoints

### Health Check
- **GET** `/api/health` - Server health status

### Students
- **POST** `/api/students/add` - Add new student with face image
- **GET** `/api/students/<student_id>` - Get student details
- **GET** `/api/students/` - List all students (paginated)
- **PUT** `/api/students/<student_id>` - Update student info
- **DELETE** `/api/students/<student_id>` - Delete student (soft delete)
- **GET** `/api/students/attendance/<student_id>` - Get student attendance
- **GET** `/api/students/search` - Search students by name/ID/email

### Teachers
- **POST** `/api/teachers/add` - Add new teacher with face image
- **GET** `/api/teachers/<teacher_id>` - Get teacher details
- **GET** `/api/teachers/` - List all teachers (paginated)
- **PUT** `/api/teachers/<teacher_id>` - Update teacher info
- **DELETE** `/api/teachers/<teacher_id>` - Delete teacher
- **GET** `/api/teachers/<teacher_id>/subjects` - Get teacher's subjects
- **GET** `/api/teachers/search` - Search teachers

### Attendance
- **POST** `/api/attendance/mark` - Mark attendance using face recognition
- **POST** `/api/attendance/manual` - Manual attendance marking (admin)
- **GET** `/api/attendance/records` - Get attendance records (filtered)
- **GET** `/api/attendance/statistics` - Get attendance statistics
- **GET** `/api/attendance/summary` - Get daily attendance summary

### Hardware/Devices
- **GET** `/api/hardware/devices` - List all devices
- **POST** `/api/hardware/devices` - Register new device
- **GET** `/api/hardware/devices/<device_id>` - Get device details
- **PUT** `/api/hardware/devices/<device_id>` - Update device
- **POST** `/api/hardware/devices/<device_id>/sync` - Sync device
- **DELETE** `/api/hardware/devices/<device_id>` - Deregister device
- **GET** `/api/hardware/teacher-devices` - Get active teacher devices
- **GET** `/api/hardware/devices/<device_id>/logs` - Get device logs

### Subjects
- **GET** `/api/subjects/` - List all subjects
- **POST** `/api/subjects/` - Create new subject
- **GET** `/api/subjects/<subject_id>` - Get subject details
- **PUT** `/api/subjects/<subject_id>` - Update subject
- **GET** `/api/subjects/<subject_id>/attendance` - Get subject attendance

## Request/Response Format

### Success Response
```json
{
  "success": true,
  "message": "Success message",
  "data": {},
  "timestamp": "2024-02-07T10:30:00"
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-02-07T10:30:00"
}
```

## Common Request Examples

### Add Student
```json
POST /api/students/add
{
  "name": "Gaurav Pal",
  "student_id": "22034001",
  "email": "gaurav@example.com",
  "department": "Computer Science",
  "phone": "9876543210",
  "face_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABA..."
}
```

### Mark Attendance
```json
POST /api/attendance/mark
{
  "student_id": "22034001",
  "face_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABA...",
  "location": "Classroom A",
  "subject": "Mathematics"
}
```

### Get Attendance Records
```
GET /api/attendance/records?student_id=22034001&start_date=2024-02-01&end_date=2024-02-07&page=1&per_page=20
```

## Database Schema

### Students Collection
```javascript
{
  _id: ObjectId,
  name: String,
  student_id: String (unique),
  email: String (unique),
  department: String,
  phone: String,
  face_encoding: Array,
  face_image_path: String,
  status: String (active/inactive/deleted),
  created_at: Date,
  updated_at: Date
}
```

### Attendance Collection
```javascript
{
  _id: ObjectId,
  student_id: String,
  student_name: String,
  date: Date,
  time: Date,
  status: String (Present/Absent),
  location: String,
  subject: String,
  face_match_distance: Number,
  created_at: Date
}
```

### Teachers Collection
```javascript
{
  _id: ObjectId,
  name: String,
  teacher_id: String (unique),
  email: String (unique),
  department: String,
  phone: String,
  face_encoding: Array,
  face_image_path: String,
  status: String,
  created_at: Date,
  updated_at: Date
}
```

### Devices Collection
```javascript
{
  _id: ObjectId,
  device_id: String (unique),
  device_name: String,
  device_type: String,
  location: String,
  mac_address: String,
  ip_address: String,
  status: String,
  last_sync: Date,
  created_at: Date,
  updated_at: Date
}
```

## Configuration

Edit `config.py` to customize:
- MongoDB connection URI
- Upload folder location
- Face recognition threshold (0.6 default)
- Maximum file size (50MB default)
- API host and port

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid input or missing required fields |
| 401 | Unauthorized | Face recognition failed |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server error |

## Face Recognition

The system uses the `face_recognition` library which is based on deep learning (dlib's ResNet):

- **Extract Face Encoding**: Converts face image to 128-dimensional vector
- **Compare Encodings**: Calculates Euclidean distance between vectors
- **Threshold**: Default distance threshold is 0.6 (configurable)
- **Accuracy**: ~99.3% accuracy on LFW benchmark

## Security Considerations

1. **Image Storage**: Face images are stored with timestamp-based filenames
2. **Encoding Storage**: Only face encodings stored, not raw pixel data
3. **Soft Delete**: Students/Teachers marked as deleted, not permanently removed
4. **Error Handling**: Detailed errors logged, generic messages to clients
5. **CORS**: Enabled for specified domains

## Performance Optimization

1. **Indexes**: Created on frequently queried fields
2. **Pagination**: All list endpoints support pagination
3. **Soft Delete**: Deleted records excluded from queries
4. **Caching**: Can be added for frequently accessed data

## Deployment

### Local Development
```bash
python app.py
```

### Production (with Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

## Troubleshooting

### MongoDB Connection Issues
- Verify connection string in config.py
- Check network connectivity
- Ensure IP whitelist includes server IP

### Face Recognition Errors
- Ensure face is clearly visible and well-lit
- Check image resolution (minimum recommended: 100x100 pixels)
- Verify face encoding was extracted during registration

### File Upload Issues
- Check `uploads` folder permissions
- Verify disk space availability
- Check MAX_CONTENT_LENGTH setting

## Future Enhancements

- [ ] JWT Authentication and Authorization
- [ ] Role-based access control (RBAC)
- [ ] Real-time notifications
- [ ] Batch attendance import/export
- [ ] Advanced statistics and reporting
- [ ] Mobile app integration
- [ ] Cloud image storage (AWS S3)
- [ ] Multi-factor authentication

## Support

For issues or questions, contact the development team or refer to the troubleshooting section above.

## License

Proprietary - Face Attendance System
