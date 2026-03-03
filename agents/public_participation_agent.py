"""
Public Participation Agent for Legislation Review
Helps users understand legislation, compare with other countries, and collect feedback
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from core.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class ParticipationResponse:
    response_text: str
    sources: Optional[List[str]] = None
    confidence: Optional[float] = None
    feedback_collected: bool = False

class PublicParticipationAgent:
    """
    Public Participation Agent for legislation review and feedback collection
    Uses RAG for legislation search and web search for international comparisons
    """
    
    def __init__(self, llm: BaseChatModel, tools: List):
        self.llm = llm
        self.llm_with_tools = llm.bind_tools(tools)
        self.logger = logger
        logger.info("Public Participation Agent initialized")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def _invoke_llm_with_retry(self, messages: List):
        """Invoke LLM with retry logic"""
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
    
    def _extract_content(self, content) -> str:
        """Extract text content from response"""
        if isinstance(content, str):
            return content.strip()
        elif isinstance(content, list):
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
    
    async def process_query(
        self,
        user_input: str,
        history: List[Dict[str, str]] = None
    ) -> ParticipationResponse:
        """
        Process user query about legislation with tool-calling capability
        """
        try:
            # Check if this is feedback/opinion - if so, force feedback collection
            opinion_keywords = ['support', 'concerned', 'concern', 'suggest', 'think', 'believe', 
                              'opinion', 'should', 'must', 'need to', 'recommend', 'propose',
                              'agree', 'disagree', 'oppose', 'favor', 'against', 'for', 'reduce',
                              'increase', 'change', 'improve', 'better', 'worse']
            
            # Also check for explicit feedback requests
            feedback_requests = ['record', 'save', 'submit', 'log', 'store', 'collect', 'feedback']
            
            user_input_lower = user_input.lower()
            is_opinion = any(keyword in user_input_lower for keyword in opinion_keywords)
            is_feedback_request = any(keyword in user_input_lower for keyword in feedback_requests)
            
            messages = [SystemMessage(content=self._get_system_prompt())]
            
            # Add conversation history
            if history:
                for msg in history[-5:]:
                    role = msg.get("role", "user")
                    if role == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    else:
                        messages.append(AIMessage(content=msg["content"]))
            
            # Add current user input
            messages.append(HumanMessage(content=user_input))
            
            # Check if this is a direct legislation question that requires tool use
            legislation_keywords = ['trust administration bill', 'trust act', 'trust bill', 
                                   'legislation', 'bill 2025', 'proposed law', 'draft law']
            is_legislation_query = any(keyword in user_input_lower for keyword in legislation_keywords)
            
            # Invoke LLM with tools
            response = await self._invoke_llm_with_retry(messages)
            
            # If LLM didn't call tools but this is clearly a legislation query, force tool use
            if not response.tool_calls and is_legislation_query and not is_opinion:
                self.logger.info("Legislation query detected but LLM didn't call tool - forcing search")
                
                # Manually call legislation search tool
                from tools.feedback_tool import search_legislation_knowledge
                
                try:
                    search_result = await search_legislation_knowledge.ainvoke({"query": user_input})
                    
                    # Add search result to context and ask LLM to generate response
                    messages.append(response)
                    from langchain_core.messages import ToolMessage
                    messages.append(ToolMessage(
                        content=search_result,
                        tool_call_id="forced_search",
                        name="search_legislation_knowledge"
                    ))
                    
                    # Get final response with search results
                    final_response = await self._invoke_llm_final_with_retry(messages)
                    response_text = self._extract_content(final_response.content)
                    
                    # Check if response is still empty
                    if not response_text or len(response_text.strip()) < 50:
                        response_text = (
                            "Based on the Trust Administration Bill 2025, I found relevant information. "
                            "However, I'm having trouble generating a complete response. "
                            "Could you ask about a specific aspect? For example:\n"
                            "- Registration requirements\n"
                            "- Trustee duties\n"
                            "- Penalties for non-compliance\n"
                            "- Comparison with other countries"
                        )
                    
                    sources = ["Trust Administration Bill 2025"]
                    feedback_collected = False
                    
                except Exception as e:
                    self.logger.error(f"Error in forced legislation search: {str(e)}")
                    response_text = self._extract_content(response.content)
                    if not response_text or len(response_text.strip()) < 50:
                        response_text = (
                            "I'm having trouble accessing the legislation documents right now. "
                            "Please try rephrasing your question or contact BRS directly for information "
                            "about the Trust Administration Bill 2025."
                        )
                    sources = []
                    feedback_collected = False
            
            # Check if LLM called any tools
            elif response.tool_calls:
                self.logger.info(f"Public participation agent called {len(response.tool_calls)} tool(s)")
                
                # Execute the tool calls
                from langgraph.prebuilt import ToolNode
                from tools.public_participation_tools import PUBLIC_PARTICIPATION_TOOLS
                tool_node = ToolNode(PUBLIC_PARTICIPATION_TOOLS)
                
                # Add the AI message with tool calls to history
                messages.append(response)
                
                # Execute tools
                tool_results = await tool_node.ainvoke({"messages": messages})
                
                # Add tool results to messages
                messages.extend(tool_results["messages"])
                
                # Get final response from LLM after seeing tool results
                final_response = await self._invoke_llm_final_with_retry(messages)
                response_text = self._extract_content(final_response.content)
                
                # Check if response is empty or too short
                if not response_text or len(response_text.strip()) < 50:
                    self.logger.warning("Empty or very short response from LLM after tool use")
                    response_text = (
                        "I searched for information to answer your question, but I'm having trouble "
                        "generating a complete response. This could be due to limited search results. "
                        "Could you try rephrasing your question or asking about a specific aspect? "
                        "For example, you could ask about specific provisions, registration requirements, "
                        "or trustee duties in the legislation."
                    )
                
                # Check if feedback was collected
                feedback_collected = any(
                    'collect_legislation_feedback' in str(tc.get('name', ''))
                    for tc in response.tool_calls
                )
                
                sources = self._extract_sources_from_tool_results(tool_results)
            
            # If this is an opinion or feedback request but LLM didn't call feedback tool, force it
            elif is_opinion or is_feedback_request:
                self.logger.info("Opinion/feedback request detected but LLM didn't call feedback tool - forcing collection")
                
                # If user says "record the feedback", look for their previous opinion in history
                feedback_text = user_input
                if is_feedback_request and not is_opinion and history:
                    # Look for the last user message that contained an opinion
                    for msg in reversed(history):
                        if msg.get("role") == "user":
                            msg_content = msg.get("content", "").lower()
                            if any(kw in msg_content for kw in opinion_keywords):
                                feedback_text = msg.get("content", user_input)
                                self.logger.info(f"Found previous opinion in history: {feedback_text[:50]}...")
                                break
                
                # Manually call feedback tool
                from tools.feedback_tool import collect_legislation_feedback
                
                # Determine sentiment
                sentiment = "neutral"
                feedback_lower = feedback_text.lower()
                if any(word in feedback_lower for word in ['support', 'agree', 'favor', 'good', 'excellent']):
                    sentiment = "positive"
                elif any(word in feedback_lower for word in ['concerned', 'concern', 'oppose', 'against', 'bad', 'poor']):
                    sentiment = "negative"
                elif any(word in feedback_lower for word in ['suggest', 'recommend', 'propose', 'should', 'could', 'reduce', 'increase', 'change']):
                    sentiment = "suggestion"
                
                # Call feedback tool
                feedback_result = collect_legislation_feedback.invoke({
                    "user_query": feedback_text,
                    "feedback_text": feedback_text,
                    "legislation_section": None,
                    "sentiment": sentiment
                })
                
                # Generate response acknowledging feedback
                response_text = (
                    f"Thank you for your feedback on the legislation. {feedback_result}\n\n"
                    f"Your input is valuable for the public participation process and will be "
                    f"reviewed by policy makers."
                )
                
                sources = []
                feedback_collected = True
            
            else:
                # LLM responded directly without using tools
                response_text = self._extract_content(response.content)
                sources = []
                feedback_collected = False
                self.logger.info("Public participation agent responded without using tools")
            
            return ParticipationResponse(
                response_text=response_text,
                sources=sources,
                confidence=0.85,
                feedback_collected=feedback_collected
            )
            
        except Exception as e:
            self.logger.error(f"Error in public participation agent: {str(e)}")
            return ParticipationResponse(
                response_text="I encountered an error processing your request. Please try again or contact BRS directly.",
                sources=[],
                confidence=0.0,
                feedback_collected=False
            )
    
    def _get_system_prompt(self) -> str:
        """System prompt for the public participation agent"""
        return (
            "You are BRS-SASA Public Participation Assistant for the Business Registration Service (BRS) of Kenya. "
            "Your role is to help citizens understand proposed legislation, particularly the Trust Administration Bill 2025, "
            "and facilitate public participation in the legislative process.\n\n"
            
            "You have access to FOUR powerful tools:\n"
            "1. search_legislation_knowledge - Search the Trust Administration Bill 2025 and other legislation documents\n"
            "2. search_web_duckduckgo - Search the web to compare Kenya's legislation with other countries\n"
            "3. search_brs_news - Find recent news about legislation and BRS updates\n"
            "4. collect_legislation_feedback - Collect user feedback, comments, and suggestions on legislation\n\n"
            
            "YOUR RESPONSIBILITIES:\n"
            "1. EXPLAIN LEGISLATION: Break down complex legal language into simple terms that the public can understand\n"
            "2. JURISDICTION REVIEW: Compare Kenya's proposed laws with similar laws in other countries\n"
            "   - PRIORITIZE neighboring East African countries: Uganda, Tanzania, Rwanda, Ethiopia, Somalia\n"
            "   - Also compare with: UK, US, South Africa, India, and other Commonwealth countries\n"
            "   - When comparing, search for specific aspects like 'Uganda trust laws', 'Tanzania trust legislation'\n"
            "3. ANSWER QUESTIONS: Help users understand specific sections, requirements, and implications\n"
            "4. COLLECT FEEDBACK: When users express opinions, concerns, or suggestions, use the feedback tool to record them\n\n"
            
            "TOOL SELECTION GUIDELINES - CRITICAL:\n"
            "- For ANY question about the Trust Administration Bill → ALWAYS use search_legislation_knowledge FIRST\n"
            "- For comparing with other countries' laws → use search_web_duckduckgo with specific country names\n"
            "- For recent updates and news → use search_brs_news\n"
            "- When user expresses feedback, opinion, or suggestion → use collect_legislation_feedback\n\n"
            
            "MANDATORY TOOL USE:\n"
            "- If user asks 'Explain the Trust Bill' → YOU MUST call search_legislation_knowledge\n"
            "- If user asks 'What does the bill say about X' → YOU MUST call search_legislation_knowledge\n"
            "- If user asks 'Compare with Uganda' → YOU MUST call search_web_duckduckgo\n"
            "- If user says 'I think/support/oppose' → YOU MUST call collect_legislation_feedback\n"
            "- NEVER respond about legislation without calling search_legislation_knowledge first\n\n"
            
            "FEEDBACK COLLECTION - CRITICAL:\n"
            "- When user says 'I support', 'I'm concerned', 'I suggest', 'I think', 'I believe' → ALWAYS call collect_legislation_feedback\n"
            "- When user says 'record feedback', 'save feedback', 'submit feedback', 'log feedback' → ALWAYS call collect_legislation_feedback\n"
            "- When user says 'record the feedback' → Look at conversation history to find their previous opinion/suggestion and record it\n"
            "- The tool will automatically thank the user and provide a feedback ID\n"
            "- After calling the feedback tool, acknowledge that their input was recorded\n"
            "- DO NOT provide your own feedback confirmation - let the tool handle it\n"
            "- Include the feedback ID in your response when available\n\n"
            
            "RESPONSE STYLE - IMPORTANT:\n"
            "- Be direct and conversational - get straight to the answer\n"
            "- DON'T start with 'Thank you for your question' or similar pleasantries\n"
            "- DON'T be overly formal or polite - be natural and helpful\n"
            "- Start directly with the information: 'Kenya's Trust Administration Bill...' or 'Here's how they compare...'\n"
            "- Use simple language - avoid legal jargon when possible\n"
            "- Break down complex topics into clear points\n"
            "- When comparing countries, highlight key similarities and differences\n"
            "- If web search returns limited results, acknowledge this briefly and provide what you found\n"
            "- NEVER return empty responses - always provide some helpful information\n"
            "- If you can't find specific information, suggest alternatives briefly\n"
            "- Be neutral and objective when presenting legislation\n\n"
            
            "HANDLING LIMITED SEARCH RESULTS:\n"
            "- If web search doesn't return useful results, briefly explain what you searched for\n"
            "- Provide general information about trust law principles that might apply\n"
            "- Suggest the user contact BRS directly for specific comparisons\n"
            "- Offer to search for related topics or different aspects\n\n"
            
            "FEEDBACK COLLECTION:\n"
            "- When collecting feedback, the tool will thank the user automatically\n"
            "- You just need to acknowledge their input was recorded\n"
            "- Sentiments: 'positive' (support), 'negative' (concern/opposition), 'neutral' (question/clarification), 'suggestion' (improvement idea)\n\n"
            
            "Remember: You're facilitating democratic participation. Be helpful, direct, and accessible. "
            "Make legislation easy to understand without being condescending. "
            "ALWAYS use tools when appropriate - don't try to answer from memory alone."
        )
    
    def _extract_sources_from_tool_results(self, tool_results: Dict[str, Any]) -> List[str]:
        """Extract source citations from tool execution results"""
        sources = []
        for msg in tool_results.get("messages", []):
            if hasattr(msg, 'content'):
                content = str(msg.content)
                # Extract sources from markdown-style references
                if '**From ' in content:
                    for line in content.split('\n'):
                        if line.startswith('**From '):
                            source = line.replace('**From ', '').replace('**', '').strip()
                            if source and source not in sources:
                                sources.append(source)
        return sources
