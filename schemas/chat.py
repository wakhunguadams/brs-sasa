"""
BRS-SASA API Schemas - Production-Ready Design
Following OpenAI API patterns with BRS-specific extensions.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from uuid import uuid4


# ============================================
# Message Schemas (OpenAI-style)
# ============================================

class MessageContent(BaseModel):
    """Individual message in a conversation."""
    model_config = ConfigDict(extra="ignore")
    
    role: Literal["user", "assistant", "system"] = Field(
        description="The role of the message author"
    )
    content: str = Field(description="The content of the message")
    name: Optional[str] = Field(
        default=None,
        description="Optional name for the participant"
    )


class MessageMetadata(BaseModel):
    """Metadata attached to a message."""
    sources: List[str] = Field(default_factory=list, description="Source documents referenced")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score")
    model: Optional[str] = Field(default=None, description="Model used for generation")
    tokens_used: Optional[int] = Field(default=None, description="Tokens consumed")
    latency_ms: Optional[int] = Field(default=None, description="Response latency in ms")


class Message(BaseModel):
    """Complete message with metadata."""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique message ID")
    conversation_id: str = Field(description="Parent conversation ID")
    role: Literal["user", "assistant", "system"]
    content: str
    message_metadata: Optional[MessageMetadata] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict(from_attributes=True)


# ============================================
# Conversation Schemas
# ============================================

class Conversation(BaseModel):
    """A conversation/thread containing messages."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: Optional[str] = Field(default=None, description="Optional conversation title")
    status: Literal["active", "archived", "closed"] = Field(default="active")
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    conversation_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    """Request to create a new conversation."""
    title: Optional[str] = None
    system_message: Optional[str] = Field(
        default=None,
        description="Optional system prompt for this conversation"
    )
    conversation_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ConversationUpdate(BaseModel):
    """Request to update conversation status."""
    status: Optional[Literal["active", "archived", "closed"]] = None
    title: Optional[str] = None
    conversation_metadata: Optional[Dict[str, Any]] = None


class ConversationList(BaseModel):
    """List of conversations response."""
    conversations: List[Conversation]
    total: int
    has_more: bool


# ============================================
# Chat Completion Schemas (Main API)
# ============================================

class ChatCompletionRequest(BaseModel):
    """
    Request to create a chat completion.
    Follows OpenAI API pattern with BRS-specific extensions.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "messages": [
                    {"role": "user", "content": "How do I register a company in Kenya?"}
                ],
                "conversation_id": None,
                "provider": "gemini",
                "stream": False
            }
        }
    )
    
    # Required
    messages: List[MessageContent] = Field(
        description="List of messages in the conversation"
    )
    
    # Optional - Conversation management
    conversation_id: Optional[str] = Field(
        default=None,
        description="Existing conversation ID. If not provided, creates new conversation."
    )
    
    # Optional - Model configuration
    model: Optional[str] = Field(
        default="gemini-2.0-flash",
        description="Model to use for completion"
    )
    provider: Optional[Literal["gemini", "openai", "anthropic"]] = Field(
        default="gemini",
        description="LLM provider to use"
    )
    
    # Optional - Generation parameters
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        description="Maximum tokens to generate"
    )
    
    # Optional - Streaming
    stream: Optional[bool] = Field(
        default=False,
        description="Whether to stream the response via SSE"
    )
    
    # Optional - RAG configuration
    use_knowledge_base: Optional[bool] = Field(
        default=True,
        description="Whether to use RAG for knowledge retrieval"
    )
    top_k: Optional[int] = Field(
        default=5,
        description="Number of documents to retrieve for RAG"
    )


class ChatCompletionChoice(BaseModel):
    """A single completion choice."""
    index: int = 0
    message: MessageContent
    finish_reason: Literal["stop", "length", "error"] = "stop"


class ChatCompletionUsage(BaseModel):
    """Token usage statistics."""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class ChatCompletionResponse(BaseModel):
    """
    Response from chat completion.
    Follows OpenAI API pattern with BRS-specific extensions.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "chatcmpl-abc123",
                "object": "chat.completion",
                "created": 1706000000,
                "model": "gemini-2.0-flash",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "To register a company in Kenya..."
                    },
                    "finish_reason": "stop"
                }],
                "conversation_id": "conv-xyz789",
                "sources": ["CompaniesAct17of2015.pdf", "brs_extended_info.txt"],
                "confidence": 0.85
            }
        }
    )
    
    # Standard fields
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid4().hex[:12]}")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(default_factory=lambda: int(datetime.utcnow().timestamp()))
    model: str = "gemini-2.0-flash"
    
    # Response content
    choices: List[ChatCompletionChoice]
    usage: Optional[ChatCompletionUsage] = None
    
    # BRS-specific extensions
    conversation_id: str = Field(description="Conversation ID for follow-up messages")
    sources: List[str] = Field(default_factory=list, description="Referenced documents")
    confidence: float = Field(default=0.0, description="Answer confidence score")


# ============================================
# Streaming Schemas (SSE)
# ============================================

class DeltaContent(BaseModel):
    """Delta content for streaming."""
    role: Optional[str] = None
    content: Optional[str] = None


class StreamChoice(BaseModel):
    """Streaming choice with delta."""
    index: int = 0
    delta: DeltaContent
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    """Streaming chunk for SSE responses."""
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: List[StreamChoice]
    
    # BRS extensions - sent in final chunk
    conversation_id: Optional[str] = None
    sources: Optional[List[str]] = None
    confidence: Optional[float] = None


# ============================================
# Error Schemas
# ============================================

class ErrorDetail(BaseModel):
    """Error detail structure."""
    code: str
    message: str
    type: str
    param: Optional[str] = None


class APIError(BaseModel):
    """Standardized error response."""
    error: ErrorDetail
    request_id: str = Field(default_factory=lambda: str(uuid4()))


# ============================================
# Health & Status Schemas
# ============================================

class ComponentStatus(BaseModel):
    """Status of a system component."""
    status: Literal["healthy", "degraded", "unhealthy"]
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    components: Dict[str, ComponentStatus] = Field(default_factory=dict)


# ============================================
# Document Schemas
# ============================================

class DocumentUploadResponse(BaseModel):
    """Response after document upload."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str
    size: int
    status: Literal["processing", "ready", "failed"]
    chunks: Optional[int] = None
    message: Optional[str] = None
