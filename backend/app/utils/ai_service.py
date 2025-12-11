"""
AI Service utilities
Handles Perplexity API integration
"""
import os
import asyncio
import requests
import logging
from typing import Optional, List, Dict
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

async def query_perplexity(
    prompt: str, 
    conversation_history: Optional[List[Dict]] = None, 
    custom_system_message: Optional[str] = None
) -> str:
    """Query Perplexity API for AI responses
    
    Args:
        prompt: User prompt/question
        conversation_history: Previous conversation messages
        custom_system_message: Optional custom system message to override default
    """
    
    # Try PERPLEXITY_API_KEY first, then PPLX_API_KEY1 for backward compatibility
    api_key = settings.PERPLEXITY_API_KEY or os.getenv("PPLX_API_KEY1")
    if not api_key:
        logger.error("PERPLEXITY_API_KEY or PPLX_API_KEY1 environment variable is not set")
        raise ValueError("PERPLEXITY_API_KEY or PPLX_API_KEY1 environment variable is required")
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Use custom system message if provided, otherwise use default
    system_content = custom_system_message or (
        "You are Vector AI, a strategic business intelligence analyst for ThriveBrands. "
        "Analyze the provided business data and generate strategic marketing and business recommendations. "
        "All monetary values are in Euros (€). Be specific, data-driven, and actionable. "
        "Focus on growth opportunities, customer acquisition, retention strategies, and revenue optimization. "
        "Provide recommendations with clear reasoning, expected impact, and implementation channels."
    )
    
    messages = [{
        "role": "system",
        "content": system_content
    }]
    
    if conversation_history:
        messages.extend(conversation_history)
    
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": "sonar-pro",
        "messages": messages,
        "max_tokens": 4000  # Increased for longer responses (strategic recommendations, goals, etc.)
    }
    
    # Retry logic with exponential backoff
    max_retries = 3
    retry_delay = 1  # Start with 1 second
    
    for attempt in range(max_retries):
        try:
            # Use asyncio.to_thread to run synchronous requests in a thread pool
            def make_request():
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                response.raise_for_status()
                result = response.json()
                if 'choices' not in result or len(result['choices']) == 0:
                    raise ValueError("Invalid response format from Perplexity API")
                return result['choices'][0]['message']['content']
            
            # Run the synchronous request in a thread pool
            result = await asyncio.to_thread(make_request)
            logger.info(f"Perplexity API call successful on attempt {attempt + 1}")
            return result
            
        except requests.exceptions.Timeout as e:
            logger.warning(f"Perplexity API timeout on attempt {attempt + 1}/{max_retries}: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            else:
                logger.error(f"Perplexity API timeout after {max_retries} attempts")
                raise HTTPException(status_code=500, detail="AI service timeout. Please try again.")
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Perplexity API request error on attempt {attempt + 1}/{max_retries}: {str(e)}")
            if attempt < max_retries - 1:
                # Check if it's a rate limit or server error (5xx) - retry these
                if hasattr(e, 'response') and e.response is not None:
                    status_code = e.response.status_code
                    if status_code >= 500 or status_code == 429:  # Server error or rate limit
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                # For other errors, don't retry
                logger.error(f"Perplexity API non-retryable error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")
            else:
                logger.error(f"Perplexity API request failed after {max_retries} attempts: {str(e)}")
                raise HTTPException(status_code=500, detail=f"AI service error after retries: {str(e)}")
                
        except (KeyError, ValueError) as e:
            logger.error(f"Perplexity API response parsing error: {str(e)}")
            # Don't retry parsing errors
            raise HTTPException(status_code=500, detail=f"AI service response format error: {str(e)}")
            
        except Exception as e:
            logger.error(f"Unexpected Perplexity API error on attempt {attempt + 1}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

