"""
BRS-SASA Chat API - Production-Ready Endpoints
Following industry best practices: OpenAI-compatible, SSE streaming, conversation management.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Header, Query
from fastapi.responses import StreamingResponse
from typing import Dict, Optional, AsyncGenerator, List
import json
import logging
import uuid
import time
import asyncio
from datetime import datetime

from schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionChunk,
    StreamChoice,
    DeltaContent,
    MessageContent,
    Message,
    MessageMetadata,
    Conversation,
    ConversationCreate,
    ConversationUpdate,
    ConversationList,
    ErrorDetail,
    APIError,
)
from core.workflow import brs_workflow
from core.state import BRSState
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from core.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

# In-memory conversation store (replace with Redis/PostgreSQL in production)
conversations: Dict[str, Conversation] = {}


# ============================================
# Helper Functions
# ============================================

def generate_request_id() -> str:
    """Generate unique request ID for tracing."""
    return f"req-{uuid.uuid4().hex[:16]}"


def generate_completion_id() -> str:
    """Generate unique completion ID."""
    return f"chatcmpl-{uuid.uuid4().hex[:12]}"


def messages_to_langchain(messages: List[MessageContent]) -> list:
    """Convert API messages to LangChain format."""
    lc_messages = []
    for msg in messages:
        if msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            lc_messages.append(AIMessage(content=msg.content))
        elif msg.role == "system":
            lc_messages.append(SystemMessage(content=msg.content))
    return lc_messages


async def invoke_workflow(
    messages: List[MessageContent],
    conversation_id: str,
    provider: str = "gemini"
) -> Dict:
    """Invoke the LangGraph workflow and return results."""
    
    lc_messages = messages_to_langchain(messages)
    user_input = messages[-1].content if messages else ""
    
    initial_state: BRSState = {
        "messages": lc_messages,
        "user_input": user_input,
        "response": "",
        "conversation_id": conversation_id,
        "context": {"llm_provider": provider},
        "sources": [],
        "confidence": 0.0,
        "query_type": "unknown",
        "retrieved_docs": [],
        "agent_feedback": {},
        "current_agent": "router",
        "error_count": 0,
        "max_steps": 10
    }
    
    result = await brs_workflow.invoke(
        initial_state,
        config={"configurable": {"thread_id": conversation_id}}
    )
    
    return result


async def stream_workflow(
    messages: List[MessageContent],
    conversation_id: str,
    provider: str = "gemini",
    model: str = "gemini-2.0-flash"
) -> AsyncGenerator[str, None]:
    """Stream workflow results as SSE events."""
    
    completion_id = generate_completion_id()
    created = int(time.time())
    
    try:
        # Invoke workflow (TODO: use astream for true token streaming)
        result = await invoke_workflow(messages, conversation_id, provider)
        
        response_text = result.get("response", "")
        sources = result.get("sources", [])
        confidence = result.get("confidence", 0.0)
        
        # Stream initial role
        initial_chunk = ChatCompletionChunk(
            id=completion_id,
            created=created,
            model=model,
            choices=[StreamChoice(
                index=0,
                delta=DeltaContent(role="assistant"),
                finish_reason=None
            )]
        )
        yield f"data: {initial_chunk.model_dump_json()}\n\n"
        
        # Stream content in chunks for real-time feel
        chunk_size = 20  # Characters per chunk
        for i in range(0, len(response_text), chunk_size):
            chunk_text = response_text[i:i + chunk_size]
            chunk = ChatCompletionChunk(
                id=completion_id,
                created=created,
                model=model,
                choices=[StreamChoice(
                    index=0,
                    delta=DeltaContent(content=chunk_text),
                    finish_reason=None
                )]
            )
            yield f"data: {chunk.model_dump_json()}\n\n"
            await asyncio.sleep(0.02)  # Small delay for streaming effect
        
        # Send final chunk with metadata
        final_chunk = ChatCompletionChunk(
            id=completion_id,
            created=created,
            model=model,
            choices=[StreamChoice(
                index=0,
                delta=DeltaContent(),
                finish_reason="stop"
            )],
            conversation_id=conversation_id,
            sources=sources,
            confidence=confidence
        )
        yield f"data: {final_chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Streaming error: {str(e)}")
        error_data = {"error": {"message": str(e), "type": "server_error"}}
        yield f"data: {json.dumps(error_data)}\n\n"


def store_messages_in_conversation(
    conv_id: str,
    user_content: str,
    assistant_content: str,
    metadata: MessageMetadata
):
    """Store messages in the conversation history."""
    if conv_id not in conversations:
        conversations[conv_id] = Conversation(id=conv_id)
    
    conv = conversations[conv_id]
    
    # Add user message
    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="user",
        content=user_content
    )
    conv.messages.append(user_msg)
    
    # Add assistant message
    assistant_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="assistant",
        content=assistant_content,
        metadata=metadata
    )
    conv.messages.append(assistant_msg)
    conv.updated_at = datetime.utcnow()


# ============================================
# Conversation Management Endpoints
# ============================================

@router.post("/conversations", response_model=Conversation, tags=["Conversations"])
async def create_conversation(request: ConversationCreate):
    """
    Create a new conversation/thread.
    
    Use this to start a new conversation session with an optional system prompt.
    The returned conversation_id can be used in subsequent chat completion requests.
    """
    conv_id = str(uuid.uuid4())
    conversation = Conversation(
        id=conv_id,
        title=request.title,
        metadata=request.metadata or {}
    )
    
    # Add system message if provided
    if request.system_message:
        system_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conv_id,
            role="system",
            content=request.system_message
        )
        conversation.messages.append(system_msg)
    
    conversations[conv_id] = conversation
    logger.info(f"Created conversation: {conv_id}")
    return conversation


@router.get("/conversations", response_model=ConversationList, tags=["Conversations"])
async def list_conversations(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    List all conversations with optional filtering.
    """
    convs = list(conversations.values())
    
    if status:
        convs = [c for c in convs if c.status == status]
    
    # Sort by updated_at descending
    convs.sort(key=lambda x: x.updated_at, reverse=True)
    
    total = len(convs)
    paginated = convs[offset:offset + limit]
    
    return ConversationList(
        conversations=paginated,
        total=total,
        has_more=(offset + limit) < total
    )


