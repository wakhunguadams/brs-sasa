from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging

from llm_factory.factory import BaseLLM
from core.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class AgentResponse:
    response_text: str
    sources: Optional[List[str]] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class ConversationAgent:
    """
    Agent responsible for handling conversation flow and context management
    """
    
    def __init__(self, llm: BaseLLM):
        self.llm = llm
        self.logger = logger
    
    async def process_message(
        self, 
        message: str, 
        history: List[Dict[str, str]], 
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Process a user message and return an appropriate response
        """
        try:
            # Build the prompt with conversation history and context
            prompt = self._build_prompt(message, history, context)
            
            # Generate response from LLM
            response_text = await self.llm.generate_response(prompt)
            
            # For now, return a basic response with confidence
            # In a real implementation, we would extract sources and confidence from the response
            return AgentResponse(
                response_text=response_text,
                sources=[],
                confidence=0.8,  # Placeholder confidence score
                metadata={"processed_by": "conversation_agent"}
            )
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            return AgentResponse(
                response_text="I'm sorry, I encountered an error processing your request. Please try again.",
                sources=[],
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    def _build_prompt(
        self, 
        message: str, 
        history: List[Dict[str, str]], 
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Build a prompt with conversation history and context
        """
        # Start with system context
        system_context = (
            "You are BRS-SASA, an AI assistant for the Business Registration Service (BRS) of Kenya. "
            "You help users with business registration queries, explain legal documents, "
            "provide statistics, and assist with public participation in legislation. "
            "Always be helpful, accurate, and cite sources when possible. "
            "If you don't know something, say so and suggest contacting BRS directly."
        )
        
        # Add any additional context
        if context:
            if "document_context" in context:
                system_context += f"\n\nAdditional context from documents: {context['document_context']}"
        
        # Build conversation history
        conversation_history = "\n".join([
            f"{msg['role'].title()}: {msg['content']}" 
            for msg in history[-5:]  # Use last 5 exchanges for context
        ])
        
        # Combine everything into the final prompt
        if conversation_history:
            prompt = (
                f"{system_context}\n\n"
                f"Previous conversation:\n{conversation_history}\n\n"
                f"User: {message}\n"
                f"Assistant:"
            )
        else:
            prompt = (
                f"{system_context}\n\n"
                f"User: {message}\n"
                f"Assistant:"
            )
        
        return prompt