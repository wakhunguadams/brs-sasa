"""
BRS-SASA Chat API - Production-Ready Endpoints
Following industry best practices: OpenAI-compatible, SSE streaming, conversation management.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Header, Query, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
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
from core.database import get_db
from core.models import ConversationModel, MessageModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from core.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


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
    """Stream workflow results as SSE events using LangGraph astream."""
    
    completion_id = generate_completion_id()
    created = int(time.time())
    
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
    
    try:
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
        
        last_response = ""
        sources = []
        confidence = 0.0
        
        # Use astream for real-time updates from LangGraph
        async for chunk in brs_workflow.stream(
            initial_state, 
            config={"configurable": {"thread_id": conversation_id}}
        ):
            # LangGraph chunks contain the state updates from each node
            for node_name, node_state in chunk.items():
                if "response" in node_state and node_state["response"]:
                    new_content = node_state["response"]
                    # If this is a new response or an update, stream the delta
                    if new_content != last_response:
                        delta = new_content[len(last_response):]
                        if delta:
                            stream_chunk = ChatCompletionChunk(
                                id=completion_id,
                                created=created,
                                model=model,
                                choices=[StreamChoice(
                                    index=0,
                                    delta=DeltaContent(content=delta),
                                    finish_reason=None
                                )]
                            )
                            yield f"data: {stream_chunk.model_dump_json()}\n\n"
                            last_response = new_content
                
                if "sources" in node_state:
                    sources = node_state["sources"]
                if "confidence" in node_state:
                    confidence = node_state["confidence"]
        
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
    db: Session,
    conv_id: str,
    user_content: str,
    assistant_content: str,
    metadata: MessageMetadata
):
    """Store messages in the database."""
    # Ensure conversation exists
    db_conv = db.query(ConversationModel).filter(ConversationModel.id == conv_id).first()
    if not db_conv:
        db_conv = ConversationModel(id=conv_id)
        db.add(db_conv)
        db.commit()
    
    # Add user message
    user_msg = MessageModel(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="user",
        content=user_content
    )
    db.add(user_msg)
    
    # Add assistant message
    assistant_msg = MessageModel(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="assistant",
        content=assistant_content,
        message_metadata=metadata.model_dump()
    )
    db.add(assistant_msg)
    
    # Update conversation timestamp
    db_conv.updated_at = datetime.utcnow()
    db.commit()


# ============================================
# Conversation Management Endpoints
# ============================================

@router.post("/conversations", response_model=Conversation, tags=["Conversations"])
async def create_conversation(request: ConversationCreate, db: Session = Depends(get_db)):
    """
    Create a new conversation/thread.
    """
    conv_id = str(uuid.uuid4())
    db_conv = ConversationModel(
        id=conv_id,
        title=request.title,
        conversation_metadata=request.conversation_metadata or {}
    )
    db.add(db_conv)
    
    # Add system message if provided
    if request.system_message:
        system_msg = MessageModel(
            id=str(uuid.uuid4()),
            conversation_id=conv_id,
            role="system",
            content=request.system_message
        )
        db.add(system_msg)
    
    db.commit()
    db.refresh(db_conv)
    
    logger.info(f"Created conversation: {conv_id}")
    return db_conv


@router.get("/conversations", response_model=ConversationList, tags=["Conversations"])
async def list_conversations(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    List all conversations with optional filtering.
    """
    query = db.query(ConversationModel)
    
    if status:
        query = query.filter(ConversationModel.status == status)
    
    total = query.count()
    convs = query.order_by(ConversationModel.updated_at.desc()).offset(offset).limit(limit).all()
    
    return ConversationList(
        conversations=convs,
        total=total,
        has_more=(offset + limit) < total
    )


