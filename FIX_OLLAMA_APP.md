# Fix Ollama.app Not Responding

## Problem
Ollama.app (PID 724) is running but returning "Empty reply from server".

## Solution: Stop Ollama.app and Start Command Line Version

### Step 1: Stop Ollama.app

**On Mac Studio terminal, run:**
```bash
# Stop the Ollama.app process
kill 724

# OR force kill if needed
kill -9 724

# Wait a moment
sleep 2

# Verify it's stopped
ps aux | grep ollama
```

**Should only see the `grep` process.**

### Step 2: Quit Ollama.app Completely

**On Mac Studio:**
1. Open **Activity Monitor** (Applications → Utilities → Activity Monitor)
2. Search for "ollama"
3. Quit all Ollama processes

**OR use command:**
```bash
# Quit Ollama.app
osascript -e 'quit app "Ollama"'

# Wait
sleep 2

# Verify
ps aux | grep ollama
```

### Step 3: Start Clean Ollama Instance

**On Mac Studio terminal, run:**
```bash
# Start Ollama with explicit configuration
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

**Keep this terminal open** - Ollama needs to keep running.

### Step 4: Test in New Terminal

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
      ...
    }
  ]
}
```

### Step 5: Verify It's Working

**Check the process:**
```bash
ps aux | grep ollama
```

**Should see:**
- One `ollama serve` process (the one you just started)
- The `grep` process

## Alternative: Fix Ollama.app Configuration

If you prefer to use Ollama.app:

### Step 1: Quit Ollama.app

**On Mac Studio:**
- Click Ollama icon in menu bar
- Select "Quit Ollama"

**OR:**
```bash
osascript -e 'quit app "Ollama"'
```

### Step 2: Check Ollama.app Settings

**On Mac Studio:**
1. Open Ollama.app
2. Check settings/preferences
3. Ensure it's configured to listen on `0.0.0.0:11434`

### Step 3: Restart Ollama.app

**On Mac Studio:**
- Open Ollama.app from Applications
- Or run: `open -a Ollama`

## Recommended: Use Command Line Version

**For better control, use command line:**

**On Mac Studio, create a startup script:**

```bash
#!/bin/bash
# File: ~/start_ollama.sh

# Stop any existing Ollama
pkill ollama
sleep 2

# Start Ollama with correct configuration
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

**Make executable:**
```bash
chmod +x ~/start_ollama.sh
```

**Run it:**
```bash
~/start_ollama.sh
```

## After Ollama is Working

### Step 1: Create SSH Tunnel from Laptop

**On your laptop (Windows), run:**
```bash
ssh -f -N -L 11435:localhost:11434 thrivestudio@192.168.50.29
```

### Step 2: Test Tunnel

**On your laptop:**
```bash
curl http://localhost:11435/api/tags
```

## Quick Fix Command

**On Mac Studio, run this one-liner:**
```bash
kill 724 && sleep 2 && osascript -e 'quit app "Ollama"' && sleep 2 && OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

**Then test in new terminal:**
```bash
curl http://localhost:11434/api/tags
```

