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
        logger.info(f"🔍 PERPLEXITY: Starting generation request")
        logger.info(f"🔍 PERPLEXITY: Model: {self.model}")
        logger.info(f"🔍 PERPLEXITY: Temperature: {temperature}, Max Tokens: {max_tokens}")
        
        if not self.is_available():
            logger.error(f"🔍 PERPLEXITY: API key not available")
            raise HTTPException(
                status_code=503,
                detail="Perplexity provider not available (API key missing)"
            )
        
        logger.info(f"🔍 PERPLEXITY: API key available, making request...")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        system_content = custom_system_message or (
            "You are Vector AI, a strategic business intelligence analyst for ThriveBrands. "
            "Analyze the provided business data and generate strategic marketing and business recommendations. "
            "All monetary values are in Euros (€). Be specific, data-driven, and actionable. "
            "Focus on growth opportunities, customer acquisition, retention strategies, and revenue optimization. "
            "Provide recommendations with clear reasoning, expected impact, and implementation channels."
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
        # Perplexity streaming implementation (if needed)
        raise NotImplementedError("Perplexity streaming not yet implemented")

