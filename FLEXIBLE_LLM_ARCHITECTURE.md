# Flexible LLM Provider Architecture
## Switch Between Perplexity, Local Ollama, and vLLM Seamlessly

---

## Overview

This document describes a **provider-based architecture** that allows you to easily switch between:
- **Perplexity API** (current)
- **Local Ollama** (Mac Studio via SSH)
- **vLLM** (future cloud deployment)

**Key Principle**: Single interface, multiple implementations.

---

## Architecture Design

### Provider Pattern Implementation

```
┌─────────────────────────────────────────────────────────┐
│              InsightsService.process_chat()              │
│  (No changes needed - uses LLMProvider interface)       │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              LLMProvider (Abstract Interface)            │
│  - generate(prompt, history, system_message)            │
│  - stream(prompt, history, system_message)               │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Perplexity   │ │ Ollama       │ │ vLLM        │
│ Provider     │ │ Provider      │ │ Provider    │
│ (Current)    │ │ (Mac Studio)  │ │ (Future)    │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## Implementation

### Step 1: Create LLM Provider Interface

**File**: `backend/app/utils/llm_providers/base.py`

```python
"""
Base LLM Provider Interface
All LLM providers must implement this interface
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, AsyncGenerator

class LLMProvider(ABC):
    """Abstract base class for all LLM providers"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict]] = None,
        custom_system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> str:
        """
        Generate response from LLM
        
        Args:
            prompt: User prompt/question
            conversation_history: Previous conversation messages
            custom_system_message: Optional custom system message
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
            
        Returns:
            Generated response text
        """
        pass
    
    @abstractmethod
    async def stream(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict]] = None,
        custom_system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream response from LLM
        
        Args:
            prompt: User prompt/question
            conversation_history: Previous conversation messages
            custom_system_message: Optional custom system message
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
            
        Yields:
            Response tokens as they are generated
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass
```

### Step 2: Perplexity Provider (Existing)

**File**: `backend/app/utils/llm_providers/perplexity.py`

```python
"""
Perplexity API Provider
"""
import os
import asyncio
import requests
import logging
from typing import Optional, List, Dict, AsyncGenerator
from fastapi import HTTPException
from app.utils.llm_providers.base import LLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class PerplexityProvider(LLMProvider):
    """Perplexity API provider implementation"""
    
    def __init__(self):
        self.api_key = settings.PERPLEXITY_API_KEY or os.getenv("PPLX_API_KEY1")
        if not self.api_key:
            logger.warning("Perplexity API key not found")
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.model = "sonar-pro"
        self.timeout = 60
    
    def get_provider_name(self) -> str:
        return "perplexity"
    
    def is_available(self) -> bool:
        return self.api_key is not None
    
    async def generate(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict]] = None,
        custom_system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> str:
        """Generate response using Perplexity API"""
        if not self.is_available():
            raise HTTPException(
                status_code=503,
                detail="Perplexity provider not available (API key missing)"
            )
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        system_content = custom_system_message or (
            "You are Vector AI, a strategic business intelligence analyst for ThriveBrands. "
            "Analyze the provided business data and generate strategic marketing and business recommendations. "
            "All monetary values are in Euros (€). Be specific, data-driven, and actionable."
        )
        
        messages = [{"role": "system", "content": system_content}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                def make_request():
                    response = requests.post(
                        self.base_url,
                        headers=headers,
                        json=payload,
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                    result = response.json()
                    if 'choices' not in result or len(result['choices']) == 0:
                        raise ValueError("Invalid response format from Perplexity API")
                    return result['choices'][0]['message']['content']
                
                result = await asyncio.to_thread(make_request)
                logger.info(f"Perplexity API call successful on attempt {attempt + 1}")
                return result
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Perplexity API error on attempt {attempt + 1}: {str(e)}")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    logger.error(f"Perplexity API failed after {max_retries} attempts: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Perplexity API error: {str(e)}"
                    )
    
    async def stream(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict]] = None,
        custom_system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream response from Perplexity API"""
        # Perplexity streaming implementation
        # (Similar to generate but with streaming)
        raise NotImplementedError("Perplexity streaming not yet implemented")
```

### Step 3: Ollama Provider (Mac Studio)

**File**: `backend/app/utils/llm_providers/ollama.py`

```python
"""
Ollama Provider (Local LLM on Mac Studio)
Supports remote Ollama instances via SSH tunnel or direct network access
"""
import os
import asyncio
import httpx
import logging
from typing import Optional, List, Dict, AsyncGenerator
from fastapi import HTTPException
from app.utils.llm_providers.base import LLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class OllamaProvider(LLMProvider):
    """Ollama provider implementation for local LLM"""
    
    def __init__(self):
        # Configuration from environment
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:32b-instruct")  # Use existing model
        self.fallback_model = os.getenv("OLLAMA_FALLBACK_MODEL", "llama3:70b")
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "120"))
        self.client = httpx.AsyncClient(timeout=self.timeout)
        self.is_remote = "localhost" not in self.base_url and "127.0.0.1" not in self.base_url
        
        logger.info(f"Ollama provider initialized: {self.base_url}, model: {self.model}")
    
    def get_provider_name(self) -> str:
        return "ollama"
    
    async def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {str(e)}")
            return False
    
    async def generate(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict]] = None,
        custom_system_message: Optional[str] = None,
        temperature: float = 0.2,  # Lower temperature for business responses
        max_tokens: int = 4000,
        **kwargs
    ) -> str:
        """Generate response using Ollama"""
        # Check availability
        if not await self.is_available():
            raise HTTPException(
                status_code=503,
                detail=f"Ollama service not available at {self.base_url}"
            )
        
        # Build messages
        messages = []
        if custom_system_message:
            messages.append({"role": "system", "content": custom_system_message})
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                content = result.get("message", {}).get("content", "")
                
                if not content and attempt < max_retries - 1:
                    # Try fallback model
                    logger.warning(f"Empty response from {self.model}, trying fallback {self.fallback_model}")
                    payload["model"] = self.fallback_model
                    continue
                
                logger.info(f"Ollama response generated successfully (model: {payload['model']})")
                return content
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    # Model not found, try fallback
                    if payload["model"] != self.fallback_model:
                        logger.warning(f"Model {self.model} not found, trying fallback {self.fallback_model}")
                        payload["model"] = self.fallback_model
                        continue
                
                if attempt < max_retries - 1:
                    logger.warning(f"Ollama error on attempt {attempt + 1}: {str(e)}")
                    await asyncio.sleep(1)
                    continue
                else:
                    logger.error(f"Ollama failed after {max_retries} attempts: {str(e)}")
                    raise HTTPException(
                        status_code=e.response.status_code,
                        detail=f"Ollama API error: {str(e)}"
                    )
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Ollama error on attempt {attempt + 1}: {str(e)}")
                    await asyncio.sleep(1)
                    continue
                else:
                    logger.error(f"Ollama failed after {max_retries} attempts: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Ollama error: {str(e)}"
                    )
        
        raise HTTPException(
            status_code=500,
            detail="Ollama generation failed after all retries"
        )
    
    async def stream(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict]] = None,
        custom_system_message: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream response from Ollama"""
        if not await self.is_available():
            raise HTTPException(
                status_code=503,
                detail=f"Ollama service not available at {self.base_url}"
            )
        
        messages = []
        if custom_system_message:
            messages.append({"role": "system", "content": custom_system_message})
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        import json
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Ollama streaming error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Ollama streaming error: {str(e)}"
            )
