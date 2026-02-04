from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from typing import List, Dict, Any, Optional

class BRSState(TypedDict):
    """
    State definition for the BRS-SASA multi-agent system following LangGraph best practices
    """
    # Conversation state - using add_messages reducer for accumulating messages
    messages: Annotated[list, add_messages]  # Chat history using LangGraph's built-in reducer

    # Query processing state
    user_input: str  # Current user input
    response: str  # Final response to user
    query_type: str  # Type of query ('knowledge', 'conversation', 'mixed')

    # Context and metadata
    context: Optional[Dict[str, Any]]  # Additional context for the query
    conversation_id: str  # Unique identifier for the conversation

    # Knowledge retrieval state
    retrieved_docs: Annotated[List[Dict[str, Any]], lambda x, y: x + y]  # Accumulate retrieved docs
    sources: Annotated[List[str], lambda x, y: list(set(x + y if y else []))]  # Deduplicate sources
    confidence: float  # Confidence score for the response

    # Agent tracking
    current_agent: str  # Currently active agent
    agent_feedback: Optional[Dict[str, Any]]  # Feedback from various agents
    error_count: int  # Count of errors in the current flow
    max_steps: int  # Maximum steps allowed to prevent infinite loops

def should_route_to_rag(state: BRSState) -> str:
    """
    Determine if the query should be routed to the RAG agent
    """
    # Get the last user message if available
    user_input = state.get("user_input", "")
    if not user_input and state.get("messages"):
        # Look for the last user message in the message history
        for msg in reversed(state["messages"]):
            if hasattr(msg, 'content') and hasattr(msg, 'type') and 'human' in msg.type.lower():
                user_input = str(msg.content)
                break

    user_input_lower = user_input.lower()

    # Keywords that indicate knowledge-based queries
    knowledge_query_keywords = [
        'registration', 'process', 'requirement', 'fee', 'law', 'act', 'legislation',
        'document', 'procedure', 'how to', 'steps', 'timeline', 'cost', 'price',
        'compare', 'explain', 'what is', 'when', 'where', 'who', 'why', 'statute',
        'regulation', 'section', 'chapter', 'subsection', 'provision', 'rule',
        'policy', 'guideline', 'application', 'form', 'certificate', 'license',
        'permit', 'compliance', 'obligation', 'right', 'duty', 'liability'
    ]

    is_knowledge_query = any(keyword in user_input_lower for keyword in knowledge_query_keywords)

    if is_knowledge_query:
        return "rag_agent"
    else:
        return "conversation_agent"

def route_query_type(state: BRSState) -> str:
    """
    Route to appropriate agent based on LLM-determined query type from router node
    """
    # Use the agent determined by the LLM-based router node
    current_agent = state.get("current_agent", "conversation_agent")
    return current_agent

def route_after_processing(state: BRSState) -> str:
    """
    Route after agent processing to determine next step
    """
    # Check if we have an error
    if state.get("error_count", 0) > state.get("max_steps", 5):
        return "error_handler"

    # Otherwise, return to response formatter
    return "response_formatter"

def route_after_validation(state: BRSState) -> str:
    """
    Route after validation to determine next step
    """
    if state.get("response"):
        return "response_formatter"
    else:
        return "error_handler"