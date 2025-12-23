# Global Deployment Guide - Mac Studio Ollama to Server

## Current Implementation Status

### ✅ What's Already Implemented

1. **LLM Provider System** ✅
   - Flexible provider architecture (Ollama, Perplexity, vLLM-ready)
   - Automatic fallback (Ollama → Perplexity)
   - Clear logging and debugging

2. **Ollama Integration** ✅
   - Ollama provider implementation
   - SSH tunnel support
   - Model configuration

3. **Error Handling** ✅
   - Automatic fallback
   - Debug endpoints
   - Status checking

### ❌ What's NOT Yet Implemented

1. **Vector Database (ChromaDB)** ❌
   - Only documented in roadmap
   - Not implemented in code yet

2. **Embedding Service** ❌
   - Only documented in roadmap
   - Not implemented in code yet

3. **Caching Layer** ❌
   - Only documented in roadmap
   - Not implemented in code yet

---

## Deployment Options

### Option 1: Keep Mac Studio + Expose via VPN/Reverse Proxy (Current Setup)

**Pros:**
- ✅ No changes needed
- ✅ Uses existing Mac Studio
- ✅ Cost-effective

**Cons:**
- ❌ Requires VPN for security
- ❌ Mac Studio must be always on
- ❌ Single point of failure

### Option 2: Deploy Ollama on Cloud Server (Recommended)

**Pros:**
- ✅ Accessible from anywhere
- ✅ Better reliability
- ✅ Scalable
- ✅ No VPN needed

**Cons:**
- ❌ Requires cloud server with GPU
- ❌ Higher cost than Mac Studio

### Option 3: Hybrid Approach (Best for Production)

**Pros:**
- ✅ Mac Studio for development
- ✅ Cloud server for production
- ✅ Easy switching

**Cons:**
- ❌ Need to manage both

---

## Deployment Strategy: Cloud Server

### Step 1: Choose Cloud Provider

**Recommended Options:**

#### Option A: AWS EC2 (GPU Instance)
- **Instance Type**: `g5.xlarge` or `g5.2xlarge` (NVIDIA A10G)
- **Cost**: ~$1-2/hour (~$720-1440/month)
- **RAM**: 16-32GB (can run smaller models)

#### Option B: Google Cloud Platform (GPU)
- **Instance Type**: `n1-standard-4` + `NVIDIA T4`
- **Cost**: ~$0.50-1/hour (~$360-720/month)
- **RAM**: 15GB + GPU memory

#### Option C: Azure (GPU)
- **Instance Type**: `NC6s_v3` (NVIDIA V100)
- **Cost**: ~$1.50/hour (~$1080/month)
- **RAM**: 112GB

#### Option D: RunPod / Vast.ai (Cheaper GPU Rental)
- **Cost**: ~$0.20-0.50/hour (~$144-360/month)
- **GPU**: Various (RTX 3090, A100, etc.)
- **Best for**: Cost-effective GPU access

### Step 2: Server Requirements

**Minimum:**
- **CPU**: 8+ cores
- **RAM**: 32GB+ (for 32B models)
- **GPU**: NVIDIA GPU with 16GB+ VRAM (for faster inference)
- **Storage**: 200GB+ (for models)
- **OS**: Ubuntu 22.04 LTS

**Recommended:**
- **CPU**: 16+ cores
- **RAM**: 64GB+ (for multiple models)
- **GPU**: NVIDIA A100 or RTX 4090 (24GB+ VRAM)
- **Storage**: 500GB+ SSD
- **OS**: Ubuntu 22.04 LTS

### Step 3: Install Ollama on Server

**On your cloud server:**

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull qwen2.5:32b-instruct
ollama pull llama3:70b
ollama pull mixtral:8x7b

# Start Ollama service
systemctl enable ollama
systemctl start ollama

# Configure to accept remote connections
export OLLAMA_HOST=0.0.0.0:11434
# Add to /etc/environment for persistence
echo 'OLLAMA_HOST=0.0.0.0:11434' >> /etc/environment
```

### Step 4: Configure Firewall

```bash
# Allow Ollama port
sudo ufw allow 11434/tcp

# Allow SSH
sudo ufw allow 22/tcp

# Allow your backend port (if deploying backend on same server)
sudo ufw allow 8000/tcp

# Enable firewall
sudo ufw enable
```

### Step 5: Update Backend Configuration

**On your laptop/backend server, update `.env`:**

```bash
# Use cloud server Ollama
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://your-server-ip:11434
# OR use domain
OLLAMA_BASE_URL=http://ollama.yourdomain.com:11434

OLLAMA_MODEL=qwen2.5:32b-instruct
OLLAMA_FALLBACK_MODEL=llama3:70b
OLLAMA_TIMEOUT=120
```

### Step 6: Deploy Backend to Cloud

**Option A: Same Server as Ollama**

```bash
# On cloud server
git clone your-repo
cd backend
pip install -r requirements.txt

# Set environment variables
export MONGO_URL=your-mongodb-url
export OLLAMA_BASE_URL=http://localhost:11434
export LLM_PROVIDER=ollama

# Run with PM2 or systemd
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8000" --name bizpulse-api
```

**Option B: Separate Backend Server**

- Deploy backend to a separate server
- Point `OLLAMA_BASE_URL` to Ollama server IP
- Use load balancer if needed

### Step 7: Set Up Domain & SSL

**Using Nginx:**

```nginx
# /etc/nginx/sites-available/bizpulse
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
    }
}
```

**Enable SSL with Let's Encrypt:**

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

### Step 8: Security Hardening

```bash
# 1. Use firewall
sudo ufw enable

# 2. Disable password auth (use SSH keys only)
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no