```

### Step 4: LLM Provider Factory

**File**: `backend/app/utils/llm_providers/factory.py`

```python
"""
LLM Provider Factory
Creates and manages LLM provider instances
"""
import os
import logging
from typing import Optional
from app.utils.llm_providers.base import LLMProvider
from app.utils.llm_providers.perplexity import PerplexityProvider
from app.utils.llm_providers.ollama import OllamaProvider

logger = logging.getLogger(__name__)

class LLMProviderFactory:
    """Factory for creating LLM provider instances"""
    
    _providers = {
        "perplexity": PerplexityProvider,
        "ollama": OllamaProvider,
        # "vllm": VLLMProvider,  # Future implementation
    }
    
    _current_provider: Optional[LLMProvider] = None
    
    @classmethod
    def get_provider(cls, provider_name: Optional[str] = None) -> LLMProvider:
        """
        Get LLM provider instance
        
        Args:
            provider_name: Provider name (perplexity, ollama, vllm)
                          If None, uses LLM_PROVIDER environment variable
        
        Returns:
            LLMProvider instance
        """
        if provider_name is None:
            provider_name = os.getenv("LLM_PROVIDER", "perplexity").lower()
        
        if provider_name not in cls._providers:
            logger.warning(f"Unknown provider '{provider_name}', defaulting to 'perplexity'")
            provider_name = "perplexity"
        
        # Return cached provider if same type
        if cls._current_provider and cls._current_provider.get_provider_name() == provider_name:
            return cls._current_provider
        
        # Create new provider instance
        provider_class = cls._providers[provider_name]
        cls._current_provider = provider_class()
        
        logger.info(f"LLM Provider initialized: {provider_name}")
        return cls._current_provider
    
    @classmethod
    def list_available_providers(cls) -> list:
        """List all available provider names"""
        return list(cls._providers.keys())
    
    @classmethod
    async def get_available_provider(cls) -> Optional[LLMProvider]:
        """Get first available provider"""
        for provider_name in cls._providers.keys():
            provider = cls.get_provider(provider_name)
            if hasattr(provider, 'is_available'):
                if await provider.is_available() if asyncio.iscoroutine(provider.is_available()) else provider.is_available():
                    return provider
        return None

