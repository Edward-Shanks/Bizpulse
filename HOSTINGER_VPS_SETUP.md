# Hostinger VPS Setup - Connect to Mac Studio Ollama

## Your Current Setup

- ✅ **Backend**: Deployed on Hostinger VPS
- ✅ **Frontend**: Deployed on Hostinger VPS
- ✅ **Mac Studio**: Running Ollama locally

## What You Need to Do

### Step 1: Set Up VPN Connection (Tailscale - Recommended)

**On Mac Studio:**
```bash
# Install Tailscale
brew install tailscale
sudo tailscale up
# Sign in via browser
tailscale ip -4
# Note the IP (e.g., 100.64.1.2)
```

**On Hostinger VPS (via SSH):**
```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
# Sign in via browser (same account as Mac Studio)
```

**Test Connection:**
```bash
# On Hostinger VPS
tailscale status  # Should see Mac Studio
curl http://100.64.1.2:11434/api/tags  # Replace with Mac Studio IP
```

### Step 2: Configure Mac Studio Ollama

**On Mac Studio:**
```bash
# Make Ollama accessible via VPN
export OLLAMA_HOST=0.0.0.0:11434
echo 'OLLAMA_HOST=0.0.0.0:11434' | sudo tee -a /etc/environment

# Restart Ollama
pkill ollama
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

### Step 3: Update Backend Configuration on Hostinger

**On Hostinger VPS, edit your backend `.env` file:**

```bash
# SSH to Hostinger VPS
ssh your-user@your-hostinger-ip

# Navigate to backend directory
cd /path/to/your/backend

# Edit .env file
nano .env
```

**Add/Update these lines:**
```bash
# LLM Configuration
LLM_PROVIDER=ollama

# Use Mac Studio Tailscale IP
OLLAMA_BASE_URL=http://100.64.1.2:11434
# Replace 100.64.1.2 with your actual Mac Studio Tailscale IP

OLLAMA_MODEL=qwen2.5:32b-instruct
OLLAMA_FALLBACK_MODEL=llama3:70b
OLLAMA_TIMEOUT=120

# Keep Perplexity as fallback
PERPLEXITY_API_KEY=your-perplexity-key
```

### Step 4: Test Connection

**On Hostinger VPS:**
```bash
# Test Ollama connection
curl http://100.64.1.2:11434/api/tags

# Should return models list
```

### Step 5: Restart Backend

**On Hostinger VPS:**
```bash
# If using PM2
pm2 restart your-backend-name

# OR if using systemd
sudo systemctl restart your-backend-service

# OR if using screen/tmux
# Just restart your uvicorn process
```

### Step 6: Verify It's Working

**Test the chat endpoint:**
```bash
curl -X POST https://your-domain.com/api/insights/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "What is the revenue for Food business?",
    "context": {}
  }'
```

**Check backend logs:**
```bash
# On Hostinger VPS
pm2 logs your-backend-name
# OR
tail -f /path/to/logs/app.log
```

**You should see:**
```
🤖 USING LLM PROVIDER: OLLAMA
🦙 OLLAMA: Starting generation request
```

---

## Alternative: SSH Tunnel (If Tailscale Doesn't Work)

**On Hostinger VPS, create persistent SSH tunnel:**

```bash
# Install autossh
sudo apt install autossh -y

# Create systemd service
sudo nano /etc/systemd/system/ollama-tunnel.service
```

**Add this content:**
```ini
[Unit]
Description=SSH Tunnel to Mac Studio Ollama
After=network.target

[Service]
Type=simple
User=your-user
ExecStart=/usr/bin/autossh -M 0 -o "ServerAliveInterval 30" -o "ServerAliveCountMax 3" -N -L 11434:localhost:11434 thrivestudio@YOUR_MAC_STUDIO_PUBLIC_IP
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable ollama-tunnel
sudo systemctl start ollama-tunnel
sudo systemctl status ollama-tunnel
```

**Update `.env`:**
```bash
OLLAMA_BASE_URL=http://localhost:11434
```

---

## Hostinger-Specific Notes

### If Using Hostinger Control Panel:

1. **Access via SSH:**
   - Use Hostinger's SSH access from control panel
   - Or use terminal: `ssh user@your-vps-ip`

2. **File Management:**
   - Use Hostinger File Manager OR
   - Use SFTP (FileZilla, WinSCP) OR
   - Use Git to pull updates

3. **Environment Variables:**
   - Edit `.env` file in backend directory
   - Or set via Hostinger control panel if available

### Common Hostinger VPS Paths:

```bash
# Backend might be at:
/home/your-user/backend
/var/www/backend
/opt/backend

# Find your backend:
find / -name "main.py" -type f 2>/dev/null | grep backend
```

---

## Quick Checklist

- [ ] Install Tailscale on Mac Studio
- [ ] Install Tailscale on Hostinger VPS
- [ ] Get Mac Studio Tailscale IP
- [ ] Configure Mac Studio Ollama (OLLAMA_HOST=0.0.0.0:11434)
- [ ] Test connection from Hostinger: `curl http://MAC_STUDIO_IP:11434/api/tags`
- [ ] Update Hostinger backend `.env` with Mac Studio IP
- [ ] Restart backend on Hostinger
- [ ] Test chat endpoint
- [ ] Verify logs show Ollama usage

---

## Troubleshooting

### Can't Connect to Mac Studio?

```bash
# On Hostinger VPS
# Check Tailscale status
tailscale status

# Test ping
ping 100.64.1.2  # Mac Studio IP

# Test Ollama
curl -v http://100.64.1.2:11434/api/tags
```

### Backend Still Using Perplexity?

```bash
# Check .env file
cat .env | grep LLM_PROVIDER

# Should show: LLM_PROVIDER=ollama

# Restart backend
pm2 restart your-backend-name
```

### Ollama Not Responding?

```bash
# On Mac Studio
# Check if Ollama is running
ps aux | grep ollama

# Check if listening on all interfaces
lsof -i :11434

# Restart Ollama
pkill ollama
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

---

## Summary

**Changes Needed on Hostinger VPS:**
1. ✅ Install Tailscale (or set up SSH tunnel)
2. ✅ Update `.env` file: `OLLAMA_BASE_URL=http://MAC_STUDIO_TAILSCALE_IP:11434`
3. ✅ Set: `LLM_PROVIDER=ollama`
4. ✅ Restart backend

**That's it!** Your chatbot will now use Mac Studio Ollama from anywhere in the world! 🌍

