# Testing Guide - New Backend Architecture

## Quick Start Testing

### 1. Activate Virtual Environment
```bash
cd backend
# On Windows
venv\Scripts\activate
# On Linux/Mac
source venv/bin/activate
```

### 2. Start the New Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test Endpoints

#### Authentication
```bash
# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "data.admin@thrivebrands.ai", "password": "ThriveBrands@2024"}'

# Signup (requires auth token)
curl -X POST "http://localhost:8000/api/auth/signup" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"email": "test@example.com", "password": "password123", "name": "Test User", "department": "sales", "role": "Manager"}'
```

#### Users
```bash
# Get all users (requires auth)
curl -X GET "http://localhost:8000/api/users" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get current user
curl -X GET "http://localhost:8000/api/users/me" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get users by department
curl -X GET "http://localhost:8000/api/users/by-department/sales" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Data
```bash
# Sync data from Azure
curl -X GET "http://localhost:8000/api/data/sync" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get data source info
curl -X GET "http://localhost:8000/api/data/source" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Expected Results

### Login Response
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "email": "data.admin@thrivebrands.ai"
}
```

### Users Response
```json
[
  {
    "id": "...",
    "email": "data.admin@thrivebrands.ai",
    "name": "Data Admin",
    "department": "technology",
    "role": "VP",
    "status": "active"
  }
]
```

### Data Sync Response
```json
{
  "status": "success",
  "message": "Loaded from Azure",
  "records_count": 12345
}
```

## Troubleshooting

### Import Errors
- Make sure virtual environment is activated
- Install dependencies: `pip install -r requirements.txt`

### Database Connection Errors
- Check `.env` file has correct `MONGO_URL` and `DB_NAME`
- Verify MongoDB is running and accessible

### Authentication Errors
- Verify JWT_SECRET in `.env` matches
- Check token expiration
- Ensure user exists in database

## Next Steps

Once these endpoints are tested and working:
1. Continue with Analytics service and routes
2. Continue with Filter service and routes
3. Continue with remaining endpoints