# Convenience function for backward compatibility
def get_llm_provider(provider_name: Optional[str] = None) -> LLMProvider:
    """Get LLM provider (convenience function)"""
    return LLMProviderFactory.get_provider(provider_name)
```

### Step 5: Update AI Service (Unified Interface)

**File**: `backend/app/utils/ai_service.py` (Replace entire file)

```python
"""
AI Service utilities
Unified interface for all LLM providers (Perplexity, Ollama, vLLM)
"""
import logging
from typing import Optional, List, Dict
from app.utils.llm_providers.factory import get_llm_provider

logger = logging.getLogger(__name__)

async def query_llm(
    prompt: str,
    conversation_history: Optional[List[Dict]] = None,
    custom_system_message: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4000,
    provider_name: Optional[str] = None,
    **kwargs
) -> str:
    """
    Query LLM (unified interface for all providers)
    
    This function automatically uses the provider specified in LLM_PROVIDER
    environment variable, or can be overridden with provider_name parameter.
    
    Args:
        prompt: User prompt/question
        conversation_history: Previous conversation messages
        custom_system_message: Optional custom system message
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens to generate
        provider_name: Override provider (perplexity, ollama, vllm)
        **kwargs: Provider-specific parameters
    
    Returns:
        Generated response text
    """
    try:
        provider = get_llm_provider(provider_name)
        response = await provider.generate(
            prompt=prompt,
            conversation_history=conversation_history,
            custom_system_message=custom_system_message,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        logger.info(f"LLM response generated using provider: {provider.get_provider_name()}")
        return response
    except Exception as e:
        logger.error(f"Error querying LLM: {str(e)}")
        raise

# Backward compatibility aliases
async def query_perplexity(
    prompt: str,
    conversation_history: Optional[List[Dict]] = None,
    custom_system_message: Optional[str] = None
) -> str:
    """Backward compatibility - uses configured provider"""
    return await query_llm(
        prompt=prompt,
        conversation_history=conversation_history,
        custom_system_message=custom_system_message,
        provider_name="perplexity"  # Force Perplexity for backward compatibility
    )

async def query_ollama(
    prompt: str,
    conversation_history: Optional[List[Dict]] = None,
    custom_system_message: Optional[str] = None
) -> str:
    """Convenience function for Ollama provider"""
    return await query_llm(
        prompt=prompt,
        conversation_history=conversation_history,
        custom_system_message=custom_system_message,
        provider_name="ollama"
    )
```

### Step 6: Update Insights Service (No Changes Needed!)

**File**: `backend/app/services/insights_service.py`

**Only change the import:**
```python
# OLD:
from app.utils.ai_service import query_perplexity

# NEW:
from app.utils.ai_service import query_llm as query_perplexity
# OR keep using query_perplexity - it will use configured provider
```

**That's it!** The rest of the code remains unchanged.

---

## Configuration

### Environment Variables

**File**: `.env` or `.env.local`

```bash
# LLM Provider Selection
# Options: perplexity, ollama, vllm
LLM_PROVIDER=ollama

# Perplexity Configuration (if using Perplexity)
PERPLEXITY_API_KEY=your_perplexity_key_here

# Ollama Configuration (if using Ollama)
# For Mac Studio accessed via SSH tunnel or network
OLLAMA_BASE_URL=http://192.178.90.31:11434
# OR for local Ollama
# OLLAMA_BASE_URL=http://localhost:11434

OLLAMA_MODEL=qwen2.5:32b-instruct  # Use your existing model
OLLAMA_FALLBACK_MODEL=llama3:70b
OLLAMA_TIMEOUT=120

# vLLM Configuration (future)
# VLLM_BASE_URL=http://your-vllm-server:8000
# VLLM_MODEL=your-model
```

---

## Mac Studio Setup for Remote Access

### Option 1: Direct Network Access (Recommended)

**On Mac Studio:**

1. **Check Ollama is accessible:**
```bash
# On Mac Studio
curl http://localhost:11434/api/tags
```

2. **Configure Ollama to accept remote connections:**
```bash
# Edit Ollama configuration
export OLLAMA_HOST=0.0.0.0:11434

# Restart Ollama
# If using Launchd service, update the plist file
```

3. **Configure Firewall (if needed):**
```bash
# Allow port 11434
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /Applications/Ollama.app
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /Applications/Ollama.app
```

4. **Test from laptop:**
```bash
# From your laptop
curl http://192.178.90.31:11434/api/tags
```

### Option 2: SSH Tunnel (More Secure)

**On your laptop, create SSH tunnel:**

```bash
# Create SSH tunnel (port forwarding)
ssh -L 11434:localhost:11434 rivemain@192.178.90.31

# Keep this terminal open
# Now use localhost:11434 in your .env file
```

**In `.env`:**
```bash
OLLAMA_BASE_URL=http://localhost:11434
```

### Option 3: SSH Tunnel with Background Process

**Create persistent SSH tunnel:**

```bash
# Create SSH tunnel in background
ssh -f -N -L 11434:localhost:11434 rivemain@192.178.90.31

# Verify tunnel is working
curl http://localhost:11434/api/tags
```

**Create script for easy tunnel management:**

**File**: `scripts/ollama_tunnel.sh`
```bash
#!/bin/bash

MAC_STUDIO_IP="192.178.90.31"
MAC_STUDIO_USER="rivemain"
LOCAL_PORT="11434"
REMOTE_PORT="11434"

# Check if tunnel already exists
if lsof -Pi :$LOCAL_PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "SSH tunnel already exists on port $LOCAL_PORT"
    exit 0
fi

# Create SSH tunnel
echo "Creating SSH tunnel to Mac Studio..."
ssh -f -N -L $LOCAL_PORT:localhost:$REMOTE_PORT $MAC_STUDIO_USER@$MAC_STUDIO_IP

if [ $? -eq 0 ]; then
    echo "✅ SSH tunnel created successfully"
    echo "Ollama accessible at http://localhost:$LOCAL_PORT"
else
    echo "❌ Failed to create SSH tunnel"
    exit 1
fi
```

**Make executable:**
```bash
chmod +x scripts/ollama_tunnel.sh
```

**Usage:**
```bash
./scripts/ollama_tunnel.sh
```

---

## Testing the Setup

### Test 1: Check Ollama Access from Laptop

**From your laptop terminal:**
```bash
# Test direct access (if using network)
curl http://192.178.90.31:11434/api/tags

# OR test via SSH tunnel
curl http://localhost:11434/api/tags
```

**Expected output:**
```json
{
  "models": [
    {
      "name": "qwen2.5:32b-instruct",
      "modified_at": "2025-12-21T...",
      "size": 19000000000
    },
    ...
  ]
}
```

### Test 2: Test Model Generation

```bash
# Test model generation
curl http://192.178.90.31:11434/api/generate -d '{
  "model": "qwen2.5:32b-instruct",
  "prompt": "Say hello",
  "stream": false
}'
```

### Test 3: Test from Python

**File**: `scripts/test_ollama_connection.py`
```python
import asyncio
import httpx
import os

