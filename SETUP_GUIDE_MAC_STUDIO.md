# Complete Setup Guide: Mac Studio Ollama Integration

## Overview

This guide walks you through setting up your laptop to use Ollama running on Mac Studio (`192.178.90.31`) via SSH tunnel.

---

## Prerequisites

✅ Mac Studio has Ollama installed and running  
✅ You can SSH to Mac Studio: `ssh rivemain@192.178.90.31`  
✅ Models are downloaded (qwen2.5:32b-instruct, llama3:70b, etc.)  
✅ Ollama is accessible on Mac Studio at port 11434  

---

## Step-by-Step Setup

### Step 1: Create SSH Tunnel

**On your laptop, open terminal and run:**

```bash
# Create SSH tunnel in background
ssh -f -N -L 11434:localhost:11434 rivemain@192.178.90.31
```

**Verify tunnel is active:**
```bash
lsof -i :11434
```

**You should see:**
```
COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
ssh     12345 user    3u  IPv4  ...      0t0  TCP localhost:11434 (LISTEN)
```

**OR use the tunnel script:**
```bash
chmod +x scripts/ollama_tunnel.sh
./scripts/ollama_tunnel.sh start
```

### Step 2: Test Connection

**Test from your laptop:**
```bash
curl http://localhost:11434/api/tags
```

**Expected output:**
```json
{
  "models": [
    {
      "name": "qwen2.5:32b-instruct",
      "modified_at": "2025-12-21T...",
      "size": 19000000000
    },
    ...
  ]
}
```

**OR run the test script:**
```bash
python scripts/test_ollama_connection.py
```

### Step 3: Configure Environment

**Create/Update `.env` file in `backend/` directory:**

```bash
# LLM Provider Selection
# Change this to switch between providers
LLM_PROVIDER=ollama

# Ollama Configuration (Mac Studio via SSH tunnel)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:32b-instruct
OLLAMA_FALLBACK_MODEL=llama3:70b
OLLAMA_TIMEOUT=120

# Perplexity (keep for fallback)
PERPLEXITY_API_KEY=your_key_here
```

### Step 4: Install Dependencies

```bash
cd backend
pip install httpx
```

### Step 5: Verify Files Are Created

**Check these files exist:**
```bash
ls backend/app/utils/llm_providers/
# Should show:
# __init__.py
# base.py
# perplexity.py
# ollama.py
# factory.py
```

### Step 6: Start Backend

```bash
cd backend
uvicorn app.main:app --reload
```

### Step 7: Test API

**Test the chat endpoint:**
```bash
curl -X POST http://localhost:8000/api/insights/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the revenue for Food business?",
    "context": {}
  }'
```

**Check logs to see which provider is used:**
```bash
# Look for this in logs:
# "LLM Provider initialized: ollama"
# "LLM response generated using provider: ollama"
```

---

## Architecture Explanation

### How It Works

```
Your Laptop (Development)
    ↓
SSH Tunnel (localhost:11434 → Mac Studio:11434)
    ↓
Mac Studio Ollama (Port 11434)
    ↓
Model Inference (qwen2.5:32b-instruct)
    ↓
Response → Your Laptop → Backend → Frontend
```

### Provider Switching

**Current Flow:**
```
InsightsService.process_chat()
    ↓
query_perplexity() [backward compatible function]
    ↓
query_llm() [unified interface]
    ↓
LLMProviderFactory.get_provider()
    ↓
OllamaProvider (or PerplexityProvider)
    ↓
Mac Studio Ollama API
```

**To Switch Providers:**
- Change `LLM_PROVIDER=ollama` to `LLM_PROVIDER=perplexity` in `.env`
- Restart FastAPI server
- No code changes needed!

---

## Daily Workflow

### Morning: Start SSH Tunnel

```bash
./scripts/ollama_tunnel.sh start
```

### During Development

Your backend automatically uses Ollama (if `LLM_PROVIDER=ollama`)

### Evening: Stop Tunnel (Optional)

```bash
./scripts/ollama_tunnel.sh stop
```

---

## Troubleshooting

### Problem: "Connection refused"

**Solution:**
1. Check tunnel: `./scripts/ollama_tunnel.sh status`
2. If not active: `./scripts/ollama_tunnel.sh start`
3. Test: `curl http://localhost:11434/api/tags`

### Problem: "Model not found"

**Solution:**
1. Check available models on Mac Studio:
   ```bash
   ssh rivemain@192.178.90.31 "ollama list"
   ```
2. Update `OLLAMA_MODEL` in `.env` to match available model
3. Your models: `qwen2.5:32b-instruct`, `llama3:70b`, `mistral:7b`, etc.

### Problem: Slow first request

**Solution:**
- This is normal! First request loads the model into memory
- Subsequent requests will be faster
- Model stays loaded for ~5 minutes (Ollama default)

### Problem: SSH tunnel disconnects

**Solution:**
1. Use background tunnel: `ssh -f -N -L 11434:localhost:11434 rivemain@192.178.90.31`
2. Or use script: `./scripts/ollama_tunnel.sh start`
3. Add auto-reconnect script if needed

---

## Advanced: Direct Network Access (No SSH Tunnel)

**If you want to access Mac Studio directly (not recommended for security):**

1. **On Mac Studio, configure Ollama to accept remote connections:**
```bash
# Set environment variable
export OLLAMA_HOST=0.0.0.0:11434

# Restart Ollama
# (If using Launchd, update the service file)
```

2. **Configure firewall:**
```bash
# Allow port 11434
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /Applications/Ollama.app
```

3. **Update `.env` on laptop:**
```bash
OLLAMA_BASE_URL=http://192.178.90.31:11434
```

4. **Test:**
```bash
curl http://192.178.90.31:11434/api/tags
```

**⚠️ Security Note**: Direct network access exposes Ollama to your network. Use SSH tunnel for better security.

---

## Verification Checklist

- [ ] SSH tunnel is active (`lsof -i :11434`)
- [ ] Test connection works (`curl http://localhost:11434/api/tags`)
- [ ] Environment variables configured (`.env` file)
- [ ] Provider files created (`backend/app/utils/llm_providers/`)
- [ ] Dependencies installed (`pip install httpx`)
- [ ] Backend starts without errors
- [ ] API endpoint responds
- [ ] Logs show "LLM Provider initialized: ollama"

---

## Next Steps

1. ✅ Complete setup
2. ✅ Test with a simple query
3. ✅ Monitor response times
4. ✅ Compare quality with Perplexity
5. ✅ Optimize if needed

**You're ready to use local LLM!** 🚀

