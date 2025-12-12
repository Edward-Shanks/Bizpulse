# How to Start the Server

## ⚠️ Important: Always Activate Virtual Environment First!

The server **MUST** be run with the virtual environment activated, otherwise you'll get `ModuleNotFoundError`.

## Method 1: Use the Startup Script (Recommended)

```powershell
.\start_new_server.ps1
```

This script will:
- ✅ Check if venv exists
- ✅ Activate the virtual environment automatically
- ✅ Start the server with reload enabled

## Method 2: Manual Activation

### Step 1: Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

You should see `(venv)` in your prompt:
```
(venv) PS C:\Users\Sumit Mishra\Documents\Bizpulse\backend>
```

### Step 2: Start Server
```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Or with auto-reload (for development):
```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Method 3: Direct Python Execution

If you want to run it directly:
```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Verify Virtual Environment is Active

Check if you're using the venv Python:
```powershell
python -c "import sys; print(sys.executable)"
```

Should show:
```
C:\Users\Sumit Mishra\Documents\Bizpulse\backend\venv\Scripts\python.exe
```

## Troubleshooting

### Error: `ModuleNotFoundError: No module named 'fastapi'`

**Solution:** Virtual environment is not activated!
1. Activate venv: `.\venv\Scripts\Activate.ps1`
2. Verify: `python -c "import fastapi; print('OK')"`
3. If still fails, reinstall: `pip install -r requirements.txt`

### Error: `[Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000)`

**Solution:** Port 8000 is already in use!
1. Stop existing server: `.\stop_server.ps1`
2. Or use a different port: `--port 8001`

### Error: `ExecutionPolicy` error when activating venv

**Solution:** Run this command once:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Quick Commands Reference

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Start server (with reload)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Stop server
.\stop_server.ps1

# Check if server is running
curl http://localhost:8000/health
```

---

**Remember:** Always activate the virtual environment before running Python commands!