async def test_ollama():
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Test health
        try:
            response = await client.get(f"{base_url}/api/tags")
            print(f"✅ Health check: {response.status_code}")
            print(f"   Available models: {len(response.json().get('models', []))}")
        except Exception as e:
            print(f"❌ Health check failed: {str(e)}")
            return
        
        # Test generation
        try:
            response = await client.post(
                f"{base_url}/api/chat",
                json={
                    "model": "qwen2.5:32b-instruct",
                    "messages": [{"role": "user", "content": "Say hello in one word"}],
                    "stream": False
                }
            )
            result = response.json()
            print(f"✅ Generation test: {result.get('message', {}).get('content', 'No content')}")
        except Exception as e:
            print(f"❌ Generation test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_ollama())
```

**Run:**
```bash
python scripts/test_ollama_connection.py
```

---

## Switching Between Providers

### Method 1: Environment Variable (Recommended)

**Switch to Ollama:**
```bash
export LLM_PROVIDER=ollama
# Restart your FastAPI server
```

**Switch to Perplexity:**
```bash
export LLM_PROVIDER=perplexity
# Restart your FastAPI server
```

### Method 2: Runtime Switching (API Endpoint)

**Add endpoint for runtime switching:**

**File**: `backend/app/api/admin.py`
```python
"""
Admin endpoints for LLM provider management
"""
from fastapi import APIRouter, HTTPException
from app.utils.llm_providers.factory import LLMProviderFactory
import os

router = APIRouter()

@router.post("/admin/llm-provider/{provider_name}")
async def switch_provider(provider_name: str):
    """Switch LLM provider at runtime"""
    available_providers = LLMProviderFactory.list_available_providers()
    
    if provider_name not in available_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider. Available: {available_providers}"
        )
    
    # Update environment variable
    os.environ["LLM_PROVIDER"] = provider_name
    
    # Get new provider to verify
    provider = LLMProviderFactory.get_provider(provider_name)
    
    return {
        "status": "success",
        "provider": provider_name,
        "available": await provider.is_available() if hasattr(provider, 'is_available') else True
    }

