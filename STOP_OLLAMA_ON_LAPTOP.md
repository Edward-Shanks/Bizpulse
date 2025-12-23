# Stop Ollama on Laptop (Use Mac Studio Instead)

## Problem
Ollama is running on your laptop and auto-restarting, blocking port 11434.

## Solution: Disable Ollama Auto-Start on Windows

### Step 1: Stop Ollama Service

**Open PowerShell as Administrator and run:**
```powershell
# Stop Ollama service
Stop-Service -Name "Ollama" -ErrorAction SilentlyContinue

# Disable Ollama from auto-starting
Set-Service -Name "Ollama" -StartupType Disabled -ErrorAction SilentlyContinue
```

### Step 2: Kill All Ollama Processes

```powershell
# Kill all Ollama processes
Get-Process ollama -ErrorAction SilentlyContinue | Stop-Process -Force
```

### Step 3: Verify Port is Free

```powershell
netstat -ano | findstr :11434
```
(Should return nothing)

### Step 4: Create SSH Tunnel

```bash
ssh -f -N -L 11434:localhost:11434 rivemain@192.178.90.31
```

## Alternative: Use Different Port

If you want to keep Ollama on laptop for other purposes:

**Create tunnel on port 11435:**
```bash
ssh -f -N -L 11435:localhost:11434 rivemain@192.178.90.31
```

**Update your `.env` file:**
```bash
OLLAMA_BASE_URL=http://localhost:11435
```

## Quick Fix Script

**Run this batch file:**
```bash
scripts\kill_ollama_and_tunnel.bat
```

This will:
1. Kill all processes on port 11434
2. Create SSH tunnel automatically
3. Test the connection

