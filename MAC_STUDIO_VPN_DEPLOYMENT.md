# Complete Guide: Deploy Backend on Cloud, Keep Ollama on Mac Studio (VPN Access)

## Architecture Overview

```
Internet (Global Access)
    ↓
[Cloud Server - Backend API]
    ↓ (VPN Connection)
[Mac Studio - Ollama LLM]
    ↓
[MongoDB] (Cloud or Local)
```

**What's on Cloud Server:**
- ✅ Backend API (FastAPI)
- ✅ Frontend (React) - Optional
- ✅ Nginx (Reverse Proxy)
- ✅ SSL Certificate

**What's on Mac Studio:**
- ✅ Ollama (Local LLM)
- ✅ Models (qwen2.5:32b-instruct, etc.)

**Connection:**
- ✅ VPN tunnel between Cloud Server ↔ Mac Studio

---

## Step-by-Step Deployment

### Phase 1: Set Up VPN Server on Mac Studio

#### Option A: Use Tailscale (Easiest - Recommended)

**1. Install Tailscale on Mac Studio:**

```bash
# On Mac Studio
brew install tailscale

# Start Tailscale
sudo tailscale up

# Get your Tailscale IP
tailscale ip -4
# Note this IP (e.g., 100.x.x.x)
```

**2. Install Tailscale on Cloud Server:**

```bash
# On Cloud Server (Ubuntu)
curl -fsSL https://tailscale.com/install.sh | sh

# Start Tailscale
sudo tailscale up

# Verify connection
tailscale status
```

**3. Test Connection:**

```bash
# From Cloud Server, test Mac Studio
ping 100.x.x.x  # (Mac Studio Tailscale IP)

# Test Ollama
curl http://100.x.x.x:11434/api/tags
```

#### Option B: Use WireGuard (More Control)

**1. Install WireGuard on Mac Studio:**

```bash
# On Mac Studio
brew install wireguard-tools

# Generate keys
wg genkey | tee privatekey | wg pubkey > publickey
```

**2. Configure WireGuard Server (Mac Studio):**

```bash
# Create config file
sudo nano /usr/local/etc/wireguard/wg0.conf

# Add:
[Interface]
PrivateKey = YOUR_PRIVATE_KEY
Address = 10.0.0.1/24
ListenPort = 51820

[Peer]
PublicKey = CLOUD_SERVER_PUBLIC_KEY
AllowedIPs = 10.0.0.2/32
```

**3. Start WireGuard:**

```bash
sudo wg-quick up wg0
```

**4. Configure WireGuard Client (Cloud Server):**

```bash
# Install WireGuard
sudo apt install wireguard -y

# Create config
sudo nano /etc/wireguard/wg0.conf

# Add:
[Interface]
PrivateKey = CLOUD_SERVER_PRIVATE_KEY
Address = 10.0.0.2/24

[Peer]
PublicKey = MAC_STUDIO_PUBLIC_KEY
Endpoint = YOUR_MAC_STUDIO_PUBLIC_IP:51820
AllowedIPs = 10.0.0.1/32
PersistentKeepalive = 25
```

**5. Start WireGuard:**

```bash
sudo wg-quick up wg0
```

#### Option C: Use SSH Tunnel (Simplest, but Less Secure)

**On Cloud Server, create persistent SSH tunnel:**

```bash
# Install autossh for auto-reconnect
sudo apt install autossh -y

# Create systemd service
sudo nano /etc/systemd/system/ollama-tunnel.service

# Add:
[Unit]
Description=SSH Tunnel to Mac Studio Ollama
After=network.target

[Service]
Type=simple
User=ubuntu
ExecStart=/usr/bin/autossh -M 0 -o "ServerAliveInterval 30" -o "ServerAliveCountMax 3" -N -L 11434:localhost:11434 thrivestudio@YOUR_MAC_STUDIO_PUBLIC_IP
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable ollama-tunnel
sudo systemctl start ollama-tunnel
```

---

### Phase 2: Configure Mac Studio for Remote Access

**1. Configure Ollama to Accept VPN Connections:**

```bash
# On Mac Studio
export OLLAMA_HOST=0.0.0.0:11434

# Make permanent
echo 'OLLAMA_HOST=0.0.0.0:11434' | sudo tee -a /etc/environment

# Restart Ollama
pkill ollama
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

**2. Configure Firewall (Allow VPN Access Only):**

```bash
# On Mac Studio
# Allow Ollama from VPN network only
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /Applications/Ollama.app
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /Applications/Ollama.app

