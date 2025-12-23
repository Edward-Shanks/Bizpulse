# ✅ SSH Tunnel is Working!

## Current Setup

- **SSH Tunnel**: `localhost:11436` → `Mac Studio:127.0.0.1:11434`
- **Status**: ✅ Working (confirmed via Postman)
- **Models Available**: qwen2.5:32b-instruct, llama3:70b, and 13 others

## Next Steps

### Step 1: Keep SSH Tunnel Running

**Important:** Keep the terminal with SSH tunnel open!

The tunnel command you're using:
```bash
ssh -N -L 11436:127.0.0.1:11434 thrivestudio@192.168.50.29
```

**To run in background (so you can close terminal):**
```bash
ssh -f -N -L 11436:127.0.0.1:11434 thrivestudio@192.168.50.29
```

### Step 2: Update Your .env File

**Edit `backend/.env` and update:**
```bash
# LLM Provider
LLM_PROVIDER=ollama

# Ollama Configuration (Mac Studio via SSH tunnel on port 11436)
OLLAMA_BASE_URL=http://localhost:11436
OLLAMA_MODEL=qwen2.5:32b-instruct
OLLAMA_FALLBACK_MODEL=llama3:70b
OLLAMA_TIMEOUT=120
```

### Step 3: Test from Backend

**On your laptop, test the connection:**
```bash
# Test API endpoint
curl http://localhost:11436/api/tags

# Test model generation
curl -X POST http://localhost:11436/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:32b-instruct",
    "messages": [{"role": "user", "content": "Say hello"}],
    "stream": false
  }'
```

### Step 4: Start Your Backend

**On your laptop:**
```bash
cd backend
uvicorn app.main:app --reload
```

**Test the chat endpoint:**
```bash
curl -X POST http://localhost:8000/api/insights/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the revenue for Food business?",
    "context": {}
  }'
```

## Daily Workflow

### Every Morning:

1. **Start SSH tunnel:**
   ```bash
   ssh -f -N -L 11436:127.0.0.1:11434 thrivestudio@192.168.50.29
   ```

2. **Test tunnel:**
   ```bash
   curl http://localhost:11436/api/tags
   ```

3. **Start backend:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

### Every Evening (Optional):

**Stop SSH tunnel:**
```bash
# Find SSH process
netstat -ano | findstr :11436

# Kill it (replace PID)
taskkill /PID <PID> /F
```

## Quick Reference

**SSH Tunnel Command:**
```bash
ssh -f -N -L 11436:127.0.0.1:11434 thrivestudio@192.168.50.29
```

**Test Tunnel:**
```bash
curl http://localhost:11436/api/tags
```

**Backend Config:**
```bash
OLLAMA_BASE_URL=http://localhost:11436
```

## Troubleshooting

### Issue: Tunnel stops working

**Solution:**
1. Check if tunnel is still running: `netstat -ano | findstr :11436`
2. Recreate tunnel: `ssh -f -N -L 11436:127.0.0.1:11434 thrivestudio@192.168.50.29`

### Issue: Backend can't connect

**Solution:**
1. Verify tunnel: `curl http://localhost:11436/api/tags`
2. Check `.env` has correct port: `OLLAMA_BASE_URL=http://localhost:11436`
3. Restart backend

## Summary

✅ **SSH Tunnel**: Working on port 11436  
✅ **Ollama API**: Accessible from laptop  
✅ **Models**: 14 models available  
✅ **Next**: Update `.env` and test backend  

**You're all set!** 🎉

