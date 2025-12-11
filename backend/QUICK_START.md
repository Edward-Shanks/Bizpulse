# Quick Start Guide - New Backend Architecture

## 🚀 Getting Started

### 1. Activate Virtual Environment
```powershell
cd backend
.\venv\Scripts\Activate.ps1
```

### 2. Start Server
```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Or use the provided script:
```powershell
.\start_new_server.ps1
```

### 3. Verify Server is Running
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

---

## 📍 API Endpoints

### Base URL
```
http://localhost:8000/api
```

### Authentication Required
Most endpoints require JWT authentication. Get a token by logging in:

```bash
POST /api/auth/login
{
  "email": "admin@thrivebrands.ai",
  "password": "Thrive@123"
}
```

Then include the token in all requests:
```
Authorization: Bearer <token>
```

---

## 🧪 Testing

### Run All Tests
```powershell
python test_all_migrated_endpoints.py
```

### Test Specific Endpoints
```powershell
# Test Insights Chat
python test_insights_chat.py

# Test Customer Insights Chat
python test_customer_insights.py

# Test Strategic Recommendations
python test_strategic_recommendations.py
```

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── core/                # Core functionality
│   ├── models/              # Pydantic models
│   ├── repositories/        # Data access layer
│   ├── services/            # Business logic
│   ├── utils/               # Utilities
│   └── api/v1/routes/       # API routes
```

---

## 🔑 Key Files

- **`app/main.py`**: Application entry point
- **`app/core/config.py`**: Configuration settings
- **`app/core/database.py`**: Database connection
- **`app/api/v1/api.py`**: Route aggregation

---

## 📝 Common Tasks

### Add a New Endpoint

1. Create model in `app/models/`
2. Create repository in `app/repositories/` (if needed)
3. Create service in `app/services/`
4. Create route in `app/api/v1/routes/`
5. Register route in `app/api/v1/api.py`

### Debug an Issue

1. Check server logs for error messages
2. Review test results
3. Check database connection
4. Verify environment variables

---

## 🆘 Troubleshooting

### Server Won't Start
- Check if port 8000 is available
- Verify virtual environment is activated
- Check MongoDB connection
- Review environment variables

### Endpoint Returns 404
- Verify route is registered in `app/api/v1/api.py`
- Check route path matches frontend expectations
- Restart server after adding new routes

### Authentication Fails
- Verify JWT_SECRET in `.env`
- Check user status is "active"
- Verify token is included in Authorization header

---

## 📚 Documentation

- **Full Migration Summary**: `MIGRATION_COMPLETE.md`
- **Architecture Guide**: `ARCHITECTURE_GUIDE.md`
- **Migration Progress**: `MIGRATION_PROGRESS.md`

---

*For detailed information, see `MIGRATION_COMPLETE.md`*

