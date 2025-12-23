# Complete Ollama Fix - Stop Auto-Restart and Fix API

## Problem
- Ollama.app keeps auto-restarting
- HTTP API returns "Empty reply from server"
- `ollama ls` works but API doesn't

## Complete Solution

### Step 1: Stop ALL Ollama Instances (Force Kill)

**On Mac Studio terminal, run:**
```bash
# Force kill all Ollama processes
pkill -9 ollama

# Wait
sleep 3

# Verify all stopped
ps aux | grep ollama | grep -v grep
```

**Should return nothing.**

### Step 2: Disable Ollama.app Auto-Start

**On Mac Studio, run:**
```bash
# Check for Launch Agents
ls ~/Library/LaunchAgents/ | grep -i ollama

# If found, unload them
launchctl list | grep -i ollama

# Disable login items (Ollama.app might be in login items)
osascript -e 'tell application "System Events" to get the name of every login item'
```

**Remove Ollama from login items:**
1. System Settings → Users & Groups → Login Items
2. Remove Ollama if present

### Step 3: Check What Port Ollama is Using

**On Mac Studio, run:**
```bash
# Check what's listening on port 11434
lsof -i :11434

# OR
netstat -an | grep 11434
```

### Step 4: Start Clean Ollama with Verbose Logging

**On Mac Studio, run:**
```bash
# Start with explicit host and verbose output
OLLAMA_HOST=0.0.0.0:11434 OLLAMA_DEBUG=1 ollama serve
```

**Keep this terminal open** and watch for any errors.

### Step 5: Test in New Terminal

**Open NEW terminal and run:**
```bash
# Test API
curl -v http://localhost:11434/api/tags

# OR test with specific model
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:32b-instruct",
  "prompt": "test",
  "stream": false
}'
```

## Alternative: Reinstall Ollama

If nothing works, reinstall:

### Step 1: Uninstall Ollama

```bash
# Remove Ollama.app
rm -rf /Applications/Ollama.app

# Remove Ollama data (optional - keeps models)
# rm -rf ~/.ollama

# Remove Launch Agents
rm -f ~/Library/LaunchAgents/*ollama*
```

### Step 2: Reinstall Ollama

```bash
# Install via Homebrew
brew install ollama

# OR download from ollama.ai
```

### Step 3: Start Fresh

```bash
# Start with clean config
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

## Quick Diagnostic Script

**Create `diagnose_ollama.sh` on Mac Studio:**

```bash
#!/bin/bash
echo "=== Ollama Diagnostic ==="
echo ""

echo "1. Checking Ollama processes:"
ps aux | grep ollama | grep -v grep
echo ""

echo "2. Checking port 11434:"
lsof -i :11434
echo ""

echo "3. Testing API:"
curl -v http://localhost:11434/api/tags 2>&1 | head -20
echo ""

echo "4. Checking Ollama version:"
ollama --version
echo ""

echo "5. Checking models:"
ollama list
echo ""

echo "6. Testing direct model access:"
ollama run qwen2.5:32b-instruct "say hello" 2>&1 | head -5
```

**Run it:**
```bash
chmod +x diagnose_ollama.sh
./diagnose_ollama.sh
```

## Nuclear Option: Complete Reset

**If absolutely nothing works:**

```bash
# 1. Stop everything
pkill -9 ollama
osascript -e 'quit app "Ollama"'

# 2. Remove Ollama.app
rm -rf /Applications/Ollama.app

# 3. Remove Launch Agents
rm -f ~/Library/LaunchAgents/*ollama*

# 4. Reinstall
brew install ollama

# 5. Start fresh
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

## Check Ollama Configuration

**Check Ollama config file:**
```bash
# Check if config exists
ls -la ~/.ollama/

# Check environment
env | grep OLLAMA
```

## Test Different Port

**If port 11434 is problematic, try different port:**

```bash
# Start on different port
OLLAMA_HOST=0.0.0.0:11435 ollama serve
```

**Then test:**
```bash
curl http://localhost:11435/api/tags
```

**Update tunnel:**
```bash
# From laptop
ssh -f -N -L 11436:localhost:11435 thrivestudio@192.168.50.29
```

