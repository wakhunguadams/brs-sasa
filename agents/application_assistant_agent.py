"""
Application Assistant Agent - Helps users follow up on business registration applications
Uses the BRS Pesaflow API to look up registration status and provide guidance
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from tools.brs_status_checker import check_business_registration_status, get_registration_number_format
from tools.screenshot_analysis_tool import analyze_screenshot
from core.logger import setup_logger

logger = setup_logger(__name__)

# Tools specific to the application assistant
APPLICATION_TOOLS = [
    check_business_registration_status,
    get_registration_number_format,
    analyze_screenshot,  # Add screenshot analysis
]


@dataclass
class ApplicationResponse:
    response_text: str
    sources: Optional[List[str]] = None
    confidence: Optional[float] = None
    registration_number: Optional[str] = None


class ApplicationAssistantAgent:
    """
    Application Assistant Agent - helps users track and understand
    their business registration applications.
    """

    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.llm_with_tools = llm.bind_tools(APPLICATION_TOOLS)
        self.logger = logger
        logger.info("Application Assistant Agent initialized")

    async def process_query(
        self, user_input: str, history: List[Dict[str, str]] = None
    ) -> ApplicationResponse:
        """Process user query about their business registration application."""
        try:
            messages = [SystemMessage(content=self._get_system_prompt())]

            # Add conversation history
            if history:
                for msg in history[-5:]:
                    role = msg.get("role", "user")
                    if role == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    else:
                        messages.append(AIMessage(content=msg["content"]))

            messages.append(HumanMessage(content=user_input))

            # Let LLM decide if it needs to call the status check tool
            response = await self.llm_with_tools.ainvoke(messages)

            if response.tool_calls:
                self.logger.info(
                    f"Application assistant called {len(response.tool_calls)} tool(s)"
                )

                from langgraph.prebuilt import ToolNode

                tool_node = ToolNode(APPLICATION_TOOLS)

                messages.append(response)
                tool_results = await tool_node.ainvoke({"messages": messages})
                messages.extend(tool_results["messages"])

                # Get the final response with tool results context
                final_response = await self.llm.ainvoke(messages)
                response_text = self._extract_content(final_response.content)
                
                # If response is empty or too short, provide better fallback
                if not response_text or len(response_text.strip()) < 50:
                    self.logger.warning("Empty or very short response after tool use")
                    response_text = (
                        "I attempted to look up your registration but encountered an issue. "
                        "This could mean:\n\n"
                        "• The registration number might be incorrect\n"
                        "• The application is still being processed\n"
                        "• The record isn't in the system yet\n\n"
                        "Please verify your registration number and try again, or contact BRS directly:\n\n"
                        "📞 Phone: +254 11 112 7000\n"
                        "📧 Email: eo@brs.go.ke\n"
                        "🌐 Website: https://brs.go.ke/"
                    )
            else:
                response_text = self._extract_content(response.content)

            return ApplicationResponse(
                response_text=response_text,
                sources=["BRS Official API"],
                confidence=0.9,
            )

        except Exception as e:
            self.logger.error(f"Error in application assistant: {str(e)}")
            return ApplicationResponse(
                response_text=(
                    "I'm having trouble looking up your registration status right now. "
                    "Please try again in a moment, or contact BRS directly:\n\n"
                    "📞 Phone: +254 11 112 7000\n"
                    "📧 Email: eo@brs.go.ke\n"
                    "🌐 Website: https://brs.go.ke/"
                ),
                sources=[],
                confidence=0.0,
            )

    def _extract_content(self, content) -> str:
        """Extract text from response content."""
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

    def _get_system_prompt(self) -> str:
        return (
            "You are BRS-SASA Application Assistant, specializing in helping users "
            "track and understand their business registration applications with the "
            "Business Registration Service (BRS) of Kenya.\n\n"
            "You have access to THREE tools:\n"
            "1. check_business_registration_status - Look up a business by its registration number\n"
            "2. get_registration_number_format - Show users the format of registration numbers\n"
            "3. analyze_screenshot - Analyze screenshots of errors or issues users are facing\n\n"
            "WHEN THE USER PROVIDES A REGISTRATION NUMBER:\n"
            "- ALWAYS call check_business_registration_status with that number\n"
            "- Present the results clearly\n"
            "- Explain what the current status means in simple terms\n"
            "- Tell them what steps to take next\n\n"
            "WHEN THE USER UPLOADS A SCREENSHOT:\n"
            "- ALWAYS call analyze_screenshot to understand the issue\n"
            "- Extract error messages, identify the page, understand the problem\n"
            "- Provide specific troubleshooting steps based on what you see\n"
            "- Be empathetic - users are frustrated when they have issues\n\n"
            "WHEN THE USER ASKS ABOUT FORMATS:\n"
            "- Use get_registration_number_format to show them\n\n"
            "WHEN THE USER HASN'T PROVIDED A NUMBER YET:\n"
            "- Ask them to provide their registration number\n"
            "- Show them the format examples so they know what to look for\n"
            "- Common formats: PVT-XXXXXXX (private company), BN-XXXXXXX (business name)\n\n"
            "RESPONSE GUIDELINES:\n"
            "- Be clear and helpful\n"
            "- Always explain what each status means in plain language\n"
            "- Always provide actionable next steps\n"
            "- If no records are found, reassure the user and suggest alternatives\n"
            "- Be empathetic — users are often anxious about their applications\n"
            "- If the user asks something outside application tracking, politely redirect\n"
            "- Never expose API credentials or internal system details\n\n"
            "SCREENSHOT ANALYSIS:\n"
            "- When analyzing screenshots, extract ALL visible information\n"
            "- Identify error codes, error messages, form validation issues\n"
            "- Provide step-by-step solutions\n"
            "- If issue requires human help, recommend contacting BRS\n"
        )
