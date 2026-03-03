from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from core.state import BRSState, route_query_type, route_after_processing, route_after_validation
from agents.langgraph_nodes import (
    rag_agent_node,
    conversation_agent_node,
    public_participation_agent_node,
    application_assistant_agent_node,
    router_node,
    response_formatter_node,
    error_handler_node
)
from core.logger import setup_logger

logger = setup_logger(__name__)

class BRSWorkflow:
    """
    Main LangGraph workflow for the BRS-SASA multi-agent system
    Following LangGraph best practices for state management and graph flow
    """

    def __init__(self):
        self.workflow = None
        self.memory = None

    async def initialize(self):
        """
        Initialize the workflow and its persistent storage
        """
        if self.workflow:
            return
            
        # Create a state graph with the defined state
        workflow = StateGraph(BRSState)

        # Add nodes to the graph following LangGraph best practices
        workflow.add_node("router", router_node)
        workflow.add_node("rag_agent", rag_agent_node)
        workflow.add_node("conversation_agent", conversation_agent_node)
        workflow.add_node("public_participation_agent", public_participation_agent_node)
        workflow.add_node("application_assistant_agent", application_assistant_agent_node)
        workflow.add_node("response_formatter", response_formatter_node)
        workflow.add_node("error_handler", error_handler_node)

        # Set the entry point
        workflow.set_entry_point("router")

        # Add conditional edges
        workflow.add_conditional_edges(
            "router", 
            route_query_type, 
            {
                "rag_agent": "rag_agent", 
                "conversation_agent": "conversation_agent",
                "public_participation_agent": "public_participation_agent",
                "application_assistant_agent": "application_assistant_agent",
                "error": "response_formatter",  # Go directly to formatter for errors
                "out_of_scope": "response_formatter"  # Go directly to formatter for out-of-scope
            }
        )
        workflow.add_conditional_edges("rag_agent", route_after_processing, {"response_formatter": "response_formatter", "error_handler": "error_handler"})
        workflow.add_conditional_edges("conversation_agent", route_after_processing, {"response_formatter": "response_formatter", "error_handler": "error_handler"})
        workflow.add_conditional_edges("public_participation_agent", route_after_processing, {"response_formatter": "response_formatter", "error_handler": "error_handler"})
        workflow.add_conditional_edges("application_assistant_agent", route_after_processing, {"response_formatter": "response_formatter", "error_handler": "error_handler"})
        workflow.add_conditional_edges("error_handler", route_after_validation, {"response_formatter": "response_formatter", "error_handler": "error_handler"})
        workflow.add_edge("response_formatter", END)

        # Initialize MemorySaver for conversation history
        self.memory = MemorySaver()
        self.workflow = workflow.compile(checkpointer=self.memory)
        
        logger.info("BRSWorkflow initialized with MemorySaver")

    async def close(self):
        """Close the persistent storage"""
        self.memory = None
        self.workflow = None

    async def invoke(self, inputs: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Invoke the workflow with the given inputs
        """
        if not self.workflow:
            await self.initialize()
            
        if config is None:
            config = {"configurable": {"thread_id": inputs.get("conversation_id", "default_thread")}}

        try:
            result = await self.workflow.ainvoke(inputs, config=config)
            return result
        except Exception as e:
            logger.error(f"Error invoking workflow: {str(e)}")
            raise

    async def stream(self, inputs: Dict[str, Any], config: Dict[str, Any] = None):
        """
        Stream the workflow execution
        """
        if not self.workflow:
            await self.initialize()
            
        if config is None:
            config = {"configurable": {"thread_id": inputs.get("conversation_id", "default_thread")}}

        try:
            async for chunk in self.workflow.astream(inputs, config=config):
                yield chunk
        except Exception as e:
            logger.error(f"Error streaming workflow: {str(e)}")
            raise

# Global workflow instance
brs_workflow = BRSWorkflow()