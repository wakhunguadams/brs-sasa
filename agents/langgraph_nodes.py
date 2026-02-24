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
_public_participation_agent = None

def _get_agents():
    """Lazy initialization of agents"""
    global _rag_agent, _conversation_agent, _public_participation_agent
    
    if _rag_agent is None:
        from llm_factory.factory import LLMFactory
        from agents.rag_agent import RAGAgent
        from agents.conversation_agent import ConversationAgent
        from agents.public_participation_agent import PublicParticipationAgent
        from tools.public_participation_tools import PUBLIC_PARTICIPATION_TOOLS
        from core.config import settings
        
        try:
            llm = LLMFactory.get_llm("gemini", api_key=settings.GEMINI_API_KEY)
            _rag_agent = RAGAgent(llm)
            _conversation_agent = ConversationAgent(llm)
            _public_participation_agent = PublicParticipationAgent(llm, PUBLIC_PARTICIPATION_TOOLS)
            logger.info("Agents initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agents: {str(e)}")
            raise
    
    return _rag_agent, _conversation_agent, _public_participation_agent


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
        
        # Validate input
        from core.input_validation import InputValidator
        
        is_valid, sanitized_input, error_message = InputValidator.validate(user_input)
        
        if not is_valid:
            logger.warning(f"Invalid input: {error_message}")
            return {
                "query_type": "error",
                "current_agent": "conversation_agent",
                "response": error_message,
                "error_count": state.get("error_count", 0) + 1
            }
        
        # Check if out of scope
        is_out_of_scope, out_of_scope_message = InputValidator.is_out_of_scope(sanitized_input)
        
        if is_out_of_scope:
            logger.info(f"Out of scope query: {sanitized_input[:50]}...")
            return {
                "query_type": "out_of_scope",
                "current_agent": "conversation_agent",
                "response": out_of_scope_message,
                "error_count": 0
            }
        
        # Use sanitized input
        user_input = sanitized_input
        
        logger.info(f"Router processing: {user_input[:100]}...")
        
        # Use LLM for classification - NO pre-checks, let LLM decide
        rag_agent, _, _ = _get_agents()
        llm = rag_agent.llm
        
        from langchain_core.messages import SystemMessage
        
        messages = [
            SystemMessage(content=(
                "Classify this query into ONE of these categories:\n"
                "- 'legislation' - Questions about Trust Administration Bill, legislation review, public participation, feedback on laws\n"
                "- 'knowledge' - Questions about BRS business registration, fees, processes, legal documents (NOT current info)\n"
                "- 'conversation' - General chat, greetings, identity questions, small talk, CURRENT information (who is, what is, current leader, phone number, office hours, weather, jokes)\n\n"
                "KEY DIFFERENTIATORS:\n"
                "- 'Who is' questions → conversation (current info)\n"
                "- 'What is' questions → conversation (current info)\n"
                "- 'How do I' questions → knowledge (processes)\n"
                "- 'What are the' questions → knowledge (fees, requirements)\n"
                "- 'Is this' questions → conversation (opinion/clarification)\n"
                "- 'Tell me about' questions → conversation (general info)\n\n"
                "Keywords for 'legislation': trust, bill, law, legislation, public participation, feedback, jurisdiction, compare laws, Section, concerned about, suggest, opinion, think should\n"
                "Keywords for 'knowledge': register, business, company, fee, cost, process, requirements, documents, how to, steps, timeline, company type\n"
                "Keywords for 'conversation': hello, hi, who is, what is, who are you, who created, greetings, phone, email, address, hours, location, news, revenue, weather, joke\n\n"
                "IMPORTANT: If query contains opinion/feedback words (concerned, suggest, think, believe, opinion) about legislation/trust/bill → classify as 'legislation'\n\n"
                "Respond with only ONE word: 'legislation', 'knowledge', or 'conversation'."
            )),
            HumanMessage(content=f"Query: {user_input}")
        ]

        response = await llm.ainvoke(messages)
        classification = response.content.strip().lower()
        
        if "legislation" in classification:
            query_type = "legislation"
            next_agent = "public_participation_agent"
            logger.info("Routing to public participation agent")
        elif "knowledge" in classification:
            query_type = "knowledge"
            next_agent = "rag_agent"
            logger.info("Routing to RAG agent")
        else:
            query_type = "conversation"
            next_agent = "conversation_agent"
            logger.info("Routing to conversation agent")
        
        return {
            "query_type": query_type,
            "current_agent": next_agent,
            "user_input": user_input  # Use sanitized input
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
        rag_agent, _, _ = _get_agents()
        
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
        _, conversation_agent, _ = _get_agents()
        
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
            "response": "I'm having trouble processing your request. Please try again or rephrase your question.",
            "sources": [],
            "confidence": 0.0,
            "error_count": state.get("error_count", 0) + 1,
            "current_agent": "conversation_agent"
        }


async def public_participation_agent_node(state: BRSState) -> Dict[str, Any]:
    """
    Public Participation Agent Node - Handle legislation queries and feedback
    Pure function: takes state, returns partial state update
    """
    try:
        _, _, public_participation_agent = _get_agents()
        
        user_input = state.get("user_input", "")
        
        # Convert messages to dict format for history
        history = []
        for msg in state.get("messages", []):
            if hasattr(msg, "content"):
                role = "assistant" if isinstance(msg, AIMessage) else "user"
                history.append({"role": role, "content": str(msg.content)})
        
        logger.info(f"Public participation agent processing: {user_input[:100]}...")
        
        # Process query
        result = await public_participation_agent.process_query(user_input, history=history)
        
        logger.info(f"Public participation response generated (feedback collected: {result.feedback_collected})")
        
        return {
            "response": result.response_text,
            "sources": result.sources or [],
            "confidence": result.confidence or 0.85,
            "current_agent": "public_participation_agent"
        }
        
    except Exception as e:
        logger.error(f"Public participation agent error: {str(e)}")
        return {
            "response": "I'm having trouble processing your legislation query. Please try again or contact BRS directly.",
            "sources": [],
            "confidence": 0.0,
            "error_count": state.get("error_count", 0) + 1,
            "current_agent": "public_participation_agent"
        }


async def response_formatter_node(state: BRSState) -> Dict[str, Any]:
    """
    Response Formatter Node - Format final response
    Pure function: takes state, returns partial state update
    """
    try:
        response = state.get("response", "")
        query_type = state.get("query_type", "")
        
        # If response already set (from validation), use it
        if response and query_type in ["error", "out_of_scope"]:
            logger.info(f"Using pre-set response for {query_type}")
            ai_message = AIMessage(content=response)
            return {
                "messages": [ai_message],
                "response": response
            }
        
        if not response:
            logger.warning("Empty response in formatter node")
            response = "I couldn't generate a response. Please try rephrasing your question or ask about business registration services."
        
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
                    "I'm having trouble processing your request. "
                    "Please try again later or contact the Business Registration Service directly:\n\n"
                    "📞 Phone: +254 11 112 7000\n"
                    "📧 Email: eo@brs.go.ke\n"
                    "🌐 Website: https://brs.go.ke/"
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
