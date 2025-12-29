# Parallel Processing Analysis & Solution

## Issue Description
When 3-4 users ask questions simultaneously using the chatbot, responses come sequentially (one by one) instead of in parallel. This causes:
- User 1 gets response first
- User 2 waits, then gets response
- User 3 waits even longer
- Sequential processing instead of parallel

## Root Cause Analysis

### ✅ What's Already Correct
1. **Code is fully async**: All endpoints use `async def` and `await`
2. **MongoDB operations are async**: Using `motor` (AsyncIOMotorDatabase)
3. **HTTP client is async**: Using `httpx.AsyncClient` for LLM calls
4. **No blocking operations found**: No `time.sleep`, synchronous file I/O, or blocking loops

### ❌ Likely Root Cause
**Ollama Server Processing Requests Sequentially**

Even though our code is async, if the Ollama server on Mac Studio processes requests one at a time (which is common for local LLM inference), multiple requests will queue up and process sequentially.

### Evidence
- `htop` shows only 1 CPU core active most of the time
- `running = 1` in process list (occasionally 2-3 for 1 second)
- This indicates requests arrive together but process one-by-one

## Solutions Implemented

### 1. ✅ HTTP Client Connection Pooling (Already Done)
**File**: `backend/app/utils/llm_providers/ollama.py`

```python
self.client = httpx.AsyncClient(
    timeout=self.timeout,
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
    http2=True  # Enable HTTP/2 for better concurrency
)
```

**Impact**: Allows multiple concurrent HTTP connections to Ollama

### 2. ✅ Perplexity Uses Thread Pool (Already Done)
**File**: `backend/app/utils/llm_providers/perplexity.py`

```python
result = await asyncio.to_thread(make_request)
```

**Impact**: Prevents blocking the event loop for Perplexity API calls

## Remaining Issue: Ollama Server Configuration

### Problem
Ollama server on Mac Studio may be processing requests sequentially by default. This is a **server-side limitation**, not a code issue.

### Solution Options

#### Option 1: Configure Ollama for Concurrent Requests (Recommended)
On Mac Studio, configure Ollama to handle multiple concurrent requests:

```bash
# Check Ollama configuration
ollama serve --help

# Ollama should handle concurrent requests by default, but verify:
# 1. Check if multiple models can run simultaneously
# 2. Verify Ollama API supports concurrent requests
```

#### Option 2: Use Multiple Ollama Instances (Advanced)
If Ollama can't handle concurrent requests, run multiple instances on different ports:
- Instance 1: Port 11434
- Instance 2: Port 11435
- Instance 3: Port 11436
- Instance 4: Port 11437

Then implement load balancing in the provider.

#### Option 3: Queue-Based Architecture (Best for Scale)
Implement a queue system (Celery, RQ, or asyncio queue) to:
- Accept all requests immediately
- Queue LLM inference tasks
- Process in parallel with worker pool
- Return responses as they complete

## Current Code Status

### ✅ Already Optimized
1. **Async endpoints**: All routes use `async def`
2. **Async MongoDB**: Using `motor` for non-blocking DB operations
3. **Async HTTP**: Using `httpx.AsyncClient` with connection pooling
4. **No blocking operations**: No `time.sleep`, sync I/O, or blocking loops

### ⚠️ Potential Bottleneck
**Ollama server processing requests sequentially**

## Verification Steps

### Test 1: Check Ollama Concurrency
```bash
# On Mac Studio, test concurrent requests
curl -X POST http://localhost:11434/api/chat -d '{"model":"qwen2.5:32b-instruct","messages":[{"role":"user","content":"test1"}]}' &
curl -X POST http://localhost:11434/api/chat -d '{"model":"qwen2.5:32b-instruct","messages":[{"role":"user","content":"test2"}]}' &
curl -X POST http://localhost:11434/api/chat -d '{"model":"qwen2.5:32b-instruct","messages":[{"role":"user","content":"test3"}]}' &
```

If responses come sequentially → Ollama is the bottleneck

### Test 2: Monitor Backend During Concurrent Requests
```bash
# Run htop while 3-4 users chat simultaneously
htop

# Expected if fixed:
# - Multiple CPU cores active
# - running = 3-4 (not just 1)
# - Responses arrive together, not sequentially
```

## Recommendations

### Immediate (Code is Already Correct)
✅ Code is already optimized for parallelism
✅ HTTP client configured for concurrency
✅ All operations are async

### Next Steps (Server-Side)
1. **Verify Ollama Configuration**: Check if Ollama on Mac Studio supports concurrent requests
2. **Monitor Ollama Logs**: Check if requests are queued on Ollama side
3. **Consider Queue System**: If Ollama can't handle concurrency, implement queue-based processing

### If Ollama is the Bottleneck
The issue is **not in our code** - it's a server-side limitation. Options:
1. Configure Ollama for concurrent processing (if supported)
2. Use multiple Ollama instances with load balancing
3. Implement queue-based architecture for true parallelism

## Conclusion

**Our code is already optimized for parallel processing.** The sequential behavior is likely due to Ollama server processing requests one at a time. This is a server-side limitation that requires:
- Ollama configuration changes, OR
- Multiple Ollama instances, OR
- Queue-based architecture

The code changes we've made (HTTP client connection pooling) will help once Ollama can handle concurrent requests.

