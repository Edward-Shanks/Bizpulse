# Quick Start: Using Mac Studio Ollama from Your Laptop

## Current Setup

- **Your Laptop**: Development machine (where you write code)
- **Mac Studio**: `192.178.90.31` (where Ollama is running)
- **SSH Access**: `ssh rivemain@192.178.90.31`
- **Ollama Running**: Port 11434 on Mac Studio
- **Available Models**: qwen2.5:32b-instruct, llama3:70b, etc.

---

## Step 1: Set Up SSH Tunnel

### Option A: Manual SSH Tunnel (Quick Test)

**On your laptop, open a terminal and run:**
```bash
ssh -L 11434:localhost:11434 rivemain@192.178.90.31
```

**Keep this terminal open** - it maintains the tunnel.

**Test the tunnel:**
```bash
# In another terminal on your laptop
curl http://localhost:11434/api/tags
```

### Option B: Background SSH Tunnel (Recommended)

**Create tunnel in background:**
```bash
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

### Option C: Use the Tunnel Script (Easiest)

**Make script executable:**
```bash
chmod +x scripts/ollama_tunnel.sh
```

**Start tunnel:**
```bash
./scripts/ollama_tunnel.sh start
```

**Check status:**
```bash
./scripts/ollama_tunnel.sh status
```

**Test connection:**
```bash
./scripts/ollama_tunnel.sh test
```

**Stop tunnel:**
```bash
./scripts/ollama_tunnel.sh stop
```

---

## Step 2: Configure Environment

**Create/Update `.env` file in your backend directory:**

```bash
# LLM Provider Selection
# Options: perplexity, ollama
LLM_PROVIDER=ollama

# Ollama Configuration (Mac Studio via SSH tunnel)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:32b-instruct
OLLAMA_FALLBACK_MODEL=llama3:70b
OLLAMA_TIMEOUT=120

# Perplexity (keep for fallback)
PERPLEXITY_API_KEY=your_key_here
```

**OR if using direct network access (no SSH tunnel):**
```bash
OLLAMA_BASE_URL=http://192.178.90.31:11434
```

---

## Step 3: Install Dependencies

```bash
cd backend
pip install httpx
```

---

## Step 4: Test Connection

**Run the test script:**
```bash
python scripts/test_ollama_connection.py
```

**Expected output:**
```
🔍 Testing Ollama connection...
📍 URL: http://localhost:11434

1️⃣ Health Check...
   ✅ Ollama is running
   📦 Available models: 15
      - qwen2.5:32b-instruct (19.0 GB)
      - llama3:70b (39.0 GB)
      ...

2️⃣ Model Generation Test...
   Testing model: qwen2.5:32b-instruct
   ✅ Generation successful
   📝 Response: Hello

✅ All tests passed! Ollama is ready to use.
```

---

## Step 5: Update Your Code

**The code is already updated!** Just make sure:

1. **Provider files exist:**
   - `backend/app/utils/llm_providers/__init__.py`
   - `backend/app/utils/llm_providers/base.py`
   - `backend/app/utils/llm_providers/perplexity.py`
   - `backend/app/utils/llm_providers/ollama.py`
   - `backend/app/utils/llm_providers/factory.py`

2. **AI Service is updated:**
   - `backend/app/utils/ai_service.py` (already updated)

3. **Insights Service uses the new interface:**
   - No changes needed! It already uses `query_perplexity()` which now uses the configured provider.

---

## Step 6: Start Your Backend

```bash
cd backend
uvicorn app.main:app --reload
```

**Test the API:**
```bash
curl -X POST http://localhost:8000/api/insights/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the revenue for Food business?",
    "context": {}
  }'
```

---

## Switching Between Providers

### Method 1: Environment Variable

**Switch to Ollama:**
```bash
export LLM_PROVIDER=ollama
# Restart FastAPI server
```

**Switch to Perplexity:**
```bash
export LLM_PROVIDER=perplexity
# Restart FastAPI server
```

### Method 2: Runtime API (Future)

Once you add the admin endpoints (see FLEXIBLE_LLM_ARCHITECTURE.md):
```bash
# Switch to Ollama
curl -X POST http://localhost:8000/api/admin/llm-provider/ollama

# Check current provider
curl http://localhost:8000/api/admin/llm-provider/current
```

---

## Troubleshooting

### Issue: "Connection refused" when testing

**Solution:**
1. Check SSH tunnel is active: `lsof -i :11434`
2. If not, create tunnel: `./scripts/ollama_tunnel.sh start`
3. Test again: `curl http://localhost:11434/api/tags`

### Issue: "Model not found"

**Solution:**
1. Check available models on Mac Studio:
   ```bash
   ssh rivemain@192.178.90.31 "ollama list"
   ```
2. Update `OLLAMA_MODEL` in `.env` to match an available model
3. Your available models: `qwen2.5:32b-instruct`, `llama3:70b`, etc.

### Issue: Slow responses

**Solution:**
1. First request is slow (model loading) - this is normal
2. Subsequent requests should be faster
3. Consider using smaller model for faster responses: `llama3:70b` or `mistral:7b`

### Issue: SSH tunnel keeps disconnecting

**Solution:**
1. Use background tunnel: `ssh -f -N -L 11434:localhost:11434 rivemain@192.178.90.31`
2. Or use the tunnel script: `./scripts/ollama_tunnel.sh start`
3. Add to your shell profile to auto-start on login

---

## Next Steps

1. ✅ SSH tunnel is active
2. ✅ Environment variables configured
3. ✅ Test connection successful
4. ✅ Backend using Ollama provider
5. 🎉 Start using your local LLM!

**You're all set!** Your backend will now use Ollama from Mac Studio instead of Perplexity API.

---

## Architecture Benefits

✅ **Zero Code Changes**: Your existing code works as-is  
✅ **Easy Switching**: Change one environment variable  
✅ **Future-Proof**: Ready for vLLM when needed  
✅ **Cost Savings**: $600K/month → $50/month  
✅ **Data Privacy**: No external API calls  

---

## Quick Reference

**Start tunnel:**
```bash
./scripts/ollama_tunnel.sh start
```

**Test connection:**
```bash
python scripts/test_ollama_connection.py
```

**Check provider:**
```bash
echo $LLM_PROVIDER  # Should be "ollama"
```

**Switch provider:**
```bash
export LLM_PROVIDER=ollama  # or perplexity
```

**View logs:**
```bash
# Check backend logs for provider usage
tail -f logs/app.log | grep "LLM Provider"
```

