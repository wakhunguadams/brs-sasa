"""
Feedback Collection Tool for Public Participation
Stores user feedback on legislation for later CRM integration
"""
from langchain_core.tools import tool
from typing import Optional
from core.database import get_db
from core.models import FeedbackModel
from core.logger import setup_logger

logger = setup_logger(__name__)

@tool
def collect_legislation_feedback(
    user_query: str,
    feedback_text: str,
    legislation_section: Optional[str] = None,
    sentiment: Optional[str] = None
) -> str:
    """
    Collect user feedback on legislation for public participation.
    
    Args:
        user_query: The original user query or question
        feedback_text: The user's feedback, comment, or suggestion
        legislation_section: Optional section of legislation being discussed
        sentiment: Optional sentiment (positive, negative, neutral, suggestion)
    
    Returns:
        Confirmation message
    """
    try:
        db = next(get_db())
        
        feedback = FeedbackModel(
            user_query=user_query,
            feedback_text=feedback_text,
            legislation_section=legislation_section,
            sentiment=sentiment or "neutral",
            feedback_metadata={}
        )
        
        db.add(feedback)
        db.commit()
        
        logger.info(f"Feedback collected: {feedback.id}")
        
        return (
            "Thank you for your feedback! Your input has been recorded and will be reviewed "
            "as part of the public participation process. Your feedback ID is: " + feedback.id
        )
        
    except Exception as e:
        logger.error(f"Error collecting feedback: {str(e)}")
        return "I encountered an error saving your feedback. Please try again or contact BRS directly."

@tool
async def search_legislation_knowledge(query: str) -> str:
    """
    Search the Trust Administration Bill 2025 and other legislation documents.
    Use this tool to find specific information about legislation being reviewed.
    
    Args:
        query: The search query about legislation
    
    Returns:
        Relevant information from legislation documents
    """
    try:
        from core.knowledge_base import knowledge_base
        
        # Search with legislation filter
        results = await knowledge_base.search(
            query=query,
            top_k=5,
            where={"type": "legislation"}
        )
        
        if not results:
            return "No specific information found in the legislation documents. Please rephrase your question."
        
        # Format results
        response_parts = []
        
        for chunk in results:
            source = chunk.get('source', 'Unknown')
            section = chunk.get('section', '')
            content = chunk.get('content', '')
            
            response_parts.append(f"**From {source}**")
            if section:
                response_parts.append(f"Section: {section}")
            response_parts.append(content)
            response_parts.append("")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Error searching legislation: {str(e)}")
        return "I encountered an error searching the legislation documents. Please try again."