# If using Tailscale, it handles firewall automatically
# If using WireGuard, allow port 11434 from VPN subnet only
```

**3. Test Ollama from VPN:**

```bash
# From Cloud Server (via VPN)
curl http://MAC_STUDIO_VPN_IP:11434/api/tags
```

---

### Phase 3: Deploy Backend to Cloud Server

**1. Launch Cloud Server:**

**Recommended:**
- **Provider**: AWS EC2, DigitalOcean, Linode, Vultr
- **Instance**: 2 CPU, 4GB RAM (no GPU needed - Ollama is on Mac Studio)
- **OS**: Ubuntu 22.04 LTS
- **Cost**: ~$10-20/month

**2. Connect to Server:**

```bash
ssh -i your-key.pem ubuntu@your-server-ip
```

**3. Install Dependencies:**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3.10 python3-pip python3-venv -y

# Install Nginx
sudo apt install nginx -y

# Install PM2 (Process Manager)
npm install -g pm2

# Install Git
sudo apt install git -y
```

**4. Set Up VPN Connection:**

**If using Tailscale:**
```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Get Mac Studio IP
tailscale status | grep "Mac Studio"
# Note the IP (e.g., 100.x.x.x)
```

**If using WireGuard:**
```bash
# Follow WireGuard setup from Phase 1
sudo wg-quick up wg0

# Test connection
ping 10.0.0.1  # Mac Studio VPN IP
```

**5. Clone and Set Up Backend:**

```bash
# Clone repository
git clone https://github.com/your-repo/bizpulse.git
cd bizpulse/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**6. Configure Environment Variables:**

```bash
# Create .env file
nano .env

# Add:
MONGO_URL=your-mongodb-connection-string
DB_NAME=bizpulse
JWT_SECRET=your-secret-key

# LLM Configuration (via VPN)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://MAC_STUDIO_VPN_IP:11434
# For Tailscale: http://100.x.x.x:11434
# For WireGuard: http://10.0.0.1:11434

OLLAMA_MODEL=qwen2.5:32b-instruct
OLLAMA_FALLBACK_MODEL=llama3:70b
OLLAMA_TIMEOUT=120

# Perplexity (fallback)
PERPLEXITY_API_KEY=your-perplexity-key

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Environment
ENVIRONMENT=production
```

**7. Test Connection to Mac Studio:**

```bash
# Test Ollama via VPN
curl http://MAC_STUDIO_VPN_IP:11434/api/tags

# Should return models list
```

**8. Start Backend:**

```bash
# Test run first
uvicorn app.main:app --host 0.0.0.0 --port 8000

# If working, start with PM2
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8000" --name bizpulse-api

# Save PM2 config
pm2 save
pm2 startup
```

---

### Phase 4: Set Up Nginx Reverse Proxy

**1. Create Nginx Configuration:**

```bash
sudo nano /etc/nginx/sites-available/bizpulse
```

**2. Add Configuration:**

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    # Increase timeouts for LLM requests
    proxy_read_timeout 300s;
    proxy_connect_timeout 75s;
    proxy_send_timeout 300s;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**3. Enable Site:**

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/bizpulse /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

### Phase 5: Set Up SSL Certificate

**1. Install Certbot:**

```bash
sudo apt install certbot python3-certbot-nginx -y
```

**2. Get SSL Certificate:**

```bash
sudo certbot --nginx -d api.yourdomain.com
```

**3. Auto-Renewal:**

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot auto-renews, but verify:
sudo systemctl status certbot.timer
```

---

### Phase 6: Configure Domain DNS

**1. Point Domain to Server:**

**In your domain registrar (GoDaddy, Namecheap, etc.):**

```
Type: A
Name: api
Value: YOUR_SERVER_IP
TTL: 3600
```

**2. Verify DNS:**

```bash
# Check DNS propagation
dig api.yourdomain.com

# Should return your server IP
```

---

### Phase 7: Deploy Frontend (Optional)

**Option A: Same Server**

```bash
# Build frontend
cd frontend
npm install
npm run build

# Serve with Nginx
sudo nano /etc/nginx/sites-available/bizpulse-frontend

# Add:
server {
    listen 80;
    server_name yourdomain.com;

    root /path/to/frontend/build;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Option B: Separate Server/CDN**

- Deploy to Vercel, Netlify, or AWS S3
- Update API URL in frontend config

---

### Phase 8: Security Hardening

**1. Firewall Configuration:**

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

**2. SSH Security:**

```bash
# Disable password auth (use keys only)
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart sshd
```

**3. Fail2Ban:**

```bash
# Install fail2ban
sudo apt install fail2ban -y

# Enable
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

**4. VPN Security:**

