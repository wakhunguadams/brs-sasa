from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = None
    provider: Optional[str] = None  # LLM provider to use
    context: Optional[Dict[str, Any]] = None  # Additional context for the request

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[str]] = None
    confidence: Optional[float] = 0.0
    timestamp: Optional[datetime] = None

class DocumentUploadResponse(BaseModel):
    filename: str
    size: int
    status: str
    document_id: Optional[str] = None

class HealthCheckResponse(BaseModel):
    status: str
    timestamp: int
    service: str