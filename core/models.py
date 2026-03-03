from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class ConversationModel(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=True)
    status = Column(String, default="active")
    conversation_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("MessageModel", back_populates="conversation", cascade="all, delete-orphan")

class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("ConversationModel", back_populates="messages")

class FeedbackModel(Base):
    __tablename__ = "feedback"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_query = Column(Text, nullable=False)
    legislation_section = Column(String, nullable=True)
    feedback_text = Column(Text, nullable=False)
    sentiment = Column(String, nullable=True)  # positive, negative, neutral, suggestion
    feedback_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class IssueReportModel(Base):
    __tablename__ = "issue_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    user_query = Column(Text, nullable=False)
    screenshot_path = Column(String, nullable=True)
    screenshot_url = Column(String, nullable=True)
    extracted_text = Column(Text, nullable=True)
    analysis_result = Column(JSON, nullable=True)
    issue_type = Column(String, nullable=True)  # error, navigation, form, payment, other
    status = Column(String, default="open")  # open, resolved, escalated
    resolution = Column(Text, nullable=True)
    escalated_to = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    conversation = relationship("ConversationModel", back_populates="issue_reports")

# Update ConversationModel to include relationship
ConversationModel.issue_reports = relationship("IssueReportModel", back_populates="conversation", cascade="all, delete-orphan")