@router.get("/admin/llm-provider/current")
async def get_current_provider():
    """Get current LLM provider"""
    current = os.getenv("LLM_PROVIDER", "perplexity")
    provider = LLMProviderFactory.get_provider()
    
    return {
        "current_provider": current,
        "provider_name": provider.get_provider_name(),
        "available": await provider.is_available() if hasattr(provider, 'is_available') else True
    }

@router.get("/admin/llm-provider/list")
async def list_providers():
    """List all available providers"""
    providers = LLMProviderFactory.list_available_providers()
    current = os.getenv("LLM_PROVIDER", "perplexity")
    
    return {
        "available_providers": providers,
        "current_provider": current
    }
```

**Add to main.py:**
```python
from app.api.admin import router as admin_router

app.include_router(admin_router, prefix="/api", tags=["admin"])
```

**Usage:**
```bash
# Switch to Ollama
curl -X POST http://localhost:8000/api/admin/llm-provider/ollama

# Check current provider
curl http://localhost:8000/api/admin/llm-provider/current

# List all providers
curl http://localhost:8000/api/admin/llm-provider/list
```

---

## Future: vLLM Provider

**File**: `backend/app/utils/llm_providers/vllm.py` (Future Implementation)

```python
"""
vLLM Provider (Future Implementation)
For cloud-based vLLM deployment
"""
import os
import asyncio
import httpx
import logging
from typing import Optional, List, Dict, AsyncGenerator
from fastapi import HTTPException
from app.utils.llm_providers.base import LLMProvider

logger = logging.getLogger(__name__)

