"""
Issue Report Agent - Handles visual issue reports via screenshots
Analyzes screenshots to identify problems and provide troubleshooting
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from tools.screenshot_analysis_tool import SCREENSHOT_ANALYSIS_TOOLS
from core.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class IssueReportResponse:
    response_text: str
    sources: Optional[List[str]] = None
    confidence: Optional[float] = None
    issue_type: Optional[str] = None
    escalation_needed: bool = False

class IssueReportAgent:
    """
    Issue Report Agent - Analyzes screenshots to identify and troubleshoot issues
    """
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.llm_with_tools = llm.bind_tools(SCREENSHOT_ANALYSIS_TOOLS)
        self.logger = logger
        logger.info("Issue Report Agent initialized")
    
    async def process_screenshot(
        self,
        image_path: str,
        user_description: str,
        history: List[Dict[str, str]] = None
    ) -> IssueReportResponse:
        """
        Process a screenshot to identify and troubleshoot issues
        """
        try:
            messages = [SystemMessage(content=self._get_system_prompt())]
            
            # Add conversation history
            if history:
                for msg in history[-3:]:
                    role = msg.get("role", "user")
                    if role == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    else:
                        messages.append(AIMessage(content=msg["content"]))
            
            # Add current request
            user_message = f"""User has uploaded a screenshot and described their issue as:
"{user_description}"

Screenshot path: {image_path}

Please analyze this screenshot using the analyze_screenshot tool to identify the issue and provide troubleshooting steps."""
            
            messages.append(HumanMessage(content=user_message))
            
            # Let LLM decide to call the screenshot analysis tool
            response = await self.llm_with_tools.ainvoke(messages)
            
            if response.tool_calls:
                self.logger.info(f"Issue report agent called {len(response.tool_calls)} tool(s)")
                
                from langgraph.prebuilt import ToolNode
                tool_node = ToolNode(SCREENSHOT_ANALYSIS_TOOLS)
                
                messages.append(response)
                tool_results = await tool_node.ainvoke({"messages": messages})
                messages.extend(tool_results["messages"])
                
                # Get final response with tool results
                final_response = await self.llm.ainvoke(messages)
                response_text = self._extract_content(final_response.content)
            else:
                # LLM didn't call tool, force it
                self.logger.warning("LLM didn't call screenshot tool, forcing analysis")
                from tools.screenshot_analysis_tool import analyze_screenshot
                
                analysis_result = await analyze_screenshot.ainvoke({
                    "image_path": image_path,
                    "user_description": user_description
                })
                
                # Parse and format the analysis
                import json
                analysis = json.loads(analysis_result)
                
                response_text = self._format_analysis(analysis)
            
            # Extract metadata from analysis
            import json
            try:
                # Try to find analysis in tool results
                analysis_data = {}
                for msg in messages:
                    if hasattr(msg, 'content') and isinstance(msg.content, str):
                        if msg.content.startswith('{') and 'page_identified' in msg.content:
                            analysis_data = json.loads(msg.content)
                            break
                
                issue_type = self._determine_issue_type(analysis_data)
                escalation_needed = analysis_data.get("escalation_needed", False)
                confidence = analysis_data.get("confidence_score", 0.8)
                
            except:
                issue_type = "unknown"
                escalation_needed = False
                confidence = 0.7
            
            return IssueReportResponse(
                response_text=response_text,
                sources=["Screenshot Analysis", "Gemini Vision"],
                confidence=confidence,
                issue_type=issue_type,
                escalation_needed=escalation_needed
            )
            
        except Exception as e:
            self.logger.error(f"Error in issue report agent: {str(e)}")
            return IssueReportResponse(
                response_text=(
                    "I encountered an error analyzing your screenshot. "
                    "Please describe your issue in text, or contact BRS directly:\n\n"
                    "📞 Phone: +254 11 112 7000\n"
                    "📧 Email: eo@brs.go.ke\n"
                    "🌐 Website: https://brs.go.ke/"
                ),
                sources=[],
                confidence=0.0,
                escalation_needed=True
            )
    
    def _extract_content(self, content) -> str:
        """Extract text from response content"""
        if isinstance(content, str):
            return content.strip()
        elif isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    parts.append(item["text"])
                elif isinstance(item, str):
                    parts.append(item)
                else:
                    parts.append(str(item))
            return "".join(parts).strip()
        return str(content).strip()
    
    def _format_analysis(self, analysis: Dict[str, Any]) -> str:
        """Format analysis results into user-friendly response"""
        if "error" in analysis:
            return f"""I encountered an issue analyzing the screenshot: {analysis['error']}

