"""
Feedback API Endpoint for Public Participation
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from core.database import get_db
from core.models import FeedbackModel
from core.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

class FeedbackCreate(BaseModel):
    user_query: str
    feedback_text: str
    legislation_section: Optional[str] = None
    sentiment: Optional[str] = "neutral"

class FeedbackResponse(BaseModel):
    id: str
    user_query: str
    feedback_text: str
    legislation_section: Optional[str]
    sentiment: str
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """
    Submit feedback on legislation
    """
    try:
        feedback_model = FeedbackModel(
            user_query=feedback.user_query,
            feedback_text=feedback.feedback_text,
            legislation_section=feedback.legislation_section,
            sentiment=feedback.sentiment,
            feedback_metadata={}
        )
        
        db.add(feedback_model)
        db.commit()
        db.refresh(feedback_model)
        
        logger.info(f"Feedback submitted: {feedback_model.id}")
        
        return feedback_model
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@router.get("/list", response_model=List[FeedbackResponse])
async def list_feedback(
    limit: int = 50,
    sentiment: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all feedback (for admin/review purposes)
    """
    try:
        query = db.query(FeedbackModel)
        
        if sentiment:
            query = query.filter(FeedbackModel.sentiment == sentiment)
        
        feedback_list = query.order_by(FeedbackModel.created_at.desc()).limit(limit).all()
        
        return feedback_list
        
    except Exception as e:
        logger.error(f"Error listing feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback")

@router.get("/stats")
async def feedback_stats(db: Session = Depends(get_db)):
    """
    Get feedback statistics
    """
    try:
        total = db.query(FeedbackModel).count()
        
        positive = db.query(FeedbackModel).filter(FeedbackModel.sentiment == "positive").count()
        negative = db.query(FeedbackModel).filter(FeedbackModel.sentiment == "negative").count()
        neutral = db.query(FeedbackModel).filter(FeedbackModel.sentiment == "neutral").count()
        suggestions = db.query(FeedbackModel).filter(FeedbackModel.sentiment == "suggestion").count()
        
        return {
            "total_feedback": total,
            "by_sentiment": {
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
                "suggestion": suggestions
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting feedback stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get feedback statistics")
