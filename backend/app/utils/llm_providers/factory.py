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
        
        # Log provider initialization with clear formatting
        logger.info("=" * 80)
        logger.info(f"🔧 LLM PROVIDER INITIALIZED: {provider_name.upper()}")
        logger.info(f"📋 Available Providers: {', '.join(cls._providers.keys())}")
        logger.info(f"✅ Active Provider: {provider_name}")
        logger.info("=" * 80)
        
        return cls._current_provider
    
    @classmethod
    def list_available_providers(cls) -> list:
        """List all available provider names"""
        return list(cls._providers.keys())
    
    @classmethod
    async def get_available_provider(cls) -> Optional[LLMProvider]:
        """Get first available provider"""
        import asyncio
        for provider_name in cls._providers.keys():
            provider = cls.get_provider(provider_name)
            if hasattr(provider, 'is_available'):
                is_avail = provider.is_available()
                # Handle both sync and async is_available methods
                if asyncio.iscoroutinefunction(provider.is_available):
                    is_avail = await provider.is_available()
                elif asyncio.iscoroutine(is_avail):
                    is_avail = await is_avail
                if is_avail:
                    return provider
        return None

# Convenience function for backward compatibility
def get_llm_provider(provider_name: Optional[str] = None) -> LLMProvider:
    """Get LLM provider (convenience function)"""
    return LLMProviderFactory.get_provider(provider_name)

