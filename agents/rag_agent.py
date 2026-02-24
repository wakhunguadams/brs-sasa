from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

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
    
    def _extract_content(self, content) -> str:
        """Extract text content from response (handles both string and list)"""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Handle structured content like [{'type': 'text', 'text': 'actual text'}]
            extracted_text = ""
            for item in content:
                if isinstance(item, dict) and 'text' in item:
                    extracted_text += item.get('text', '')
                elif isinstance(item, str):
                    extracted_text += item
                else:
                    extracted_text += str(item)
            return extracted_text
        else:
            return str(content)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def _invoke_llm_with_retry(self, messages: List):
        """Invoke LLM with retry logic and exponential backoff"""
        return await self.llm_with_tools.ainvoke(messages)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def _invoke_llm_final_with_retry(self, messages: List):
        """Invoke final LLM call with retry logic"""
        return await self.llm.ainvoke(messages)
    
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
            
            # Invoke LLM with tools - it will decide if it needs to search (with retry)
            response = await self._invoke_llm_with_retry(messages)
            
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
                
                # Get final response from LLM after seeing tool results (with retry)
                final_response = await self._invoke_llm_final_with_retry(messages)
                response_text = self._extract_content(final_response.content)
                
                # Extract sources from tool results
                sources = self._extract_sources_from_tool_results(tool_results)
            else:
                # LLM responded directly without using tools
                response_text = self._extract_content(response.content)
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
                response_text="I encountered an error while searching the knowledge base. Please try again or rephrase your question.",
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
            "RESPONSE GUIDELINES:\n"
            "- Be confident and direct in your responses\n"
            "- When you find information in the knowledge base, present it clearly with sources\n"
            "- If the knowledge base doesn't have specific information, say what you found and suggest alternatives\n"
            "- Focus on providing helpful guidance rather than apologizing\n"
            "- Always cite your sources when providing information from the knowledge base\n\n"
            "If asked about your creation, respond that you are BRS-SASA, "
            "developed by a team for the Business Registration Service of Kenya."
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