@router.get("/conversations/{conversation_id}", response_model=Conversation, tags=["Conversations"])
async def get_conversation(conversation_id: str):
    """
    Retrieve a conversation by ID with full message history.
    """
    if conversation_id not in conversations:
        raise HTTPException(
            status_code=404,
            detail=APIError(
                error=ErrorDetail(
                    code="conversation_not_found",
                    message=f"Conversation '{conversation_id}' not found",
                    type="invalid_request_error",
                    param="conversation_id"
                )
            ).model_dump()
        )
    return conversations[conversation_id]


@router.patch("/conversations/{conversation_id}", response_model=Conversation, tags=["Conversations"])
async def update_conversation(conversation_id: str, request: ConversationUpdate):
    """
    Update conversation status or title.
    """
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conv = conversations[conversation_id]
    if request.status:
        conv.status = request.status
    if request.title:
        conv.title = request.title
    conv.updated_at = datetime.utcnow()
    
    return conv


@router.delete("/conversations/{conversation_id}", tags=["Conversations"])
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation.
    """
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    del conversations[conversation_id]
    return {"deleted": True, "conversation_id": conversation_id}


# ============================================
# Chat Completion Endpoints
# ============================================

@router.post("/completions", response_model=ChatCompletionResponse, tags=["Chat"])
async def create_chat_completion(
    request: ChatCompletionRequest,
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Create a chat completion.
    
    This is the main endpoint for getting AI responses. Compatible with OpenAI's
    chat completions API format with BRS-specific extensions for sources and
    confidence scores.
    
    **Features:**
    - Set `stream: true` for Server-Sent Events streaming
    - Provide `conversation_id` to continue existing conversations
    - Sources and confidence scores included in response
    
    **Example:**
    ```json
    {
        "messages": [
            {"role": "user", "content": "How do I register a company?"}
        ],
        "stream": false
    }
    ```
    """
    request_id = x_request_id or generate_request_id()
    start_time = time.time()
    
    try:
        # Get or create conversation
        conv_id = request.conversation_id or str(uuid.uuid4())
        if conv_id not in conversations:
            conversations[conv_id] = Conversation(id=conv_id)
        
        # Handle streaming
        if request.stream:
            return StreamingResponse(
                stream_workflow(
                    request.messages,
                    conv_id,
                    request.provider or "gemini",
                    request.model or "gemini-2.0-flash"
                ),
                media_type="text/event-stream",
                headers={
                    "X-Request-ID": request_id,
                    "X-Conversation-ID": conv_id,
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"  # Disable nginx buffering
                }
            )
        
        # Non-streaming: invoke workflow
        result = await invoke_workflow(
            request.messages,
            conv_id,
            request.provider or "gemini"
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        response_text = result.get("response", "")
        sources = result.get("sources", [])
        confidence = result.get("confidence", 0.0)
        
        # Store in conversation history
        store_messages_in_conversation(
            conv_id,
            request.messages[-1].content,
            response_text,
            MessageMetadata(
                sources=sources,
                confidence=confidence,
                model=request.model,
                latency_ms=latency_ms
            )
        )
        
        # Build response
        return ChatCompletionResponse(
            id=generate_completion_id(),
            model=request.model or "gemini-2.0-flash",
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=MessageContent(
                        role="assistant",
                        content=response_text
                    ),
                    finish_reason="stop"
                )
            ],
            conversation_id=conv_id,
            sources=sources,
            confidence=confidence
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=APIError(
                error=ErrorDetail(
                    code="internal_error",
                    message=str(e),
                    type="server_error"
                ),
                request_id=request_id
            ).model_dump()
        )


