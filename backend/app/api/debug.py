"""
Debug endpoints for checking system status
"""
from fastapi import APIRouter, HTTPException
from app.utils.llm_providers.factory import LLMProviderFactory
from app.utils.llm_providers.ollama import OllamaProvider
from app.utils.llm_providers.perplexity import PerplexityProvider
import os
import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/debug/llm-provider")
async def get_llm_provider_status():
    """Get current LLM provider status and availability"""
    try:
        current_provider_name = os.getenv("LLM_PROVIDER", "perplexity")
        provider = LLMProviderFactory.get_provider()
        
        # Check availability
        is_available = False
        if hasattr(provider, 'is_available'):
            is_avail = provider.is_available()
            if asyncio.iscoroutine(is_avail):
                is_available = await is_avail
            else:
                is_available = is_avail
        
        # Get provider-specific info
        provider_info = {
            "name": provider.get_provider_name(),
            "is_available": is_available
        }
        
        if isinstance(provider, OllamaProvider):
            provider_info["base_url"] = provider.base_url
            provider_info["model"] = provider.model
            provider_info["fallback_model"] = provider.fallback_model
            
            # Test connection
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{provider.base_url}/api/tags")
                    provider_info["connection_test"] = "success" if response.status_code == 200 else f"failed: {response.status_code}"
            except Exception as e:
                provider_info["connection_test"] = f"failed: {str(e)}"
                provider_info["connection_error"] = str(e)
        
        elif isinstance(provider, PerplexityProvider):
            provider_info["api_key_set"] = provider.api_key is not None
            provider_info["model"] = provider.model
        
        return {
            "configured_provider": current_provider_name,
            "active_provider": provider_info,
            "available_providers": LLMProviderFactory.list_available_providers(),
            "fallback_available": {
                "perplexity": PerplexityProvider().is_available(),
                "ollama": await OllamaProvider().is_available() if hasattr(OllamaProvider(), 'is_available') else False
            }
        }
    except Exception as e:
        logger.error(f"Error getting LLM provider status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/tunnel-status")
async def check_tunnel_status():
    """Check SSH tunnel status for Ollama"""
    try:
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11436")
        
        # Extract port from URL
        import re
        port_match = re.search(r':(\d+)', ollama_url)
        port = port_match.group(1) if port_match else "11436"
        
        # Test connection
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{ollama_url}/api/tags")
                is_connected = response.status_code == 200
                
                if is_connected:
                    models = response.json().get("models", [])
                    return {
                        "tunnel_status": "active",
                        "ollama_url": ollama_url,
                        "port": port,
                        "connection": "success",
                        "models_available": len(models),
                        "models": [m.get("name") for m in models[:5]]  # First 5 models
                    }
                else:
                    return {
                        "tunnel_status": "inactive",
                        "ollama_url": ollama_url,
                        "port": port,
                        "connection": f"failed: HTTP {response.status_code}",
                        "suggestion": "Check if SSH tunnel is running: ssh -f -N -L 11436:127.0.0.1:11434 thrivestudio@192.168.50.29"
                    }
        except httpx.ConnectError:
            return {
                "tunnel_status": "inactive",
                "ollama_url": ollama_url,
                "port": port,
                "connection": "failed: Connection refused",
                "suggestion": "SSH tunnel is not active. Start it with: ssh -f -N -L 11436:127.0.0.1:11434 thrivestudio@192.168.50.29"
            }
        except Exception as e:
            return {
                "tunnel_status": "unknown",
                "ollama_url": ollama_url,
                "port": port,
                "connection": f"failed: {str(e)}",
                "suggestion": "Check SSH tunnel and Mac Studio connection"
            }
    except Exception as e:
        logger.error(f"Error checking tunnel status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

