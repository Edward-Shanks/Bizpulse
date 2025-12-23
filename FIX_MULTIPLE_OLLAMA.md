# Fix Multiple Ollama Instances on Mac Studio

## Problem
You have **TWO Ollama instances running**:
- PID 724: Running from `/Applications/Ollama.app` (started 10:32AM)
- PID 16937: Running from command line (started 3:25PM)

This is causing conflicts and "Empty reply from server" errors.

## Solution: Stop All and Start One Clean Instance

### Step 1: Stop All Ollama Instances

**On Mac Studio terminal, run:**
```bash
# Stop all Ollama processes
pkill ollama

# Wait a moment
sleep 3

# Verify they're stopped
ps aux | grep ollama
```

**Should only see the `grep` process itself** (not actual Ollama processes).

### Step 2: Start One Clean Ollama Instance

**On Mac Studio terminal, run:**
```bash
# Start Ollama with explicit configuration
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

**Keep this terminal open** - Ollama needs to keep running.

### Step 3: Test Ollama in New Terminal

**Open a NEW terminal on Mac Studio and run:**
```bash
curl http://localhost:11434/api/tags
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

### Step 4: Verify Only One Instance

**In the new terminal, check:**
```bash
ps aux | grep ollama
```

**Should see:**
- One `ollama serve` process (the one you just started)
- The `grep` process itself

## After Ollama is Working

### Step 1: Create SSH Tunnel from Laptop

**On your laptop (Windows), run:**
```bash
ssh -f -N -L 11435:localhost:11434 thrivestudio@192.168.50.29
```

**Important:**
- IP: `192.168.50.29` (your Mac Studio IP)
- Username: `thrivestudio`

### Step 2: Test Tunnel from Laptop

**On your laptop:**
```bash
curl http://localhost:11435/api/tags
```

## Quick Fix Script

**On Mac Studio, create `fix_ollama.sh`:**

```bash
#!/bin/bash
echo "Stopping all Ollama instances..."
pkill ollama
sleep 3

echo "Verifying all stopped..."
ps aux | grep ollama | grep -v grep
if [ $? -eq 0 ]; then
    echo "⚠️  Some Ollama processes still running, forcing kill..."
    pkill -9 ollama
    sleep 2
fi

echo "Starting clean Ollama instance..."
OLLAMA_HOST=0.0.0.0:11434 ollama serve &
sleep 3

echo "Testing Ollama..."
curl -s http://localhost:11434/api/tags > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Ollama is working!"
    echo ""
    echo "Models available:"
    curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | head -5
else
    echo "❌ Ollama still not responding"
    echo "Check logs or try: ollama serve"
fi
```

**Make executable and run:**
```bash
chmod +x fix_ollama.sh
./fix_ollama.sh
```

## Prevent Multiple Instances

### Option 1: Disable Ollama Auto-Start

**On Mac Studio, check Launch Agents:**
```bash
ls ~/Library/LaunchAgents/ | grep ollama
```

**If found, disable:**
```bash
launchctl unload ~/Library/LaunchAgents/com.ollama.*.plist
```

### Option 2: Use Only One Method

**Choose ONE way to run Ollama:**
- **Option A**: Use Ollama.app (GUI) - don't run `ollama serve` manually
- **Option B**: Use command line - don't use Ollama.app

**Recommended:** Use command line for better control.

## Summary

1. ✅ Stop all Ollama instances: `pkill ollama`
2. ✅ Start one clean instance: `OLLAMA_HOST=0.0.0.0:11434 ollama serve`
3. ✅ Test: `curl http://localhost:11434/api/tags`
4. ✅ Create tunnel from laptop: `ssh -f -N -L 11435:localhost:11434 thrivestudio@192.168.50.29`
5. ✅ Test tunnel: `curl http://localhost:11435/api/tags`

