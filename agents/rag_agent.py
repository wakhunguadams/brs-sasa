from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from tools.brs_tools import BRS_TOOLS
from core.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class RAGResponse:
    response_text: str
    sources: Optional[List[str]] = None
    confidence: Optional[float] = None
    retrieved_chunks: Optional[List[Dict[str, Any]]] = None

class RAGAgent:
    """
    Tool-calling RAG Agent following LangGraph 2026 best practices
    
    Uses .bind_tools() to let the LLM autonomously decide when to search the knowledge base.
    Implements the ReAct pattern: Reason → Act (call tool) → Observe → Respond
    """

    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        # Bind tools to the LLM - this is the 2026 best practice
        self.llm_with_tools = llm.bind_tools(BRS_TOOLS)
        self.logger = logger
        logger.info("RAG Agent initialized with tool-calling capability")
    
    async def query_knowledge_base(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RAGResponse:
        """
        Query using tool-calling pattern - let LLM decide when to use search tool
        """
        try:
            # Rephrase query if we have conversation history
            rephrased_query = query
            if context and context.get("history"):
                rephrased_query = await self._rephrase_query(query, context.get("history"))
                self.logger.info(f"Rephrased query: {rephrased_query}")

            # Build messages for the LLM
            messages = [
                SystemMessage(content=self._get_system_prompt()),
                HumanMessage(content=rephrased_query)
            ]
            
            # Invoke LLM with tools - it will decide if it needs to search
            response = await self.llm_with_tools.ainvoke(messages)
            
            # Check if LLM called any tools
            if response.tool_calls:
                # LLM decided to use the search tool
                self.logger.info(f"LLM called {len(response.tool_calls)} tool(s)")
                
                # Execute the tool calls
                from langgraph.prebuilt import ToolNode
                tool_node = ToolNode(BRS_TOOLS)
                
                # Add the AI message with tool calls to history
                messages.append(response)
                
                # Execute tools
                tool_results = await tool_node.ainvoke({"messages": messages})
                
                # Add tool results to messages
                messages.extend(tool_results["messages"])
                
                # Get final response from LLM after seeing tool results
                final_response = await self.llm.ainvoke(messages)
                response_text = final_response.content
                
                # Extract sources from tool results
                sources = self._extract_sources_from_tool_results(tool_results)
            else:
                # LLM responded directly without using tools
                response_text = response.content
                sources = []
                self.logger.info("LLM responded without using tools")

            return RAGResponse(
                response_text=response_text,
                sources=sources,
                confidence=0.85,
                retrieved_chunks=[]
            )
            
        except Exception as e:
            self.logger.error(f"Error in RAG agent: {str(e)}")
            return RAGResponse(
                response_text="I'm sorry, I encountered an error while searching the knowledge base. Please try again.",
                sources=[],
                confidence=0.0,
                retrieved_chunks=[]
            )
    
    async def _rephrase_query(self, query: str, history: List[Dict[str, str]]) -> str:
        """
        Rephrase the user query based on conversation history to make it standalone
        """
        if not history:
            return query
            
        history_str = "\n".join([f"{m['role'].title()}: {m['content']}" for m in history[-3:]])
        
        messages = [
            SystemMessage(content="You are a query rephraser. Rephrase the follow-up question to be standalone."),
            HumanMessage(content=f"History:\n{history_str}\n\nFollow-up Question: {query}")
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            return response.content.strip()
        except Exception as e:
            self.logger.error(f"Error rephrasing query: {str(e)}")
            return query

    def _get_system_prompt(self) -> str:
        """
        System prompt for the RAG agent
        """
        return (
            "You are BRS-SASA, an AI assistant for the Business Registration Service (BRS) of Kenya. "
            "You help users with business registration queries, explain legal documents, and provide information about fees and processes.\n\n"
            "You have access to a knowledge base search tool. Use it when you need specific information about:\n"
            "- Business registration processes and requirements\n"
            "- Fees and costs\n"
            "- Legal acts and regulations\n"
            "- BRS contact information and services\n\n"
            "If asked about your creation, identity, or who created you, respond that you are BRS-SASA, "
            "developed by a team for the Business Registration Service of Kenya, not a generic model.\n\n"
            "Always cite your sources when providing information from the knowledge base. "
            "If you don't have enough information to answer accurately, say so and suggest contacting BRS directly."
        )
    
    def _extract_sources_from_tool_results(self, tool_results: Dict[str, Any]) -> List[str]:
        """
        Extract source citations from tool execution results
        """
        sources = []
        for msg in tool_results.get("messages", []):
            if hasattr(msg, 'content') and 'Source:' in str(msg.content):
                # Parse sources from tool output
                content = str(msg.content)
                for line in content.split('\n'):
                    if line.startswith('Source:'):
                        source = line.replace('Source:', '').strip()
                        if source and source not in sources:
                            sources.append(source)
        return sources