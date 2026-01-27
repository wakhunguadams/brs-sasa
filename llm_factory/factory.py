from abc import ABC, abstractmethod
from typing import Any, Optional
import logging

from core.config import settings
from core.logger import setup_logger

logger = setup_logger(__name__)

class BaseLLM(ABC):
    """
    Abstract base class for LLM providers
    """
    
    @abstractmethod
    async def generate_response(self, prompt: str, context: Optional[dict] = None) -> str:
        """
        Generate a response from the LLM
        """
        pass
    
    @abstractmethod
    async def embed_text(self, text: str) -> list:
        """
        Generate embeddings for the given text
        """
        pass

class GeminiLLM(BaseLLM):
    """
    Google Gemini LLM implementation using google-genai
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = "gemini-2.0-flash"
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini LLM")
        
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
        except ImportError:
            raise ImportError("Please install google-genai: pip install google-genai")
    
    async def generate_response(self, prompt: str, context: Optional[dict] = None) -> str:
        """
        Generate a response using Google Gemini
        """
        try:
            from google import genai
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Error generating response from Gemini: {str(e)}")
            raise
    
    async def embed_text(self, text: str) -> list:
        """
        Generate embeddings using Google Gemini
        """
        try:
            result = self.client.models.embed_content(
                model="text-embedding-004",
                contents=text
            )
            return result.embeddings[0].values
        except Exception as e:
            logger.error(f"Error generating embeddings from Gemini: {str(e)}")
            raise

class OpenAILLM(BaseLLM):
    """
    OpenAI LLM implementation
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model_name = "gpt-3.5-turbo"  # Default model
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI LLM")
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
    
    async def generate_response(self, prompt: str, context: Optional[dict] = None) -> str:
        """
        Generate a response using OpenAI
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {str(e)}")
            raise
    
    async def embed_text(self, text: str) -> list:
        """
        Generate embeddings using OpenAI
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            response = client.embeddings.create(
                input=text,
                model="text-embedding-ada-002"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embeddings from OpenAI: {str(e)}")
            raise

class AnthropicLLM(BaseLLM):
    """
    Anthropic Claude LLM implementation
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model_name = "claude-3-haiku-20240307"  # Default model
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic LLM")
        
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")
    
    async def generate_response(self, prompt: str, context: Optional[dict] = None) -> str:
        """
        Generate a response using Anthropic Claude
        """
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error generating response from Anthropic: {str(e)}")
            raise
    
    async def embed_text(self, text: str) -> list:
        """
        Generate embeddings using Anthropic (placeholder - Anthropic doesn't have embedding API yet)
        """
        # Note: Anthropic doesn't currently offer an embedding API
        # This is a placeholder that could use a different service or return dummy values
        logger.warning("Anthropic doesn't provide embedding API. Using placeholder.")
        return [0.0] * 1536  # Placeholder embedding size

class LLMFactory:
    """
    Factory class to create and manage LLM instances
    """
    
    def __init__(self):
        self._llms = {}
    
    def get_llm(self, provider: str = "gemini") -> BaseLLM:
        """
        Get an LLM instance based on the provider
        """
        if provider in self._llms:
            return self._llms[provider]
        
        if provider.lower() == "gemini":
            llm = GeminiLLM()
        elif provider.lower() == "openai":
            llm = OpenAILLM()
        elif provider.lower() == "anthropic":
            llm = AnthropicLLM()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        self._llms[provider] = llm
        return llm
    
    def register_llm(self, provider: str, llm_instance: BaseLLM):
        """
        Register a custom LLM instance
        """
        self._llms[provider] = llm_instance