from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from core.state import BRSState, route_query_type, route_after_processing, route_after_validation
from agents.langgraph_nodes import (
    rag_agent_node,
    conversation_agent_node,
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
        self.memory = MemorySaver()
        self._build_workflow()

    def _build_workflow(self):
        """
        Build the LangGraph workflow with proper state management following best practices
        """
        # Create a state graph with the defined state
        workflow = StateGraph(BRSState)

        # Add nodes to the graph following LangGraph best practices
        workflow.add_node("router", router_node)
        workflow.add_node("rag_agent", rag_agent_node)
        workflow.add_node("conversation_agent", conversation_agent_node)
        workflow.add_node("response_formatter", response_formatter_node)
        workflow.add_node("error_handler", error_handler_node)

        # Set the entry point
        workflow.set_entry_point("router")

        # Add conditional edges from router to determine which agent to use
        workflow.add_conditional_edges(
            "router",
            route_query_type,
            {
                "rag_agent": "rag_agent",
                "conversation_agent": "conversation_agent"
            }
        )

        # Add conditional edges from agents to determine next step
        workflow.add_conditional_edges(
            "rag_agent",
            route_after_processing,
            {
                "response_formatter": "response_formatter",
                "error_handler": "error_handler"
            }
        )

        workflow.add_conditional_edges(
            "conversation_agent",
            route_after_processing,
            {
                "response_formatter": "response_formatter",
                "error_handler": "error_handler"
            }
        )

        # Add conditional edge from error handler
        workflow.add_conditional_edges(
            "error_handler",
            route_after_validation,
            {
                "response_formatter": "response_formatter",
                "error_handler": "error_handler"  # Allow retries if needed
            }
        )

        # Add simple edge from response formatter to end
        workflow.add_edge("response_formatter", END)

        # Compile the workflow with checkpointing for persistence
        self.workflow = workflow.compile(checkpointer=self.memory)

    async def invoke(self, inputs: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Invoke the workflow with the given inputs
        Following LangGraph best practices for error handling
        """
        if config is None:
            config = {"configurable": {"thread_id": inputs.get("conversation_id", "default_thread")}}

        try:
            result = await self.workflow.ainvoke(inputs, config=config)
            return result
        except Exception as e:
            logger.error(f"Error invoking workflow: {str(e)}")
            logger.error(f"Input state: {inputs}")
            raise

    async def stream(self, inputs: Dict[str, Any], config: Dict[str, Any] = None):
        """
        Stream the workflow execution
        Following LangGraph best practices
        """
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