# Quick VPN Setup Guide - Tailscale (Recommended)

## Why Tailscale?

✅ **Easiest setup** - 5 minutes  
✅ **Free for personal use** (up to 100 devices)  
✅ **Automatic firewall** - Secure by default  
✅ **No port forwarding** - Works behind NAT  
✅ **Cross-platform** - Works on Mac, Linux, Windows  

---

## Step 1: Install Tailscale on Mac Studio

**On Mac Studio terminal:**

```bash
# Install Tailscale
brew install tailscale

# Start Tailscale
sudo tailscale up

# You'll see a URL - open it in browser and sign in
# After signing in, note your Tailscale IP:
tailscale ip -4
# Example: 100.64.1.2
```

**Save this IP!** (e.g., `100.64.1.2`)

---

## Step 2: Install Tailscale on Cloud Server

**On your cloud server (Ubuntu):**

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Start Tailscale
sudo tailscale up

# You'll see a URL - open it in browser and sign in
# After signing in, verify connection:
tailscale status
```

**You should see both Mac Studio and Cloud Server listed!**

---

## Step 3: Test Connection

**On Cloud Server:**

```bash
# Get Mac Studio Tailscale IP
tailscale status | grep "Mac Studio"
# Example: 100.64.1.2

# Test connection
ping 100.64.1.2

# Test Ollama
curl http://100.64.1.2:11434/api/tags
```

**If this works, VPN is set up!** ✅

---

## Step 4: Update Backend Config

**On Cloud Server, edit `.env`:**

```bash
# Use Mac Studio Tailscale IP
OLLAMA_BASE_URL=http://100.64.1.2:11434
LLM_PROVIDER=ollama
```

**Replace `100.64.1.2` with your actual Mac Studio Tailscale IP!**

---

## Step 5: Test Backend

**On Cloud Server:**

```bash
# Test Ollama connection
curl http://100.64.1.2:11434/api/tags

# Start backend
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8000" --name bizpulse-api

# Test backend
curl http://localhost:8000/health
```

---

## That's It! 🎉

**Your setup:**
- ✅ Mac Studio: Ollama running, accessible via Tailscale
- ✅ Cloud Server: Backend running, connected to Mac Studio via Tailscale
- ✅ Global Access: Backend accessible from anywhere via domain

**Next:** Follow `MAC_STUDIO_VPN_DEPLOYMENT.md` for complete deployment!

---

## Troubleshooting

### Can't see Mac Studio from Cloud Server?

```bash
# On Mac Studio, check Tailscale
tailscale status

# On Cloud Server, check Tailscale
tailscale status

# Both should be in same network
```

### Ollama not responding?

```bash
# On Mac Studio
# Make sure Ollama is listening on all interfaces
OLLAMA_HOST=0.0.0.0:11434 ollama serve

# Test locally first
curl http://localhost:11434/api/tags
```

### Connection timeout?

```bash
# Check firewall on Mac Studio
# Tailscale handles this automatically, but verify:
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --listapps | grep Ollama
```

---

**Tailscale is the easiest way to set up VPN!** 🚀