Please describe your issue in text, or contact BRS directly:
📞 Phone: +254 11 112 7000
📧 Email: eo@brs.go.ke
🌐 Website: https://brs.go.ke/"""
        
        response_parts = ["I've analyzed your screenshot. Here's what I found:\n"]
        
        if analysis.get("page_identified"):
            response_parts.append(f"**📍 Page:** {analysis['page_identified']}\n")
        
        if analysis.get("error_messages"):
            response_parts.append("**❌ Errors Found:**")
            for error in analysis["error_messages"]:
                response_parts.append(f"- {error}")
            response_parts.append("")
        
        if analysis.get("form_validation_errors"):
            response_parts.append("**⚠️ Form Issues:**")
            for error in analysis["form_validation_errors"]:
                response_parts.append(f"- **{error.get('field', 'Field')}:** {error.get('error', 'Error')}")
            response_parts.append("")
        
        if analysis.get("likely_cause"):
            response_parts.append(f"**🔍 Likely Cause:** {analysis['likely_cause']}\n")
        
        if analysis.get("troubleshooting_steps"):
            response_parts.append("**✅ How to Fix:**")
            for i, step in enumerate(analysis["troubleshooting_steps"], 1):
                response_parts.append(f"{i}. {step}")
            response_parts.append("")
        
        if analysis.get("escalation_needed"):
            response_parts.append("\n**📞 Need More Help?**")
            response_parts.append("Contact BRS directly:")
            response_parts.append("- Phone: +254 11 112 7000")
            response_parts.append("- Email: eo@brs.go.ke")
        
        return "\n".join(response_parts)
    
    def _determine_issue_type(self, analysis: Dict[str, Any]) -> str:
        """Determine issue type from analysis"""
        if analysis.get("error_messages"):
            if any("payment" in str(e).lower() for e in analysis["error_messages"]):
                return "payment"
            return "error"
        elif analysis.get("form_validation_errors"):
            return "form"
        elif "navigation" in str(analysis.get("user_intent", "")).lower():
            return "navigation"
        return "other"
    
    def _get_system_prompt(self) -> str:
        """System prompt for issue report agent"""
        return (
            "You are BRS-SASA Issue Report Assistant, specializing in analyzing screenshots "
            "to help users troubleshoot problems with the Business Registration Service (BRS) system.\n\n"
            
            "You have access to screenshot analysis tools:\n"
            "1. analyze_screenshot - Comprehensive screenshot analysis\n"
            "2. extract_error_code - Extract error codes and messages\n"
            "3. identify_brs_page - Identify which BRS page is shown\n\n"
            
            "WHEN USER UPLOADS A SCREENSHOT:\n"
            "1. ALWAYS call analyze_screenshot tool first\n"
            "2. Review the analysis results carefully\n"
            "3. Provide clear, actionable troubleshooting steps\n"
            "4. Be empathetic - users are frustrated when they have issues\n"
            "5. If the issue requires human help, recommend escalation\n\n"
            
            "RESPONSE FORMAT:\n"
            "- Start with what you found in the screenshot\n"
            "- Explain the error/issue in simple terms\n"
            "- Provide step-by-step solutions\n"
            "- Include BRS contact info if escalation needed\n"
            "- Be encouraging and supportive\n\n"
            
            "Remember: Screenshots provide valuable visual context. Use the tools to extract "
            "all relevant information and provide the best possible assistance."
        )
