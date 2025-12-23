# LLM Provider Guide - Understanding Which Provider is Used

## 🎯 Quick Answer

**To check which provider is being used, look at your backend logs when you ask a question in the chat.**

You'll see clear messages like:
```
================================================================================
🤖 USING LLM PROVIDER: OLLAMA
📍 Provider Type: ollama
🔗 Ollama URL: http://localhost:11436
💬 User Prompt Length: 150 characters
================================================================================
```

OR

```
================================================================================
🤖 USING LLM PROVIDER: PERPLEXITY
📍 Provider Type: perplexity
🔗 Perplexity API: https://api.perplexity.ai
💬 User Prompt Length: 150 characters
================================================================================
```

---

## 📁 Key Files That Control Provider Selection

### 1. **Environment Configuration** (`.env` file)
**Location:** `backend/.env`

**Controls:** Which provider is used by default

```bash
# Set this to switch providers
LLM_PROVIDER=ollama        # Use Ollama (Mac Studio)
# OR
LLM_PROVIDER=perplexity    # Use Perplexity API

# Ollama Configuration (only needed if using Ollama)
OLLAMA_BASE_URL=http://localhost:11436
OLLAMA_MODEL=qwen2.5:32b-instruct
OLLAMA_FALLBACK_MODEL=llama3:70b
```

**This is the MAIN file to change providers!**

---

### 2. **Provider Factory** (Creates Provider Instances)
**Location:** `backend/app/utils/llm_providers/factory.py`

**What it does:**
- Reads `LLM_PROVIDER` from environment
- Creates the appropriate provider instance (Ollama or Perplexity)
- Logs which provider is initialized

**Key function:**
```python
LLMProviderFactory.get_provider(provider_name=None)
# If provider_name is None, uses LLM_PROVIDER from .env
```

---

### 3. **AI Service** (Unified Interface)
**Location:** `backend/app/utils/ai_service.py`

**What it does:**
- Provides unified `query_llm()` function
- Calls the appropriate provider based on configuration
- **Logs which provider is being used** (with clear formatting)

**Key functions:**
- `query_llm()` - Main function (uses configured provider)
- `query_perplexity()` - Backward compatibility (actually uses configured provider)
- `query_ollama()` - Convenience function (forces Ollama)

---

### 4. **Insights Service** (Chat Logic)
**Location:** `backend/app/services/insights_service.py`

**What it does:**
- Handles chat requests
- Calls `query_perplexity()` (which uses configured provider)
- Processes responses

**Line 9:**
```python
from app.utils.ai_service import query_perplexity
```

**Note:** Even though it's called `query_perplexity`, it actually uses whatever provider is configured in `.env`!

---

### 5. **Provider Implementations**

#### Ollama Provider
**Location:** `backend/app/utils/llm_providers/ollama.py`

**What it does:**
- Connects to Ollama on Mac Studio (via SSH tunnel)
- Makes API calls to `http://localhost:11436/api/chat`
- Logs Ollama-specific information

#### Perplexity Provider
**Location:** `backend/app/utils/llm_providers/perplexity.py`

**What it does:**
- Connects to Perplexity API
- Makes API calls to `https://api.perplexity.ai/chat/completions`
- Uses API key from environment

---

## 🔍 How to Check Which Provider is Active

### Method 1: Check Backend Logs

**When you ask a question in chat, look at your backend terminal/logs:**

You'll see:
```
================================================================================
🔧 LLM PROVIDER INITIALIZED: OLLAMA
📋 Available Providers: perplexity, ollama
✅ Active Provider: ollama
================================================================================
```

Then when a request comes in:
```
================================================================================
🤖 USING LLM PROVIDER: OLLAMA
📍 Provider Type: ollama
🔗 Ollama URL: http://localhost:11436
💬 User Prompt Length: 150 characters
================================================================================
🦙 OLLAMA: Starting generation request
🦙 OLLAMA: Base URL: http://localhost:11436
🦙 OLLAMA: Model: qwen2.5:32b-instruct
🦙 OLLAMA: Temperature: 0.2, Max Tokens: 4000
🦙 OLLAMA: Service available: True
```

