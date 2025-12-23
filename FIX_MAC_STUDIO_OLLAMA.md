# Fix Mac Studio Ollama - Empty Reply from Server

## Problem
- Mac Studio IP: `192.168.50.29`
- Ollama returns "Empty reply from server" when accessing `http://localhost:11434/api/tags`

## Diagnosis

### Step 1: Check if Ollama is Running

**On Mac Studio terminal, run:**
```bash
ps aux | grep ollama
```

**Expected output:**
```
thrivestudio  ... /Applications/Ollama.app/Contents/Resources/ollama serve
```

If you don't see this, Ollama is not running.

### Step 2: Check if Port 11434 is Listening

**On Mac Studio, run:**
```bash
lsof -i :11434
```

**Expected output:**
```
COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
ollama   1234 user   3u  IPv6  ...      0t0  TCP *:11434 (LISTEN)
```

### Step 3: Check Ollama Service Status

**On Mac Studio, run:**
```bash
# Check if Ollama service is running
launchctl list | grep ollama

# OR check with systemctl (if using)
systemctl status ollama
```

## Solutions

### Solution 1: Restart Ollama Service

**On Mac Studio, run:**
```bash
# Stop Ollama
pkill ollama

# Wait a moment
sleep 2

# Start Ollama
ollama serve
```

**Keep this terminal open** and test in another terminal:
```bash
curl http://localhost:11434/api/tags
```

### Solution 2: Check Ollama Configuration

**On Mac Studio, check Ollama host configuration:**
```bash
# Check environment variables
env | grep OLLAMA

# Should see:
# OLLAMA_HOST=0.0.0.0:11434
```

**If not set, start Ollama with explicit host:**
```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

### Solution 3: Check Ollama Logs

**On Mac Studio, check for errors:**
```bash
# If using Launchd service
tail -f ~/Library/Logs/ollama.log

# OR check system logs
log show --predicate 'process == "ollama"' --last 5m
```

### Solution 4: Reinstall/Update Ollama

**On Mac Studio, if nothing works:**
```bash
# Update Ollama
brew upgrade ollama

# OR reinstall
brew uninstall ollama
brew install ollama
```

## Quick Fix Script

**On Mac Studio, create and run:**

```bash
#!/bin/bash
echo "Stopping Ollama..."
pkill ollama
sleep 2

echo "Starting Ollama with correct configuration..."
OLLAMA_HOST=0.0.0.0:11434 ollama serve &

sleep 3

echo "Testing Ollama..."
curl http://localhost:11434/api/tags

if [ $? -eq 0 ]; then
    echo "✅ Ollama is working!"
else
    echo "❌ Ollama still not responding"
fi
```

## After Fixing Ollama

### Step 1: Verify Ollama Works on Mac Studio

**On Mac Studio:**
```bash
curl http://localhost:11434/api/tags
```

**Should return:**
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

### Step 2: Create SSH Tunnel from Laptop

**On your laptop (Windows), use correct IP:**
```bash
ssh -f -N -L 11435:localhost:11434 thrivestudio@192.168.50.29
```

**Note:** 
- IP: `192.168.50.29` (not `192.178.90.31`)
- Username: `thrivestudio` (as shown in your terminal)

### Step 3: Test Tunnel from Laptop

**On your laptop:**
```bash
curl http://localhost:11435/api/tags
```

## Summary

1. ✅ Fix Ollama on Mac Studio first
2. ✅ Use correct IP: `192.168.50.29`
3. ✅ Use correct username: `thrivestudio`
4. ✅ Create tunnel: `ssh -f -N -L 11435:localhost:11434 thrivestudio@192.168.50.29`