# 3. Use fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban

# 4. Restrict Ollama access (optional - use reverse proxy)
# Only allow from backend server IP
```

---

## Deployment Architecture

### Architecture 1: All on One Server

```
Internet
    ↓
[Cloud Server]
├── Nginx (Port 80/443)
├── Backend API (Port 8000)
├── Ollama (Port 11434)
└── MongoDB (Port 27017) [or external]
```

### Architecture 2: Separated Services

```
Internet
    ↓
[Load Balancer]
    ↓
[Backend Server 1] ──┐
[Backend Server 2] ──┼──→ [Ollama Server]
[Backend Server 3] ──┘
    ↓
[MongoDB Cluster]
```

---

## Step-by-Step Deployment (AWS Example)

### 1. Launch EC2 Instance

```bash
# Launch g5.xlarge instance
# OS: Ubuntu 22.04 LTS
# Storage: 200GB SSD
# Security Group: Allow SSH (22), HTTP (80), HTTPS (443), Ollama (11434)
```

### 2. Connect to Server

```bash
ssh -i your-key.pem ubuntu@your-server-ip
```

### 3. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install NVIDIA drivers (if GPU instance)
sudo apt install nvidia-driver-535 -y
sudo reboot

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Install Python
sudo apt install python3.10 python3-pip python3-venv -y

# Install Nginx
sudo apt install nginx -y
```

### 4. Configure Ollama

```bash
# Set Ollama to listen on all interfaces
export OLLAMA_HOST=0.0.0.0:11434
echo 'OLLAMA_HOST=0.0.0.0:11434' | sudo tee -a /etc/environment

# Start Ollama service
sudo systemctl enable ollama
sudo systemctl start ollama

# Pull models
ollama pull qwen2.5:32b-instruct
ollama pull llama3:70b
```

### 5. Deploy Backend

```bash
# Clone repository
git clone https://github.com/your-repo/bizpulse.git
cd bizpulse/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
nano .env
# Add:
# MONGO_URL=your-mongodb-url
# OLLAMA_BASE_URL=http://localhost:11434
# LLM_PROVIDER=ollama
# OLLAMA_MODEL=qwen2.5:32b-instruct

# Test run
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 6. Set Up PM2 (Process Manager)

```bash
# Install PM2
npm install -g pm2

# Start backend
cd /path/to/backend
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8000" --name bizpulse-api

# Save PM2 configuration
pm2 save
pm2 startup
```

### 7. Configure Nginx

```bash
# Create Nginx config
sudo nano /etc/nginx/sites-available/bizpulse

# Add:
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/bizpulse /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 8. Set Up SSL

```bash
sudo certbot --nginx -d api.yourdomain.com
```

### 9. Update Frontend

**Update frontend API URL:**

```javascript
// frontend/src/config/api.js
const API_BASE_URL = 'https://api.yourdomain.com';
```

---

## Cost Comparison

### Current Setup (Mac Studio)
- **Cost**: $0 (electricity only)
- **Access**: VPN/SSH tunnel required
- **Reliability**: Depends on Mac Studio uptime

### Cloud Deployment Options

| Provider | Instance | Cost/Month | GPU | RAM |
|----------|----------|------------|-----|-----|
| AWS EC2 | g5.xlarge | ~$720 | A10G 24GB | 32GB |
| GCP | n1-standard-4 + T4 | ~$360 | T4 16GB | 15GB |
| RunPod | RTX 3090 | ~$144 | RTX 3090 24GB | 64GB |
| Vast.ai | RTX 4090 | ~$200 | RTX 4090 24GB | 64GB |

---

## Security Considerations

### 1. Restrict Ollama Access

**Option A: Use Nginx Reverse Proxy**

```nginx
# Only allow from localhost (backend)
upstream ollama {
    server 127.0.0.1:11434;
}

server {
    listen 11434;
    server_name _;
    
    location / {
        allow 127.0.0.1;
        deny all;
        proxy_pass http://ollama;
    }
}
```

**Option B: Use Firewall Rules**

```bash
# Only allow from backend server IP
sudo ufw allow from YOUR_BACKEND_IP to any port 11434
sudo ufw deny 11434
```

### 2. Use API Keys for Backend

```bash
# Add API key authentication
OLLAMA_API_KEY=your-secret-key
```

### 3. Enable Rate Limiting

```nginx
# In Nginx config
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

location / {
    limit_req zone=api_limit burst=20;
    proxy_pass http://localhost:8000;
}
```

---

## Monitoring & Maintenance

### 1. Set Up Monitoring

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs -y

# Monitor Ollama
watch -n 1 'curl -s http://localhost:11434/api/tags | jq .models[].name'
```

### 2. Set Up Logging

```bash
# Backend logs
pm2 logs bizpulse-api

# Ollama logs
sudo journalctl -u ollama -f
```

### 3. Auto-Restart on Failure

```bash
# PM2 auto-restart
pm2 startup
pm2 save
```

---

## Next Steps

1. **Choose deployment option** (cloud provider)
2. **Set up server** (install Ollama, dependencies)
3. **Deploy backend** (clone repo, configure, run)
4. **Configure domain** (Nginx, SSL)
5. **Update frontend** (point to new API URL)
6. **Test globally** (from different locations)

---

## Quick Reference

**Server Setup:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Configure
export OLLAMA_HOST=0.0.0.0:11434

# Pull models
ollama pull qwen2.5:32b-instruct
```

**Backend Config:**
```bash
OLLAMA_BASE_URL=http://your-server-ip:11434
LLM_PROVIDER=ollama
```

**Test:**
```bash
curl http://your-server-ip:11434/api/tags
```

---

**Ready to deploy? Start with Step 1!** 🚀
