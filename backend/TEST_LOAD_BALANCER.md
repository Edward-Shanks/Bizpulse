# How to Test Ollama Load Balancing

Since Python might not be directly accessible, here are **3 easy ways** to test the load balancer:

---

## Method 1: Browser Test (EASIEST) ✅

1. **Start your backend server** (if not already running):
   ```powershell
   cd backend
   .\start_server.bat
   # OR if you have venv activated:
   uvicorn app.main:app --reload
   ```

2. **Open the test page in your browser**:
   - Navigate to: `file:///C:/Users/Sumit%20Mishra/Documents/Bizpulse/backend/test_load_balancer.html`
   - OR simply double-click `test_load_balancer.html` in Windows Explorer

3. **Click the test buttons**:
   - "Test Single Request" - Test one request
   - "Test 10 Requests" - Test 10 requests sequentially
   - "Test 20 Requests" - Test 20 requests sequentially
   - "Test 4 Concurrent" - Test 4 requests at the same time

4. **Check the results**:
   - You'll see which endpoint (port) was selected for each request
   - Statistics show distribution across all ports
   - Should see ports 11434, 11435, 11436, 11437 being used

---

## Method 2: PowerShell Script

1. **Navigate to backend directory**:
   ```powershell
   cd "C:\Users\Sumit Mishra\Documents\Bizpulse\backend"
   ```

2. **Run the PowerShell script**:
   ```powershell
   .\test_load_balancer.ps1
   ```

   The script will:
   - Try to find Python (venv, python, python3, or py)
   - Run the test automatically
   - Show you the results

---

## Method 3: Direct API Calls (Using curl or browser)

1. **Make multiple requests to the test endpoint**:
   
   Open multiple browser tabs and visit:
   ```
   http://localhost:8000/api/test/load-balancer
   ```
   
   OR use PowerShell:
   ```powershell
   # Test 10 requests
   1..10 | ForEach-Object {
       Invoke-RestMethod -Uri "http://localhost:8000/api/test/load-balancer" -Method Get
   }
   ```

2. **Check the response**:
   Each response will show:
   ```json
   {
     "status": "success",
     "config": {
       "selected_endpoint": "http://192.168.50.29:11434",
       "port": "11434",
       ...
     }
   }
   ```

3. **Verify distribution**:
   - You should see different ports (11434, 11435, 11436, 11437) in the responses
   - Each request should select the next endpoint in round-robin order

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
2. `config.py` - `OLLAMA_ENDPOINTS` should have 4 URLs
3. Restart backend after config changes

---

## Quick Check: Backend Logs

When you start your backend, you should see:
```
🔄 Ollama load balancer initialized with 4 endpoints: ['http://192.168.50.29:11434', ...]
🔄 Ollama provider initialized with load balancing across 4 endpoints
```

If you see:
```
🔄 Ollama load balancer using single endpoint: http://localhost:11436
```

Then `OLLAMA_ENDPOINTS` is not being used correctly.

---

## Troubleshooting

### Python Not Found
- **Solution**: Use Method 1 (Browser Test) or Method 3 (API calls)
- No Python needed for these methods

### Backend Not Running
- Start it with: `.\start_server.bat` or `uvicorn app.main:app --reload`

### Only One Endpoint Used
- Check `backend/app/core/config.py` line 58-61
- Verify `OLLAMA_ENDPOINTS` has 4 URLs
- Restart backend after config changes

---

## Next Steps

Once you confirm all 4 endpoints are being used:
1. ✅ Load balancing is working
2. ✅ Multiple users can get parallel responses
3. ✅ Ready for production

If you still see only one endpoint, share:
- Backend startup logs
- Response from `/api/test/load-balancer` endpoint
- Contents of `config.py` lines 58-61