class VLLMProvider(LLMProvider):
    """vLLM provider implementation"""
    
    def __init__(self):
        self.base_url = os.getenv("VLLM_BASE_URL", "http://localhost:8000")
        self.model = os.getenv("VLLM_MODEL", "your-model")
        self.client = httpx.AsyncClient(timeout=120.0)
    
    def get_provider_name(self) -> str:
        return "vllm"
    
    async def is_available(self) -> bool:
        try:
            response = await self.client.get(f"{self.base_url}/health", timeout=5.0)
            return response.status_code == 200
        except:
            return False
    
    async def generate(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict]] = None,
        custom_system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> str:
        """Generate using vLLM (OpenAI-compatible API)"""
        messages = []
        if custom_system_message:
            messages.append({"role": "system", "content": custom_system_message})
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = await self.client.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    async def stream(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict]] = None,
        custom_system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream from vLLM"""
        # Similar to generate but with streaming
        raise NotImplementedError("vLLM streaming not yet implemented")
```

**Add to factory:**
```python
from app.utils.llm_providers.vllm import VLLMProvider

_providers = {
    "perplexity": PerplexityProvider,
    "ollama": OllamaProvider,
    "vllm": VLLMProvider,  # Add this
}
```

---

## Quick Start Guide

### Step 1: Set Up SSH Tunnel (if needed)

```bash
# Create SSH tunnel
ssh -f -N -L 11434:localhost:11434 rivemain@192.178.90.31

# Verify
curl http://localhost:11434/api/tags
```

### Step 2: Configure Environment

**Create `.env.local`:**
```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434  # If using SSH tunnel
# OR
OLLAMA_BASE_URL=http://192.178.90.31:11434  # If direct network access

OLLAMA_MODEL=qwen2.5:32b-instruct
OLLAMA_FALLBACK_MODEL=llama3:70b
```

### Step 3: Install Dependencies

```bash
cd backend
pip install httpx
```

### Step 4: Create Provider Files

Create the directory structure:
```bash
mkdir -p backend/app/utils/llm_providers
touch backend/app/utils/llm_providers/__init__.py
```

Then create all the files as described above.

### Step 5: Update Imports

**In `backend/app/services/insights_service.py`:**
```python
# Change this line:
from app.utils.ai_service import query_perplexity

# To:
from app.utils.ai_service import query_llm as query_perplexity
```

### Step 6: Test

```bash
# Start your FastAPI server
cd backend
uvicorn app.main:app --reload

# Test the endpoint
curl -X POST http://localhost:8000/api/insights/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the revenue for Food business?"}'
```

---

## Benefits of This Architecture

✅ **Zero Code Changes**: InsightsService doesn't need changes  
✅ **Easy Switching**: Change one environment variable  
✅ **Future-Proof**: Add vLLM provider when ready  
✅ **Backward Compatible**: Existing code still works  
✅ **Testable**: Test each provider independently  
✅ **Flexible**: Use different providers for different features  

---

## Migration Checklist

- [ ] Create provider interface (`base.py`)
- [ ] Create Perplexity provider (`perplexity.py`)
- [ ] Create Ollama provider (`ollama.py`)
- [ ] Create provider factory (`factory.py`)
- [ ] Update AI service (`ai_service.py`)
- [ ] Update Insights service import
- [ ] Set up SSH tunnel or network access
- [ ] Configure environment variables
- [ ] Test Ollama connection
- [ ] Test provider switching
- [ ] Deploy and monitor

---

## Troubleshooting

### Issue: Cannot connect to Mac Studio Ollama

**Solutions:**
1. Check SSH tunnel is active: `lsof -i :11434`
2. Check Mac Studio firewall allows port 11434
3. Verify Ollama is running: `ssh rivemain@192.178.90.31 "curl http://localhost:11434/api/tags"`
4. Try direct network access instead of SSH tunnel

### Issue: Model not found

**Solutions:**
1. Check available models: `curl http://192.178.90.31:11434/api/tags`
2. Update `OLLAMA_MODEL` in `.env` to match available model
3. Use fallback model if primary fails

### Issue: Slow responses

**Solutions:**
1. Check Mac Studio CPU/memory usage
2. Use smaller model (8B instead of 32B)
3. Reduce `max_tokens` parameter
4. Enable caching

---

**Your architecture is now future-proof and flexible!** 🚀

