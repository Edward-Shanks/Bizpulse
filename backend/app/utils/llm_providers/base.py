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
        think: bool = False,
        **kwargs
    ) -> AsyncGenerator[Dict[str, str], None]:
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

