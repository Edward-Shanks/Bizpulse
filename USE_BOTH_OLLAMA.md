# Use Both Ollama Instances (Laptop + Mac Studio)

## Your Setup
- ✅ **Laptop Ollama**: Running on port 11434 (keep it running)
- ✅ **Mac Studio Ollama**: Running on port 11434 (via SSH tunnel on port 11435)

## Solution: Use Different Ports

### Step 1: Create SSH Tunnel on Port 11435

**On your laptop, run:**
```bash
ssh -f -N -L 11435:localhost:11434 rivemain@192.178.90.31
```

**This creates:**
- Laptop port 11435 → Mac Studio port 11434
- Your laptop's Ollama stays on port 11434 (no conflict!)

### Step 2: Test Both Connections

**Test laptop Ollama:**
```bash
curl http://localhost:11434/api/tags
```

**Test Mac Studio Ollama:**
```bash
curl http://localhost:11435/api/tags
```

Both should work! 🎉

### Step 3: Configure Your Backend

**Update `backend/.env`:**
```bash
# LLM Provider
LLM_PROVIDER=ollama

# Ollama Configuration (Mac Studio via SSH tunnel on port 11435)
OLLAMA_BASE_URL=http://localhost:11435
OLLAMA_MODEL=qwen2.5:32b-instruct
OLLAMA_FALLBACK_MODEL=llama3:70b
OLLAMA_TIMEOUT=120
```

## Architecture

```
Your Laptop
├── Ollama (Port 11434) ← Keep running
└── SSH Tunnel (Port 11435) → Mac Studio Ollama (Port 11434)
```

## Benefits

✅ **No conflicts**: Different ports  
✅ **Flexibility**: Can use either Ollama  
✅ **No changes needed**: Laptop Ollama keeps running  
✅ **Easy switching**: Just change `OLLAMA_BASE_URL` in `.env`  

## Quick Commands

**Start Mac Studio tunnel:**
```bash
ssh -f -N -L 11435:localhost:11434 rivemain@192.178.90.31
```

**Test Mac Studio:**
```bash
curl http://localhost:11435/api/tags
```

**Stop tunnel (if needed):**
```bash
# Find SSH process
netstat -ano | findstr :11435

# Kill it (replace PID)
taskkill /PID <PID> /F
```

## Switching Between Ollama Instances

**Use Mac Studio (512GB RAM - recommended):**
```bash
OLLAMA_BASE_URL=http://localhost:11435
```

**Use Laptop (if needed for testing):**
```bash
OLLAMA_BASE_URL=http://localhost:11434
```

Just update `.env` and restart your backend!

