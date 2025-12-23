# Use Different Port for SSH Tunnel (Easiest Solution)

## Problem
Ollama keeps restarting on your laptop, blocking port 11434.

## Solution: Use Port 11435 for Tunnel

Since Ollama on your laptop keeps restarting, let's use a **different port** for the SSH tunnel.

### Step 1: Create SSH Tunnel on Port 11435

**On your laptop, run:**
```bash
ssh -f -N -L 11435:localhost:11434 rivemain@192.178.90.31
```

**This forwards:**
- Your laptop's `localhost:11435` → Mac Studio's `localhost:11434`

### Step 2: Update Your .env File

**Edit `backend/.env`:**
```bash
# Change this line:
OLLAMA_BASE_URL=http://localhost:11434

# To this:
OLLAMA_BASE_URL=http://localhost:11435
```

### Step 3: Test Connection

```bash
curl http://localhost:11435/api/tags
```

**Expected output:**
```json
{
  "models": [
    {
      "name": "qwen2.5:32b-instruct",
      ...
    }
  ]
}
```

### Step 4: Update Test Script

**Edit `scripts/test_ollama_connection.py` and change:**
```python
base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11435")
```

## Why This Works

- Port 11434: Used by Ollama on your laptop (can't change this)
- Port 11435: Used for SSH tunnel to Mac Studio (we control this)
- No conflicts: Both can run simultaneously

## Quick Command Reference

**Start tunnel:**
```bash
ssh -f -N -L 11435:localhost:11434 rivemain@192.178.90.31
```

**Test tunnel:**
```bash
curl http://localhost:11435/api/tags
```

**Stop tunnel:**
```bash
# Find SSH process
netstat -ano | findstr :11435

# Kill it (replace PID with actual process ID)
taskkill /PID <PID> /F
```

