from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
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
    Conversation Agent for handling general chat
    Following LangGraph 2026 best practices with proper message-based invocation
    """
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.logger = logger
        logger.info("Conversation agent initialized")
    
    async def generate_response(self, user_input: str, history: List[Dict[str, str]] = None) -> str:
        """
        Generate a conversational response with history awareness
        """
        try:
            messages = [SystemMessage(content=self._get_system_context())]
            
            # Add conversation history
            if history:
                for msg in history[-5:]:  # Last 5 exchanges
                    role = msg.get("role", "user")
                    if role == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    else:
                        messages.append(AIMessage(content=msg["content"]))
            
            # Add current user input
            messages.append(HumanMessage(content=user_input))
            
            # Invoke LLM
            response = await self.llm.ainvoke(messages)
            return response.content.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating conversation response: {str(e)}")
            return self._get_fallback_response(user_input)
    
    def _get_system_context(self) -> str:
        """
        Get the system context for the conversation
        """
        return (
            "You are BRS-SASA, an intelligent conversational AI platform for the Business Registration Service (BRS) of Kenya. "
            "You were developed by a team of developers working on this project to help users with business registration queries, "
            "explain legal documents, and provide general information about the BRS. "
            "You use advanced RAG (Retrieval-Augmented Generation) technology powered by LangGraph and Google's Gemini model. "
            "Always be professional yet approachable. "
            "If asked about your creation, clearly state that you are BRS-SASA, developed by the team working on this project for the BRS of Kenya, "
            "not a generic Google model. "
            "If you don't know something specific, suggest contacting BRS directly or asking a more specific question."
        )
    
    def _get_fallback_response(self, user_input: str) -> str:
        """Provide a fallback response when LLM fails"""
        user_input_lower = user_input.lower()
        
        if any(kw in user_input_lower for kw in ['hi', 'hello', 'hey', 'jambo']):
            return "Hello! I'm BRS-SASA, your AI assistant for the Business Registration Service of Kenya. How can I help you today?"
        
        return "I apologize, but I'm currently experiencing high traffic. Please try again in a moment, or ask a specific question about business registration in Kenya."