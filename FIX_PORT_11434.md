# Fix Port 11434 Already in Use

## Problem
Port 11434 is already in use on your laptop, preventing SSH tunnel from binding.

## Solution Options

### Option 1: Kill Processes Using Port 11434 (Recommended)

**Step 1: Find the processes:**
```bash
netstat -ano | findstr :11434
```

**Step 2: Kill the processes:**
```bash
# Kill process 52436
taskkill /PID 52436 /F

# Kill process 50220
taskkill /PID 50220 /F

# Kill process 64580
taskkill /PID 64580 /F
```

**Step 3: Verify port is free:**
```bash
netstat -ano | findstr :11434
```
(Should return nothing)

**Step 4: Create SSH tunnel:**
```bash
ssh -f -N -L 11434:localhost:11434 rivemain@192.178.90.31
```

### Option 2: Use Different Port (Alternative)

If you can't kill the processes, use a different port:

**Create tunnel on different port:**
```bash
ssh -f -N -L 11435:localhost:11434 rivemain@192.178.90.31
```

**Update your .env file:**
```bash
OLLAMA_BASE_URL=http://localhost:11435
```

### Option 3: Check if Ollama is Running on Laptop

**Check if Ollama is installed and running on your laptop:**
```bash
# Check if Ollama process exists
tasklist | findstr ollama

# If found, stop it:
# (Ollama shouldn't be running on laptop, only on Mac Studio)
```

## Quick Fix Script

**Create a batch file to kill processes and start tunnel:**

**File: `scripts/fix_and_tunnel.bat`**
```batch
@echo off
echo Killing processes on port 11434...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :11434') do (
    echo Killing PID %%a
    taskkill /PID %%a /F 2>nul
)
timeout /t 2 /nobreak >nul
echo Starting SSH tunnel...
ssh -f -N -L 11434:localhost:11434 rivemain@192.178.90.31
echo Done! Test with: curl http://localhost:11434/api/tags
```

**Run it:**
```bash
scripts\fix_and_tunnel.bat
```