**For Tailscale:**
- Use access controls in Tailscale admin panel
- Restrict Mac Studio access to cloud server only

**For WireGuard:**
- Use strong keys
- Rotate keys periodically
- Monitor connection logs

---

### Phase 9: Monitoring & Maintenance

**1. Set Up Monitoring:**

```bash
# Install monitoring tools
sudo apt install htop iotop -y

# Monitor backend
pm2 monit

# Monitor VPN connection
# Tailscale: tailscale status
# WireGuard: sudo wg show
```

**2. Set Up Logging:**

```bash
# Backend logs
pm2 logs bizpulse-api

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -u ollama-tunnel -f  # If using SSH tunnel
```

**3. Auto-Restart on Failure:**

```bash
# PM2 auto-restart (already configured)
pm2 startup
pm2 save

# VPN auto-reconnect (if using SSH tunnel)
# Systemd service already has Restart=always
```

---

## Testing Global Access

### 1. Test from Different Locations

**From your laptop:**
```bash
curl https://api.yourdomain.com/health
```

**From different network:**
- Use mobile hotspot
- Test from different country (use VPN)
- Verify chatbot works

### 2. Test Ollama Connection

```bash
# From cloud server
curl http://MAC_STUDIO_VPN_IP:11434/api/tags

# Should return models
```

### 3. Test Chat Endpoint

```bash
curl -X POST https://api.yourdomain.com/api/insights/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "What is the revenue for Food business?",
    "context": {}
  }'
```

---

## Troubleshooting

### Issue: Can't Connect to Mac Studio via VPN

**Solution:**
```bash
# Check VPN status
# Tailscale:
tailscale status

# WireGuard:
sudo wg show

# Test connection
ping MAC_STUDIO_VPN_IP

# Check firewall
sudo ufw status
```

### Issue: Ollama Not Responding

**Solution:**
```bash
# On Mac Studio, check Ollama
ps aux | grep ollama

# Check if listening on correct interface
lsof -i :11434

# Restart Ollama
pkill ollama
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

### Issue: Backend Can't Reach Ollama

**Solution:**
```bash
# On cloud server, test connection
curl http://MAC_STUDIO_VPN_IP:11434/api/tags

# Check backend logs
pm2 logs bizpulse-api

# Check VPN connection
tailscale status  # or sudo wg show
```

### Issue: SSL Certificate Issues

**Solution:**
```bash
# Renew certificate
sudo certbot renew

# Check certificate
sudo certbot certificates

# Test Nginx config
sudo nginx -t
```

---

## Cost Breakdown

### Monthly Costs:

| Service | Cost |
|---------|------|
| Cloud Server (2 CPU, 4GB) | $10-20 |
| Domain Name | $10-15/year (~$1/month) |
| SSL Certificate | Free (Let's Encrypt) |
| Tailscale (up to 100 devices) | Free |
| WireGuard | Free |
| **Total** | **~$11-21/month** |

### One-Time Costs:

- Domain registration: $10-15/year
- Server setup time: 2-4 hours

---

## Quick Reference

### Mac Studio Commands:

```bash
# Start Ollama
OLLAMA_HOST=0.0.0.0:11434 ollama serve

# Check Tailscale IP
tailscale ip -4

# Test Ollama
curl http://localhost:11434/api/tags
```

### Cloud Server Commands:

```bash
# Check VPN connection
tailscale status  # or sudo wg show

# Test Ollama via VPN
curl http://MAC_STUDIO_VPN_IP:11434/api/tags

# Backend status
pm2 status
pm2 logs bizpulse-api

# Nginx status
sudo systemctl status nginx
```

### Environment Variables:

```bash
# On Cloud Server .env
OLLAMA_BASE_URL=http://MAC_STUDIO_VPN_IP:11434
LLM_PROVIDER=ollama
```

---

## Summary

✅ **Mac Studio**: Runs Ollama, accessible via VPN  
✅ **Cloud Server**: Runs backend API, accessible globally  
✅ **VPN**: Connects cloud server to Mac Studio  
✅ **Domain & SSL**: Global access with HTTPS  
✅ **Cost**: ~$11-21/month  

**Your chatbot is now accessible from anywhere in the world!** 🌍

---

## Next Steps

1. ✅ Set up VPN (Tailscale recommended)
2. ✅ Configure Mac Studio Ollama
3. ✅ Deploy backend to cloud server
4. ✅ Set up Nginx & SSL
5. ✅ Configure domain DNS
6. ✅ Test globally
7. ✅ Monitor and maintain

**Start with Phase 1 (VPN Setup)!** 🚀

