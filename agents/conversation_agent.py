from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from tools.brs_tools import BRS_TOOLS
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
    Conversation Agent for handling general chat with web search capability
    Following LangGraph 2026 best practices with tool-calling for web search
    """
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        # Bind tools to LLM so it can search the web when needed
        self.llm_with_tools = llm.bind_tools(BRS_TOOLS)
        self.logger = logger
        logger.info("Conversation agent initialized with web search capability")
    
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
    
    async def generate_response(self, user_input: str, history: List[Dict[str, str]] = None) -> str:
        """
        Generate a conversational response with history awareness and web search capability
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
            
            # Invoke LLM with tools - it will decide if it needs to search
            response = await self._invoke_llm_with_retry(messages)
            
            # Check if LLM called any tools
            if response.tool_calls:
                self.logger.info(f"Conversation agent called {len(response.tool_calls)} tool(s)")
                
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
                final_response = await self._invoke_llm_final_with_retry(messages)
                return self._extract_content(final_response.content)
            else:
                # LLM responded directly without using tools
                return self._extract_content(response.content)
            
        except Exception as e:
            self.logger.error(f"Error generating conversation response: {str(e)}")
            return self._get_fallback_response(user_input)
    
    def _extract_content(self, content) -> str:
        """Extract text content from response (handles both string and list)"""
        if isinstance(content, str):
            return content.strip()
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
            return extracted_text.strip()
        else:
            return str(content).strip()
    
    def _get_system_context(self) -> str:
        """
        Get the system context for the conversation
        """
        return (
            "You are BRS-SASA, an intelligent conversational AI platform for the Business Registration Service (BRS) of Kenya. "
            "You were developed by a team of developers working on this project to help users with business registration queries, "
            "explain legal documents, and provide general information about the BRS. "
            "You use advanced RAG (Retrieval-Augmented Generation) technology powered by LangGraph and Google's Gemini model. "
            "\n\n"
            "You have access to SIX powerful tools:\n"
            "1. search_brs_knowledge - Search the local knowledge base for laws, regulations, fees, and processes\n"
            "2. search_web_duckduckgo - Search the web for current information like BRS leadership, revenue, statistics, news\n"
            "3. search_brs_news - Search for recent news and announcements about BRS\n"
            "4. scrape_brs_website - Scrape the official BRS website (https://brs.go.ke/) across ALL pages for current information about services, fees, statistics, etc.\n"
            "5. get_brs_contact_info - Get current BRS contact information from the official website\n"
            "6. get_brs_leadership - Get current BRS senior management and leadership team directly from the official website\n"
            "\n"
            "IMPORTANT TOOL SELECTION:\n"
            "- For 'Who is' questions about BRS directors, staff, leadership → use get_brs_leadership FIRST\n"
            "- For current BRS leadership, directors, management team → use get_brs_leadership\n"
            "- For other current website information (statistics, services, fees) → use scrape_brs_website\n"
            "- For laws, regulations, fees, processes from knowledge base → use search_brs_knowledge\n"
            "- For BRS contact info (phone, email, address) → use get_brs_contact_info\n"
            "- For recent news and updates → use search_brs_news\n"
            "- For general web information → use search_web_duckduckgo\n"
            "\n"
            "RESPONSE GUIDELINES - BE DIRECT AND CONVERSATIONAL:\n"
            "- Start with the answer, not with pleasantries\n"
            "- DO NOT start with 'Thank you for your question' or 'I'm doing great, thank you'\n"
            "- DO NOT be overly formal or polite\n"
            "- Get straight to the point\n"
            "- When asked 'Who are you?', respond: 'I am BRS-SASA, your AI assistant for the Business Registration Service of Kenya'\n"
            "- When asked 'Hello' or greeting, respond briefly and redirect to BRS topics\n"
            "- When you find information, present it confidently\n"
            "- If a tool doesn't find specific details, provide what you found and suggest where to get more info\n"
            "- Only suggest contacting BRS directly as a LAST resort after trying relevant tools\n"
            "- Never apologize for using tools or searching - that's your job!\n"
            "- Focus on what you CAN provide rather than what you can't\n"
            "\n"
            "When users ask about BRS leadership, directors, or staff, ALWAYS use get_brs_leadership FIRST. "
            "When users ask about contact information, use get_brs_contact_info. "
            "When users ask about statistics, services, fees or other website info, use scrape_brs_website. "
            "Be proactive in using your tools to help users.\n"
            "\n"
            "Always be professional yet approachable. "
            "If asked about your creation, clearly state that you are BRS-SASA, developed by the team working on this project for the BRS of Kenya."
        )
    
    def _get_fallback_response(self, user_input: str) -> str:
        """Provide a fallback response when LLM fails"""
        user_input_lower = user_input.lower()
        
        if any(kw in user_input_lower for kw in ['hi', 'hello', 'hey', 'jambo']):
            return "Hello! I'm BRS-SASA, your AI assistant for the Business Registration Service of Kenya. How can I help you today?"
        
        return "I'm currently experiencing high traffic. Please try again in a moment, or ask a specific question about business registration in Kenya."