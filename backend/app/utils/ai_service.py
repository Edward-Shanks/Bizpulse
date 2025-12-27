"""
AI Service utilities
Unified interface for all LLM providers (Perplexity, Ollama, vLLM)
"""
import logging
from typing import Optional, List, Dict, AsyncGenerator
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
        provider_name_actual = provider.get_provider_name()
        
        # Log which provider is being used (with clear formatting)
        logger.info("=" * 80)
        logger.info(f"🤖 USING LLM PROVIDER: {provider_name_actual.upper()}")
        logger.info(f"📍 Provider Type: {provider_name_actual}")
        if provider_name_actual == "ollama":
            import os
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11436")
            logger.info(f"🔗 Ollama URL: {ollama_url}")
        elif provider_name_actual == "perplexity":
            logger.info(f"🔗 Perplexity API: https://api.perplexity.ai")
        logger.info(f"💬 User Prompt Length: {len(prompt)} characters")
        logger.info("=" * 80)
        
        try:
            response = await provider.generate(
                prompt=prompt,
                conversation_history=conversation_history,
                custom_system_message=custom_system_message,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            logger.info("=" * 80)
            logger.info(f"✅ LLM RESPONSE RECEIVED from {provider_name_actual.upper()}")
            logger.info(f"📝 Response Length: {len(response)} characters")
            logger.info("=" * 80)
            
            return response
        except Exception as provider_error:
            # No automatic fallback - just raise the error
            # Users can manually switch LLM provider via LLM_PROVIDER environment variable
            logger.error("=" * 80)
            logger.error(f"❌ LLM PROVIDER FAILED: {str(provider_error)}")
            logger.error(f"💡 To switch providers, set LLM_PROVIDER environment variable to 'ollama', 'perplexity', or 'vllm'")
            logger.error("=" * 80)
            raise provider_error
    except Exception as e:
        logger.error(f"Error querying LLM: {str(e)}")
        raise

# Backward compatibility - uses configured provider by default
async def query_perplexity(
    prompt: str,
    conversation_history: Optional[List[Dict]] = None,
    custom_system_message: Optional[str] = None
) -> str:
    """
    Backward compatibility function
    Uses the configured LLM provider (can be Perplexity, Ollama, or vLLM)
    To force Perplexity, set provider_name="perplexity" or use query_llm with provider_name
    """
    return await query_llm(
        prompt=prompt,
        conversation_history=conversation_history,
        custom_system_message=custom_system_message
    )

# Convenience function for Ollama
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

async def stream_llm(
    prompt: str,
    conversation_history: Optional[List[Dict]] = None,
    custom_system_message: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4000,
    provider_name: Optional[str] = None,
    think: bool = False,
    **kwargs
) -> AsyncGenerator[Dict[str, str], None]:
    """
    Stream LLM response (unified interface for all providers)
    
    Yields dictionaries with:
    - "type": "thinking" or "content" or "done"
    - "data": the actual text chunk
    """
    try:
        provider = get_llm_provider(provider_name)
        provider_name_actual = provider.get_provider_name()
        
        logger.info("=" * 80)
        logger.info(f"🔄 STREAMING LLM PROVIDER: {provider_name_actual.upper()}")
        logger.info(f"📍 Provider Type: {provider_name_actual}")
        logger.info(f"💭 Think Mode: {think}")
        logger.info("=" * 80)
        
        async for chunk in provider.stream(
            prompt=prompt,
            conversation_history=conversation_history,
            custom_system_message=custom_system_message,
            temperature=temperature,
            max_tokens=max_tokens,
            think=think,
            **kwargs
        ):
            yield chunk
            
    except Exception as e:
        logger.error(f"Error streaming LLM: {str(e)}")
        # Yield error as content
        yield {
            "type": "error",
            "data": f"Error: {str(e)}"
        }

