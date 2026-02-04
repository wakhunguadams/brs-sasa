"""
LLM Factory - Multi-provider abstraction layer using LangChain
Supports: Gemini, OpenAI, Anthropic
"""
from typing import Optional, List, Any
import os
from core.logger import setup_logger
from langchain_core.language_models.chat_models import BaseChatModel

logger = setup_logger(__name__)

class LLMFactory:
    """Factory for creating LangChain ChatModel instances"""
    
    @staticmethod
    def get_llm(provider: str = "gemini", api_key: Optional[str] = None, model: Optional[str] = None) -> BaseChatModel:
        """
        Get a LangChain ChatModel instance for the specified provider
        """
        provider = provider.lower()
        
        if provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            key = api_key or os.getenv("GEMINI_API_KEY")
            if not key:
                raise ValueError("GEMINI_API_KEY not found in environment")
            
            return ChatGoogleGenerativeAI(
                model=model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                google_api_key=key,
                temperature=0.7,
                convert_system_message_to_human=True
            )
        
        elif provider == "openai":
            from langchain_openai import ChatOpenAI
            key = api_key or os.getenv("OPENAI_API_KEY")
            if not key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            
            return ChatOpenAI(
                model=model or "gpt-4-turbo",
                openai_api_key=key,
                temperature=0.7
            )
        
        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            
            return ChatAnthropic(
                model=model or "claude-3-sonnet-20240229",
                anthropic_api_key=key,
                temperature=0.7
            )
        
        else:
            raise ValueError(f"Unknown LLM provider: {provider}. Supported: gemini, openai, anthropic")

# Convenience function
def get_default_llm() -> Any:
    """Get the default LLM from environment configuration"""
    from core.config import settings
    return LLMFactory.get_llm(settings.DEFAULT_LLM_PROVIDER)