@router.get("/conversations/{conversation_id}", response_model=Conversation, tags=["Conversations"])
async def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a conversation by ID with full message history.
    """
    db_conv = db.query(ConversationModel).filter(ConversationModel.id == conversation_id).first()
    if not db_conv:
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
    return db_conv


@router.patch("/conversations/{conversation_id}", response_model=Conversation, tags=["Conversations"])
async def update_conversation(conversation_id: str, request: ConversationUpdate, db: Session = Depends(get_db)):
    """
    Update conversation status or title.
    """
    db_conv = db.query(ConversationModel).filter(ConversationModel.id == conversation_id).first()
    if not db_conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if request.status:
        db_conv.status = request.status
    if request.title:
        db_conv.title = request.title
    
    db.commit()
    db.refresh(db_conv)
    
    return db_conv


@router.delete("/conversations/{conversation_id}", tags=["Conversations"])
async def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """
    Delete a conversation.
    """
    db_conv = db.query(ConversationModel).filter(ConversationModel.id == conversation_id).first()
    if not db_conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    db.delete(db_conv)
    db.commit()
    
    return {"deleted": True, "conversation_id": conversation_id}


# ============================================
# Chat Completion Endpoints
# ============================================

@router.post("/completions", response_model=ChatCompletionResponse, tags=["Chat"])
async def create_chat_completion(
    request: ChatCompletionRequest,
    db: Session = Depends(get_db),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Create a chat completion.
    """
    request_id = x_request_id or generate_request_id()
    start_time = time.time()
    
    try:
        # Get or create conversation
        conv_id = request.conversation_id or str(uuid.uuid4())
        db_conv = db.query(ConversationModel).filter(ConversationModel.id == conv_id).first()
        if not db_conv:
            db_conv = ConversationModel(id=conv_id)
            db.add(db_conv)
            db.commit()
        
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
                    "X-Accel-Buffering": "no"
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
        
        # Store in database
        store_messages_in_conversation(
            db,
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
    """
    await websocket.accept()
    
    from core.database import SessionLocal
    db = SessionLocal()
    
    conversation_id = str(uuid.uuid4())
    db_conv = ConversationModel(id=conversation_id)
    db.add(db_conv)
    db.commit()
    
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
            
            # Ensure conversation exists
            db_conv = db.query(ConversationModel).filter(ConversationModel.id == conv_id).first()
            if not db_conv:
                db_conv = ConversationModel(id=conv_id)
                db.add(db_conv)
                db.commit()
            
            # Build messages from database history
            messages = []
            for msg in db_conv.messages:
                messages.append(MessageContent(role=msg.role, content=msg.content))
            messages.append(MessageContent(role="user", content=content))
            
            if stream:
                # Stream response
                await websocket.send_json({"type": "stream_start"})
                
                lc_messages = messages_to_langchain(messages)
                initial_state: BRSState = {
                    "messages": lc_messages,
                    "user_input": content,
                    "response": "",
                    "conversation_id": conv_id,
                    "context": {"llm_provider": "gemini"},
                    "sources": [],
                    "confidence": 0.0,
                    "query_type": "unknown",
                    "retrieved_docs": [],
                    "agent_feedback": {},
                    "current_agent": "router",
                    "error_count": 0,
                    "max_steps": 10
                }
                
                last_response = ""
                sources = []
                confidence = 0.0
                
                async for chunk in brs_workflow.stream(
                    initial_state,
                    config={"configurable": {"thread_id": conv_id}}
                ):
                    for node_name, node_state in chunk.items():
                        if "response" in node_state and node_state["response"]:
                            new_content = node_state["response"]
                            if new_content != last_response:
                                delta = new_content[len(last_response):]
                                if delta:
                                    await websocket.send_json({
                                        "type": "stream_chunk",
                                        "content": delta
                                    })
                                    last_response = new_content
                        
                        if "sources" in node_state:
                            sources = node_state["sources"]
                        if "confidence" in node_state:
                            confidence = node_state["confidence"]
                
                # Store final response
                store_messages_in_conversation(
                    db,
                    conv_id,
                    content,
                    last_response,
                    MessageMetadata(sources=sources, confidence=confidence)
                )
                
                await websocket.send_json({
                    "type": "stream_end",
                    "sources": sources,
                    "confidence": confidence,
                    "conversation_id": conv_id
                })
            else:
                # Non-streaming response
                result = await invoke_workflow(messages, conv_id, "gemini")
                response_text = result.get("response", "")
                sources = result.get("sources", [])
                confidence = result.get("confidence", 0.0)
                
                # Store messages
                store_messages_in_conversation(
                    db,
                    conv_id,
                    content,
                    response_text,
                    MessageMetadata(
                        sources=sources,
                        confidence=confidence
                    )
                )
                
                await websocket.send_json({
                    "type": "response",
                    "content": response_text,
                    "sources": sources,
                    "confidence": confidence,
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
    finally:
        db.close()