# ============================================
# WebSocket Endpoint
# ============================================

@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time bidirectional chat.
    
    **Connect:** `ws://localhost:8000/api/v1/chat/ws`
    
    **Send message:**
    ```json
    {"type": "message", "content": "Your question", "conversation_id": "optional"}
    ```
    
    **Receive:**
    ```json
    {"type": "response", "content": "...", "sources": [...], "confidence": 0.85}
    ```
    """
    await websocket.accept()
    
    conversation_id = str(uuid.uuid4())
    conversations[conversation_id] = Conversation(id=conversation_id)
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "conversation_id": conversation_id,
            "message": "Connected to BRS-SASA"
        })
        
        while True:
            data = await websocket.receive_json()
            
            msg_type = data.get("type", "message")
            content = data.get("content", data.get("message", ""))
            conv_id = data.get("conversation_id", conversation_id)
            stream = data.get("stream", False)
            
            if not content:
                await websocket.send_json({
                    "type": "error",
                    "error": {"code": "missing_content", "message": "Content is required"}
                })
                continue
            
            # Build messages from conversation history
            messages = []
            if conv_id in conversations:
                for msg in conversations[conv_id].messages:
                    messages.append(MessageContent(role=msg.role, content=msg.content))
            messages.append(MessageContent(role="user", content=content))
            
            if stream:
                # Stream response
                await websocket.send_json({"type": "stream_start"})
                
                result = await invoke_workflow(messages, conv_id, "gemini")
                response_text = result.get("response", "")
                
                # Stream in chunks
                chunk_size = 20
                for i in range(0, len(response_text), chunk_size):
                    chunk = response_text[i:i + chunk_size]
                    await websocket.send_json({
                        "type": "stream_chunk",
                        "content": chunk
                    })
                    await asyncio.sleep(0.02)
                
                await websocket.send_json({
                    "type": "stream_end",
                    "sources": result.get("sources", []),
                    "confidence": result.get("confidence", 0.0),
                    "conversation_id": conv_id
                })
            else:
                # Non-streaming response
                result = await invoke_workflow(messages, conv_id, "gemini")
                
                # Store messages
                store_messages_in_conversation(
                    conv_id,
                    content,
                    result.get("response", ""),
                    MessageMetadata(
                        sources=result.get("sources", []),
                        confidence=result.get("confidence", 0.0)
                    )
                )
                
                await websocket.send_json({
                    "type": "response",
                    "content": result.get("response", ""),
                    "sources": result.get("sources", []),
                    "confidence": result.get("confidence", 0.0),
                    "conversation_id": conv_id
                })
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "error": {"message": str(e)}
            })
        except:
            pass
        await websocket.close(code=1011)
