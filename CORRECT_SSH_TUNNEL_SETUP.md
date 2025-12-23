# Correct SSH Tunnel Setup

## The Problem

You're trying to create the SSH tunnel **from Mac Studio** to your laptop, but it should be **from your laptop** to Mac Studio.

## Correct Setup

### On Mac Studio (Terminal 1)
✅ **Keep Ollama running:**
```bash
ollama serve
```
**This is correct - leave this running!**

### On Your Laptop (Windows Terminal)
✅ **Create SSH tunnel FROM laptop TO Mac Studio:**

```bash
ssh -L 11434:localhost:11434 rivemain@192.178.90.31
```

**OR if you want it in background:**
```bash
ssh -f -N -L 11434:localhost:11434 rivemain@192.178.90.31
```

**Important Notes:**
- Run this command **on your laptop**, NOT on Mac Studio
- Replace `192.178.90.31` with your actual Mac Studio IP (check with `ifconfig` on Mac Studio)
- The command forwards: `laptop:11434` → `Mac Studio:11434`

## Verify Setup

### On Your Laptop:
```bash
# Test if tunnel is working
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

## Architecture Flow

```
Your Laptop (Windows)
    ↓
SSH Tunnel (localhost:11434)
    ↓
Mac Studio (192.178.90.31:11434)
    ↓
Ollama Server (Port 11434)
    ↓
Model Inference
```

## Troubleshooting

### If you get "Connection refused":
1. Make sure Ollama is running on Mac Studio (Terminal 1)
2. Make sure SSH tunnel is created from laptop (not Mac Studio)
3. Check Mac Studio IP address is correct

### If you get "Address already in use" on laptop:
```bash
# Check what's using port 11434 on laptop
netstat -ano | findstr :11434

# Kill the process if needed (Windows)
taskkill /PID <PID> /F
```

### To find Mac Studio IP:
**On Mac Studio, run:**
```bash
ifconfig | grep "inet "
```

Look for the IP address (usually starts with 192.168.x.x or 10.x.x.x)