### Method 2: Check Environment Variable

**On your laptop, run:**
```bash
# Check current provider setting
echo $LLM_PROVIDER

# OR in PowerShell
echo $env:LLM_PROVIDER
```

**Or check `.env` file:**
```bash
cat backend/.env | grep LLM_PROVIDER
```

### Method 3: Add Debug Endpoint (Optional)

**Add this to your backend to check provider status:**

**File:** `backend/app/api/debug.py`
```python
from fastapi import APIRouter
from app.utils.llm_providers.factory import LLMProviderFactory
import os

router = APIRouter()

@router.get("/debug/llm-provider")
async def get_llm_provider_status():
    current_provider = os.getenv("LLM_PROVIDER", "perplexity")
    provider = LLMProviderFactory.get_provider()
    
    return {
        "configured_provider": current_provider,
        "active_provider": provider.get_provider_name(),
        "is_available": await provider.is_available() if hasattr(provider, 'is_available') else True,
        "available_providers": LLMProviderFactory.list_available_providers()
    }
```

**Then check:**
```bash
curl http://localhost:8000/api/debug/llm-provider
```

---

## 🔄 How to Switch Providers

### Switch to Ollama (Mac Studio)

1. **Edit `backend/.env`:**
   ```bash
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11436
   ```

2. **Restart backend:**
   ```bash
   # Stop backend (Ctrl+C)
   # Start again
   uvicorn app.main:app --reload
   ```

3. **Check logs** - you should see:
   ```
   🔧 LLM PROVIDER INITIALIZED: OLLAMA
   ```

### Switch to Perplexity

1. **Edit `backend/.env`:**
   ```bash
   LLM_PROVIDER=perplexity
   PERPLEXITY_API_KEY=your_key_here
   ```

2. **Restart backend**

3. **Check logs** - you should see:
   ```
   🔧 LLM PROVIDER INITIALIZED: PERPLEXITY
   ```

---

## 📊 Log Messages Explained

### When Provider is Initialized:
```
================================================================================
🔧 LLM PROVIDER INITIALIZED: OLLAMA
📋 Available Providers: perplexity, ollama
✅ Active Provider: ollama
================================================================================
```

### When Request is Made:
```
================================================================================
🤖 USING LLM PROVIDER: OLLAMA
📍 Provider Type: ollama
🔗 Ollama URL: http://localhost:11436
💬 User Prompt Length: 150 characters
================================================================================
```

### When Response is Received:
```
================================================================================
✅ LLM RESPONSE RECEIVED from OLLAMA
📝 Response Length: 500 characters
================================================================================
```

---

## 🛠️ Where to Make Changes

### To Change Default Provider:
**File:** `backend/.env`
```bash
LLM_PROVIDER=ollama  # or perplexity
```

### To Add New Provider:
1. Create provider class in `backend/app/utils/llm_providers/your_provider.py`
2. Add to factory in `backend/app/utils/llm_providers/factory.py`
3. Update `.env` to use new provider

### To Modify Provider Behavior:
- **Ollama:** Edit `backend/app/utils/llm_providers/ollama.py`
- **Perplexity:** Edit `backend/app/utils/llm_providers/perplexity.py`

### To Change Logging:
- **Provider selection:** `backend/app/utils/llm_providers/factory.py`
- **Request logging:** `backend/app/utils/ai_service.py`
- **Provider-specific:** Individual provider files

---

## ✅ Summary

1. **Check logs** - Clear messages show which provider is used
2. **Main config file:** `backend/.env` (LLM_PROVIDER setting)
3. **Provider selection:** `backend/app/utils/llm_providers/factory.py`
4. **Unified interface:** `backend/app/utils/ai_service.py`
5. **Chat logic:** `backend/app/services/insights_service.py`

**The logs will now clearly show you which provider is being used!** 🎉

