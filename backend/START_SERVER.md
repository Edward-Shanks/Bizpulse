# How to Start the New Backend Server

## Step-by-Step Instructions

### 1. Open PowerShell or Command Prompt
Navigate to the backend directory:
```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
```

### 2. Activate Virtual Environment

**For PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**For Command Prompt (cmd):**
```cmd
venv\Scripts\activate.bat
```

**Alternative (if PowerShell execution policy blocks it):**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

### 3. Verify Venv is Activated
You should see `(venv)` at the beginning of your command prompt:
```
(venv) PS C:\Users\Sumit Mishra\Documents\Bizpulse\backend>
```

### 4. Start the Server
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Verify Server is Running
You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Quick Test Commands

Once the server is running, test the endpoints:

### Test Health Check
```powershell
curl http://localhost:8000/health
```

### Test Root Endpoint
```powershell
curl http://localhost:8000/
```

### Test Login (Get Token)
```powershell
curl -X POST "http://localhost:8000/api/auth/login" -H "Content-Type: application/json" -d '{\"email\": \"data.admin@thrivebrands.ai\", \"password\": \"ThriveBrands@2024\"}'
```

## Troubleshooting

### If venv activation fails:
1. Make sure you're in the `backend` directory
2. Check that `venv` folder exists
3. Try using Command Prompt instead of PowerShell

### If server fails to start:
1. Check that all dependencies are installed: `pip install -r requirements.txt`
2. Verify `.env` file exists and has correct `MONGO_URL` and `DB_NAME`
3. Check MongoDB is running and accessible

### If you see import errors:
1. Make sure venv is activated (you should see `(venv)` in prompt)
2. Reinstall dependencies: `pip install -r requirements.txt`

## Stopping the Server

Press `CTRL+C` in the terminal where the server is running.



