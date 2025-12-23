# Disable Ollama on Laptop - Use Mac Studio Instead

## Your Situation
- ✅ Mac Studio: Has Ollama running (512GB RAM - perfect!)
- ❌ Laptop: Has Ollama installed but can't use it (limited RAM)
- 🎯 Goal: Use Mac Studio's Ollama from laptop

## Solution: Disable Ollama on Laptop

### Step 1: Stop Ollama Service on Windows

**Open PowerShell as Administrator:**

1. Press `Windows + X`
2. Select "Windows PowerShell (Admin)" or "Terminal (Admin)"
3. Run these commands:

```powershell
# Stop Ollama service
Stop-Service -Name "Ollama" -ErrorAction SilentlyContinue

# Disable Ollama from auto-starting
Set-Service -Name "Ollama" -StartupType Disabled

# Verify it's disabled
Get-Service -Name "Ollama" | Select-Object Name, Status, StartType
```

**Expected output:**
```
Name   Status StartType
----   ------ ---------
Ollama Stopped Disabled
```

### Step 2: Kill All Ollama Processes

**In the same PowerShell (Admin), run:**
```powershell
# Kill all Ollama processes
Get-Process ollama -ErrorAction SilentlyContinue | Stop-Process -Force

# Verify no Ollama processes are running
Get-Process ollama -ErrorAction SilentlyContinue
```
(Should return nothing)

### Step 3: Verify Port 11434 is Free

```powershell
netstat -ano | findstr :11434
```
(Should return nothing - port is free)

### Step 4: Create SSH Tunnel to Mac Studio

**Now create the tunnel (in regular PowerShell, not Admin):**
```bash
ssh -f -N -L 11434:localhost:11434 rivemain@192.178.90.31
```

**OR if you prefer port 11435 (to avoid any future conflicts):**
```bash
ssh -f -N -L 11435:localhost:11434 rivemain@192.178.90.31
```

### Step 5: Test Connection

**Test the tunnel:**
```bash
# If using port 11434:
curl http://localhost:11434/api/tags

# OR if using port 11435:
curl http://localhost:11435/api/tags
```

**Expected output:**
```json
{
  "models": [
    {
      "name": "qwen2.5:32b-instruct",
      "size": 19000000000,
      ...
    }
  ]
}
```

### Step 6: Configure Your Backend

**Update `backend/.env`:**
```bash
# LLM Provider
LLM_PROVIDER=ollama

# Ollama Configuration (Mac Studio via SSH tunnel)
OLLAMA_BASE_URL=http://localhost:11434
# OR if using port 11435:
# OLLAMA_BASE_URL=http://localhost:11435

OLLAMA_MODEL=qwen2.5:32b-instruct
OLLAMA_FALLBACK_MODEL=llama3:70b
OLLAMA_TIMEOUT=120
```

## Quick Script to Do Everything

**Create `scripts/setup_mac_studio_ollama.bat`:**

```batch
@echo off
echo ========================================
echo Setting up Mac Studio Ollama connection
echo ========================================
echo.

echo Step 1: Stopping Ollama service...
net stop Ollama 2>nul
sc config Ollama start= disabled 2>nul
echo Ollama service disabled.

echo.
echo Step 2: Killing Ollama processes...
taskkill /F /IM ollama.exe 2>nul
timeout /t 2 /nobreak >nul
echo Ollama processes stopped.

echo.
echo Step 3: Checking port 11434...
netstat -ano | findstr :11434
if %errorlevel% equ 0 (
    echo WARNING: Port 11434 still in use!
    echo You may need to restart your computer.
) else (
    echo Port 11434 is free!
)

echo.
echo Step 4: Creating SSH tunnel...
echo Command: ssh -f -N -L 11434:localhost:11434 rivemain@192.178.90.31
echo.
echo NOTE: You will be prompted for SSH password
echo.

ssh -f -N -L 11434:localhost:11434 rivemain@192.178.90.31

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Setup complete!
    echo ========================================
    echo.
    echo Test with: curl http://localhost:11434/api/tags
) else (
    echo.
    echo ========================================
    echo SSH tunnel failed!
    echo ========================================
    echo.
    echo Please check:
    echo 1. Mac Studio IP: 192.178.90.31
    echo 2. SSH user: rivemain
    echo 3. Mac Studio is accessible
)

pause
```

## Daily Workflow

### Every Morning:

1. **Start SSH tunnel:**
   ```bash
   ssh -f -N -L 11434:localhost:11434 rivemain@192.178.90.31
   ```

2. **Test connection:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. **Start your backend:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

### Every Evening (Optional):

**Stop SSH tunnel:**
```bash
# Find SSH process
netstat -ano | findstr :11434

# Kill it (replace PID)
taskkill /PID <PID> /F
```

## Troubleshooting

### Issue: Ollama service won't stop

**Solution:**
1. Open Services (Windows + R, type `services.msc`)
2. Find "Ollama" service
3. Right-click → Stop
4. Right-click → Properties → Startup type: Disabled

### Issue: Port still in use after stopping service

**Solution:**
1. Restart your laptop
2. Then create SSH tunnel

### Issue: SSH tunnel disconnects

**Solution:**
1. Use background tunnel: `ssh -f -N -L 11434:localhost:11434 rivemain@192.178.90.31`
2. Or create a script that auto-reconnects

## Summary

✅ **Disable Ollama on laptop** (you don't need it)  
✅ **Use Mac Studio's Ollama** (512GB RAM - perfect!)  
✅ **Connect via SSH tunnel** (secure and simple)  

Your laptop will now use Mac Studio's powerful Ollama instance! 🚀

