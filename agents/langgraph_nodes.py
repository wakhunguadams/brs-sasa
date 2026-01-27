from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
import traceback

from core.state import BRSState, should_route_to_rag
from llm_factory.factory import LLMFactory
from agents.rag_agent import RAGAgent
from agents.conversation_agent import ConversationAgent
from core.logger import setup_logger

logger = setup_logger(__name__)

class BRSAgents:
    """
    Class containing all the agent implementations for the BRS-SASA system
    Following LangGraph best practices for state management
    """

    def __init__(self):
        self.llm_factory = LLMFactory()
        # We'll create agents per request to avoid state conflicts in concurrent usage

    def get_agents(self, llm_provider: str = "gemini"):
        """
        Get initialized agents for the specified LLM provider
        """
        llm = self.llm_factory.get_llm(llm_provider)
        rag_agent = RAGAgent(llm=llm)
        conversation_agent = ConversationAgent(llm=llm)

        return rag_agent, conversation_agent

async def rag_agent_node(state: BRSState) -> Dict[str, Any]:
    """
    RAG Agent node in the LangGraph workflow
    Following LangGraph best practices: treat as pure function, return partial state update
    """
    logger.info("Executing RAG Agent")

    try:
        # Get the appropriate agents (fresh instances to avoid state conflicts)
        rag_agent, _ = BRSAgents().get_agents(
            state.get("context", {}).get("llm_provider", "gemini")
        )

        # Prepare query - get the last user message if user_input is not set
        query = state.get("user_input", "")
        if not query and state.get("messages"):
            for msg in reversed(state["messages"]):
                if hasattr(msg, 'content') and hasattr(msg, 'type') and 'human' in msg.type.lower():
                    query = str(msg.content)
                    break

        # Query the knowledge base
        rag_response = await rag_agent.query_knowledge_base(
            query=query,
            top_k=5,
            context={"history": state.get("messages", [])}
        )

        # Return partial state update following LangGraph best practices
        return {
            "response": rag_response.response_text,
            "sources": rag_response.sources or [],
            "confidence": rag_response.confidence or 0.0,
            "retrieved_docs": rag_response.retrieved_chunks or [],
            "current_agent": "rag_agent",
            "agent_feedback": {
                "query_processed": query,
                "chunks_retrieved": len(rag_response.retrieved_chunks or []),
                "processing_time": "calculated_in_real_impl"
            },
            "query_type": "knowledge"
        }
    except Exception as e:
        logger.error(f"Error in RAG agent: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "response": "I encountered an error while searching our knowledge base. Please try again.",
            "current_agent": "rag_agent",
            "error_count": state.get("error_count", 0) + 1,
            "agent_feedback": {"error": str(e)}
        }

async def conversation_agent_node(state: BRSState) -> Dict[str, Any]:
    """
    Conversation Agent node in the LangGraph workflow
    Following LangGraph best practices: treat as pure function, return partial state update
    """
    logger.info("Executing Conversation Agent")

    try:
        # Get the appropriate agents (fresh instances to avoid state conflicts)
        _, conversation_agent = BRSAgents().get_agents(
            state.get("context", {}).get("llm_provider", "gemini")
        )

        # Prepare query - get the last user message if user_input is not set
        query = state.get("user_input", "")
        if not query and state.get("messages"):
            for msg in reversed(state["messages"]):
                if hasattr(msg, 'content') and hasattr(msg, 'type') and 'human' in msg.type.lower():
                    query = str(msg.content)
                    break

        # Process the message with conversation agent
        # Convert messages to the format expected by the conversation agent
        history = []
        for msg in state.get("messages", []):
            if hasattr(msg, 'content') and hasattr(msg, 'type'):
                role = "user" if 'human' in msg.type.lower() else "assistant"
                history.append({"role": role, "content": str(msg.content)})

        conv_response = await conversation_agent.process_message(
            message=query,
            history=history
        )

        # Return partial state update following LangGraph best practices
        return {
            "response": conv_response.response_text,
            "sources": conv_response.sources or [],
            "confidence": conv_response.confidence or 0.0,
            "current_agent": "conversation_agent",
            "agent_feedback": {
                "message_processed": query,
                "processing_time": "calculated_in_real_impl"
            },
            "query_type": "conversation"
        }
    except Exception as e:
        logger.error(f"Error in conversation agent: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "response": "I encountered an error while processing your request. Please try again.",
            "current_agent": "conversation_agent",
            "error_count": state.get("error_count", 0) + 1,
            "agent_feedback": {"error": str(e)}
        }

async def router_node(state: BRSState) -> Dict[str, str]:
    """
    Router node that determines which agent should handle the query
    Following LangGraph best practices
    """
    logger.info("Routing query to appropriate agent")

    try:
        routing_decision = should_route_to_rag(state)
        return {
            "current_agent": routing_decision.replace("_agent", ""),
            "query_type": "knowledge" if "rag" in routing_decision else "conversation"
        }
    except Exception as e:
        logger.error(f"Error in router: {str(e)}")
        # Default to conversation agent if routing fails
        return {
            "current_agent": "conversation",
            "query_type": "conversation",
            "error_count": state.get("error_count", 0) + 1
        }

async def response_formatter_node(state: BRSState) -> Dict[str, Any]:
    """
    Node that formats the final response for the user
    Following LangGraph best practices
    """
    logger.info("Formatting final response")

    try:
        # Create a formatted response that includes sources and confidence
        response_text = state.get("response", "")

        # Add sources if available
        sources = state.get("sources", [])
        if sources:
            formatted_sources = ", ".join(sources)
            response_text += f"\n\nSources: {formatted_sources}"

        # Add confidence indicator if available
        confidence = state.get("confidence", 0.0)
        if confidence > 0:
            response_text += f"\nConfidence: {confidence:.2f}"

        # Create AI message
        ai_message = AIMessage(content=response_text)

        # Return partial state update
        return {
            "response": response_text,
            "messages": [ai_message],
            "current_agent": "formatter"
        }
    except Exception as e:
        logger.error(f"Error in response formatter: {str(e)}")
        return {
            "response": "There was an error formatting the response.",
            "current_agent": "formatter",
            "error_count": state.get("error_count", 0) + 1
        }

async def error_handler_node(state: BRSState) -> Dict[str, Any]:
    """
    Node that handles errors in the workflow
    Following LangGraph best practices for error handling
    """
    logger.info("Handling error in workflow")

    error_msg = "I'm sorry, but I encountered an issue processing your request. Please try rephrasing your question."

    ai_message = AIMessage(content=error_msg)

    return {
        "response": error_msg,
        "messages": [ai_message],
        "current_agent": "error_handler",
        "error_count": state.get("error_count", 0) + 1
    }