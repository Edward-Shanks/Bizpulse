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

logger = logging.getLogger(__name__)

class OllamaProvider(LLMProvider):
    """Ollama provider implementation for local LLM"""
    
    def __init__(self):
        # Configuration from environment
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:32b-instruct")  # Use your existing model
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
        logger.info(f"🦙 OLLAMA: Starting generation request")
        logger.info(f"🦙 OLLAMA: Base URL: {self.base_url}")
        logger.info(f"🦙 OLLAMA: Model: {self.model}")
        logger.info(f"🦙 OLLAMA: Temperature: {temperature}, Max Tokens: {max_tokens}")
        
        # Check availability
        is_avail = await self.is_available()
        logger.info(f"🦙 OLLAMA: Service available: {is_avail}")
        
        if not is_avail:
            logger.error(f"🦙 OLLAMA: Service not available at {self.base_url}")
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

