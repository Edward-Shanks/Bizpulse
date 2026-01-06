# How to Run Load Balancer Tests

This guide provides commands to run all the test files for verifying Ollama load balancing.

---

## Method 1: Browser Test (EASIEST - No Python Required) ✅

### Steps:
1. **Start your backend server** (if not already running):
   ```powershell
   cd backend
   .\start_server.bat
   # OR if you have venv activated:
   uvicorn app.main:app --reload
   ```

2. **Open the test page**:
   - Navigate to: `file:///C:/Users/Sumit%20Mishra/Documents/Bizpulse/backend/test_load_balancer.html`
   - OR simply double-click `test_load_balancer.html` in Windows Explorer

3. **Click test buttons**:
   - "Test Single Request" - Test one request
   - "Test 10 Requests" - Test 10 requests sequentially
   - "Test 20 Requests" - Test 20 requests sequentially
   - "Test 4 Concurrent" - Test 4 requests at the same time

4. **Check results**:
   - See which endpoint (port) was selected for each request
   - Statistics show distribution across all ports
   - Should see ports 11434, 11435, 11436, 11437 being used

---

## Method 2: PowerShell Script

### Command:
```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
.\test_load_balancer.ps1
```

The script will:
- Automatically find Python (venv, python, python3, or py)
- Run the test automatically
- Show you the results

---

## Method 3: Direct Python Test (Simple)

### Prerequisites:
- Python must be accessible
- Backend dependencies installed

### Commands:

**Option A: If you have virtual environment:**
```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
.\venv\Scripts\activate
python test_load_balancer_simple.py
```

**Option B: If Python is in PATH:**
```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
python test_load_balancer_simple.py
```

**Option C: Using Python launcher:**
```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
py test_load_balancer_simple.py
```

**Option D: Using Python 3:**
```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
python3 test_load_balancer_simple.py
```

---

## Method 4: Comprehensive Python Test

### Command:
```powershell
cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
python test_ollama_load_balancing.py
```

This test includes:
- Direct endpoint selection test
- Endpoint health check
- API request test (requires backend running)

---

## Method 5: Direct API Endpoint Test (PowerShell)

### Prerequisites:
- Backend server must be running on `http://localhost:8000`

### Command:
```powershell
# Test single request
Invoke-RestMethod -Uri "http://localhost:8000/api/test/load-balancer" -Method Get

# Test 10 requests and show distribution
1..10 | ForEach-Object {
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/test/load-balancer" -Method Get
    Write-Host "Request $_: Port $($result.config.port) - $($result.config.selected_endpoint)"
}

# Test 20 requests and count distribution
$results = 1..20 | ForEach-Object {
    $result = Invoke-RestMethod -Uri "http://localhost:8000/api/test/load-balancer" -Method Get
    $result.config.port
}
$results | Group-Object | Select-Object Name, Count | Format-Table
```

---

## Method 6: Direct API Endpoint Test (Browser)

### Steps:
1. **Start backend server** (if not running)

2. **Open browser and visit multiple times**:
   ```
   http://localhost:8000/api/test/load-balancer
   ```

3. **Check the response** - Each response shows:
   ```json
   {
     "status": "success",
     "config": {
       "selected_endpoint": "http://192.168.50.29:11434",
       "port": "11434",
       "num_endpoints": 4,
       "ollama_endpoints": [...]
     }
   }
   ```

4. **Verify distribution**:
   - Refresh the page multiple times
   - You should see different ports (11434, 11435, 11436, 11437)
   - Each request should select the next endpoint in round-robin order

---

## Method 7: Using curl (if available)

### Command:
```powershell
# Test single request
curl http://localhost:8000/api/test/load-balancer

# Test 10 requests
1..10 | ForEach-Object {
    curl http://localhost:8000/api/test/load-balancer
}
```

---

## Expected Results

### ✅ SUCCESS (Working Correctly):
- All 4 ports (11434, 11435, 11436, 11437) appear in results
- Distribution is roughly even (e.g., 5 requests each for 20 total)
- Ports cycle in order: 11434 → 11435 → 11436 → 11437 → 11434...

### ❌ PROBLEM (Only One Port):
- Only port 11436 appears
- All requests go to the same endpoint

**If you see this, check:**
1. Backend logs for: `🔄 Ollama load balancer initialized with X endpoints`
2. `.env` file - `OLLAMA_ENDPOINTS` should have 4 URLs
3. Restart backend after config changes

---

## Quick Test Checklist

- [ ] Backend server is running
- [ ] `.env` file has `OLLAMA_ENDPOINTS` configured
- [ ] All 4 Ollama instances are running on Mac Studio
- [ ] Network connectivity between laptop and Mac Studio
- [ ] Test endpoint is accessible: `http://localhost:8000/api/test/load-balancer`

---

## Troubleshooting

### Python Not Found
- **Solution**: Use Method 1 (Browser Test) or Method 5 (API Endpoint)
- No Python needed for these methods

### Backend Not Running
- Start it with: `.\start_server.bat` or `uvicorn app.main:app --reload`

### Only One Endpoint Used
- Check `backend/app/core/config.py` - `OLLAMA_ENDPOINTS` should have 4 URLs
- Check backend startup logs
- Restart backend after config changes

### Ports Not Accessible
- Verify all Ollama instances are running on Mac Studio
- Check Mac Studio firewall settings
- Verify IP address is correct in `.env` file

---

## Recommended Testing Order

1. **Start with Method 1 (Browser Test)** - Easiest, no setup needed
2. **Then Method 5 (API Endpoint)** - Quick verification
3. **Finally Method 3 (Python Test)** - Detailed analysis

---

## Example Output (Success)

```
📊 DISTRIBUTION RESULTS:
   Port 11434: 5 times (25.0%) - http://192.168.50.29:11434
   Port 11435: 5 times (25.0%) - http://192.168.50.29:11435
   Port 11436: 5 times (25.0%) - http://192.168.50.29:11436
   Port 11437: 5 times (25.0%) - http://192.168.50.29:11437

✅ SUCCESS: All 4 endpoints are being used!
```


