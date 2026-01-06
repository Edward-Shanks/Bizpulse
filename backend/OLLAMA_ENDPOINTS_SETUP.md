# OLLAMA_ENDPOINTS Configuration Guide

## Overview

The `OLLAMA_ENDPOINTS` configuration is now **read-only from the `.env` file**. There are no hardcoded defaults in the code.

---

## Setup Instructions

### 1. Locate or Create `.env` File

The `.env` file should be in the **root directory** of your project:
```
Bizpulse/
├── .env          ← Add OLLAMA_ENDPOINTS here
├── backend/
├── frontend/
└── ...
```

### 2. Add OLLAMA_ENDPOINTS to `.env`

Open your `.env` file and add:

```env
# Ollama Multiple Instances Configuration (for load balancing)
# Format: comma-separated URLs (no spaces around commas)
OLLAMA_ENDPOINTS=http://192.168.50.29:11434,http://192.168.50.29:11435,http://192.168.50.29:11436,http://192.168.50.29:11437
```

**Important Notes:**
- ✅ Use comma-separated URLs (no spaces)
- ✅ Each URL should be complete: `http://IP:PORT`
- ✅ Replace `192.168.50.29` with your Mac Studio's actual IP address
- ✅ You can use 2, 3, 4, or more endpoints

### 3. Example Configurations

#### Single Endpoint (No Load Balancing)
```env
# Leave OLLAMA_ENDPOINTS empty or don't set it
# System will use OLLAMA_BASE_URL instead
OLLAMA_BASE_URL=http://localhost:11436
```

#### Two Endpoints
```env
OLLAMA_ENDPOINTS=http://192.168.50.29:11434,http://192.168.50.29:11435
```

#### Four Endpoints (Recommended)
```env
OLLAMA_ENDPOINTS=http://192.168.50.29:11434,http://192.168.50.29:11435,http://192.168.50.29:11436,http://192.168.50.29:11437
```

#### Different IP Addresses (if using multiple machines)
```env
OLLAMA_ENDPOINTS=http://192.168.50.29:11434,http://192.168.50.30:11434,http://192.168.50.31:11434
```

---

## How It Works

### If OLLAMA_ENDPOINTS is Set:
- ✅ Load balancing is **enabled**
- ✅ Requests are distributed using **round-robin**
- ✅ All endpoints in the list are used

### If OLLAMA_ENDPOINTS is NOT Set:
- ✅ Falls back to **single endpoint mode**
- ✅ Uses `OLLAMA_BASE_URL` only
- ✅ No load balancing (sequential processing)

---

## Verification

### Check Configuration

1. **Start your backend** and check logs:
   ```
   🔄 Ollama load balancer initialized with 4 endpoints: [...]
   ```
   
   OR if not set:
   ```
   🔄 Ollama load balancer using single endpoint: http://localhost:11436
   ```

2. **Use the test endpoint**:
   ```
   http://localhost:8000/api/test/load-balancer
   ```
   
   Response will show:
   ```json
   {
     "config": {
       "num_endpoints": 4,
       "ollama_endpoints": ["http://192.168.50.29:11434", ...]
     }
   }
   ```

---

## Troubleshooting

### Problem: Only One Endpoint Used

**Check:**
1. Is `OLLAMA_ENDPOINTS` set in `.env`?
2. Is the `.env` file in the root directory?
3. Did you restart the backend after changing `.env`?
4. Check backend logs for initialization message

**Solution:**
- Add `OLLAMA_ENDPOINTS` to `.env` file
- Restart backend server
- Verify in logs

### Problem: Backend Can't Find Endpoints

**Check:**
1. Are all Ollama instances running on Mac Studio?
2. Can you access each endpoint from your laptop?
   ```powershell
   # Test each endpoint
   Invoke-WebRequest -Uri "http://192.168.50.29:11434/api/tags"
   Invoke-WebRequest -Uri "http://192.168.50.29:11435/api/tags"
   # etc...
   ```

**Solution:**
- Verify all Ollama instances are running
- Check Mac Studio firewall settings
- Verify IP addresses are correct

### Problem: Configuration Not Loading

**Check:**
1. `.env` file location (should be in project root)
2. File format (no extra spaces, proper syntax)
3. Backend restart after changes

**Solution:**
- Ensure `.env` is in: `C:\Users\Sumit Mishra\Documents\Bizpulse\.env`
- Check file encoding (should be UTF-8)
- Restart backend completely

---

## Environment Variable Format

### ✅ Correct Format:
```env
OLLAMA_ENDPOINTS=http://192.168.50.29:11434,http://192.168.50.29:11435,http://192.168.50.29:11436,http://192.168.50.29:11437
```

### ❌ Wrong Formats:
```env
# Don't use spaces around commas
OLLAMA_ENDPOINTS=http://192.168.50.29:11434, http://192.168.50.29:11435

# Don't use quotes
OLLAMA_ENDPOINTS="http://192.168.50.29:11434,http://192.168.50.29:11435"

# Don't use newlines
OLLAMA_ENDPOINTS=http://192.168.50.29:11434,
http://192.168.50.29:11435
```

---

## Quick Setup Checklist

- [ ] Locate `.env` file in project root
- [ ] Add `OLLAMA_ENDPOINTS` line with your Mac Studio IP
- [ ] Verify format: comma-separated, no spaces, no quotes
- [ ] Save `.env` file
- [ ] Restart backend server
- [ ] Check backend logs for initialization message
- [ ] Test with `/api/test/load-balancer` endpoint
- [ ] Verify all endpoints are being used

---

## Example `.env` File

```env
# MongoDB
MONGO_URL=your_mongodb_url
DB_NAME=bizpulse

# JWT
JWT_SECRET=your-secret-key

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11436
OLLAMA_MODEL=qwen2.5:32b-instruct
OLLAMA_FALLBACK_MODEL=llama3:70b
OLLAMA_TIMEOUT=120
LLM_PROVIDER=ollama

# Ollama Multiple Instances (for load balancing)
OLLAMA_ENDPOINTS=http://192.168.50.29:11434,http://192.168.50.29:11435,http://192.168.50.29:11436,http://192.168.50.29:11437
```

---

## Need Help?

If you're still having issues:
1. Check backend startup logs
2. Verify `.env` file location and format
3. Test endpoints manually with curl/PowerShell
4. Share backend logs for debugging


