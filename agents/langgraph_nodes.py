"""
LangGraph Nodes - Pure functions following 2026 best practices
Each node: (state) → partial_state_update
"""
from typing import Dict, Any
from core.state import BRSState
from langchain_core.messages import AIMessage, HumanMessage
from core.logger import setup_logger

logger = setup_logger(__name__)

# Lazy initialization of agents
_rag_agent = None
_conversation_agent = None

def _get_agents():
    """Lazy initialization of agents"""
    global _rag_agent, _conversation_agent
    
    if _rag_agent is None:
        from llm_factory.factory import LLMFactory
        from agents.rag_agent import RAGAgent
        from agents.conversation_agent import ConversationAgent
        from core.config import settings
        
        try:
            llm = LLMFactory.get_llm("gemini", api_key=settings.GEMINI_API_KEY)
            _rag_agent = RAGAgent(llm)
            _conversation_agent = ConversationAgent(llm)
            logger.info("Agents initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agents: {str(e)}")
            raise
    
    return _rag_agent, _conversation_agent


async def router_node(state: BRSState) -> Dict[str, Any]:
    """
    Router Node - Classify query intent using LLM
    Pure function: takes state, returns partial state update
    """
    try:
        user_input = state.get("user_input", "")
        
        if not user_input:
            # Try to get from messages
            messages = state.get("messages", [])
            if messages:
                last_msg = messages[-1]
                if hasattr(last_msg, 'content'):
                    user_input = str(last_msg.content)
        
        logger.info(f"Router processing: {user_input[:100]}...")
        
        # Use LLM for classification
        rag_agent, _ = _get_agents()
        llm = rag_agent.llm
        
        from langchain_core.messages import SystemMessage
        
        messages = [
            SystemMessage(content="Classify this query as 'knowledge' (needs BRS info) or 'conversation' (general chat). Respond with only one word."),
            HumanMessage(content=f"Query: {user_input}")
        ]

        response = await llm.ainvoke(messages)
        classification = response.content.strip().lower()
        
        if "knowledge" in classification:
            query_type = "knowledge"
            next_agent = "rag_agent"
            logger.info("Routing to RAG agent")
        else:
            query_type = "conversation"
            next_agent = "conversation_agent"
            logger.info("Routing to conversation agent")
        
        return {
            "query_type": query_type,
            "current_agent": next_agent
        }
        
    except Exception as e:
        logger.error(f"Router node error: {str(e)}")
        return {
            "query_type": "conversation",
            "current_agent": "conversation_agent",
            "error_count": state.get("error_count", 0) + 1
        }


async def rag_agent_node(state: BRSState) -> Dict[str, Any]:
    """
    RAG Agent Node - Invoke tool-calling RAG agent
    Pure function: takes state, returns partial state update
    """
    try:
        rag_agent, _ = _get_agents()
        
        user_input = state.get("user_input", "")
        
        # Convert messages to dict format for context
        history = []
        for msg in state.get("messages", []):
            if hasattr(msg, "content"):
                role = "assistant" if isinstance(msg, AIMessage) else "user"
                history.append({"role": role, "content": str(msg.content)})
        
        context = {"history": history}
        
        logger.info(f"RAG agent processing: {user_input[:100]}...")
        
        # Invoke RAG agent (which will use tools if needed)
        result = await rag_agent.query_knowledge_base(
            query=user_input,
            context=context
        )
        
        logger.info(f"RAG response generated with {len(result.sources or [])} sources")
        
        return {
            "response": result.response_text,
            "sources": result.sources or [],
            "confidence": result.confidence or 0.85,
            "current_agent": "rag_agent"
        }
        
    except Exception as e:
        logger.error(f"RAG agent error: {str(e)}")
        return {
            "response": "",
            "sources": [],
            "confidence": 0.0,
            "error_count": state.get("error_count", 0) + 1,
            "current_agent": "rag_agent"
        }


async def conversation_agent_node(state: BRSState) -> Dict[str, Any]:
    """
    Conversation Agent Node - Handle general conversation
    Pure function: takes state, returns partial state update
    """
    try:
        _, conversation_agent = _get_agents()
        
        user_input = state.get("user_input", "")
        
        # Convert messages to dict format for history
        history = []
        for msg in state.get("messages", []):
            if hasattr(msg, "content"):
                role = "assistant" if isinstance(msg, AIMessage) else "user"
                history.append({"role": role, "content": str(msg.content)})
                
        logger.info(f"Conversation agent processing: {user_input[:100]}...")
        
        # Generate response
        result = await conversation_agent.generate_response(user_input, history=history)
        
        logger.info("Conversation response generated")
        
        return {
            "response": result,
            "sources": [],
            "confidence": 0.9,
            "current_agent": "conversation_agent"
        }
        
    except Exception as e:
        logger.error(f"Conversation agent error: {str(e)}")
        return {
            "response": "I apologize, but I'm having trouble processing your request. Please try again.",
            "sources": [],
            "confidence": 0.0,
            "error_count": state.get("error_count", 0) + 1,
            "current_agent": "conversation_agent"
        }


async def response_formatter_node(state: BRSState) -> Dict[str, Any]:
    """
    Response Formatter Node - Format final response
    Pure function: takes state, returns partial state update
    """
    try:
        response = state.get("response", "")
        
        if not response:
            logger.warning("Empty response in formatter node")
            response = "I apologize, but I couldn't generate a response. Please try rephrasing your question."
        
        logger.info(f"Formatting response: {len(response)} characters")
        
        # Create AI message for history
        ai_message = AIMessage(content=response)
        
        return {
            "messages": [ai_message],
            "response": response
        }
        
    except Exception as e:
        logger.error(f"Response formatter error: {str(e)}")
        return {
            "response": state.get("response", "An error occurred while formatting the response."),
            "error_count": state.get("error_count", 0) + 1
        }


async def error_handler_node(state: BRSState) -> Dict[str, Any]:
    """
    Error Handler Node - Handle errors gracefully
    Pure function: takes state, returns partial state update
    """
    try:
        error_count = state.get("error_count", 0)
        max_steps = state.get("max_steps", 10)
        
        logger.warning(f"Error handler invoked (error count: {error_count}/{max_steps})")
        
        if error_count >= 3:
            logger.error("Maximum error count reached")
            return {
                "response": (
                    "I apologize, but I'm having trouble processing your request. "
                    "Please try again later or contact the Business Registration Service directly:\n\n"
                    "📞 Phone: +254 11 112 7000\n"
                    "📧 Email: eo@brs.go.ke\n"
                    "🌐 Website: https://brs.go.ke"
                ),
                "sources": [],
                "confidence": 0.0,
                "current_agent": "error_handler"
            }
        
        # Try to recover
        logger.info("Attempting recovery via conversation agent")
        return {
            "current_agent": "conversation_agent",
            "error_count": error_count
        }
        
    except Exception as e:
        logger.error(f"Error handler itself failed: {str(e)}")
        return {
            "response": "An unexpected error occurred. Please try again.",
            "sources": [],
            "confidence": 0.0,
            "current_agent": "error_handler"
        }
