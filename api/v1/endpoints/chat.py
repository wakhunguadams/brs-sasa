from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from typing import Dict, List
import json
import logging
import uuid

from schemas.chat import ChatRequest, ChatResponse
from core.workflow import brs_workflow
from core.state import BRSState
from langchain_core.messages import HumanMessage
from core.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Handle a chat request using the LangGraph multi-agent system
    """
    try:
        # Prepare the initial state for the workflow
        conversation_id = str(uuid.uuid4())

        # Convert history to LangChain messages
        messages = []
        if request.history:
            for msg in request.history:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    from langchain_core.messages import AIMessage
                    messages.append(AIMessage(content=msg.content))

        # Add the current user message
        messages.append(HumanMessage(content=request.message))

        # Prepare the initial state
        initial_state: BRSState = {
            "messages": messages,
            "user_input": request.message,
            "response": "",
            "conversation_id": conversation_id,
            "context": {
                "llm_provider": request.provider or "gemini",
                "original_request": request.dict() if hasattr(request, 'dict') else request.__dict__
            },
            "sources": [],
            "confidence": 0.0,
            "query_type": "unknown",
            "retrieved_docs": [],
            "agent_feedback": {},
            "current_agent": "router"
        }

        # Invoke the workflow
        result = await brs_workflow.invoke(
            initial_state,
            config={
                "configurable": {
                    "thread_id": conversation_id
                }
            }
        )

        return ChatResponse(
            response=result.get("response", ""),
            sources=result.get("sources", []),
            confidence=result.get("confidence", 0.0)
        )
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat using the LangGraph multi-agent system
    """
    await websocket.accept()

    try:
        conversation_id = str(uuid.uuid4())
        chat_history = []

        while True:
            data = await websocket.receive_text()
            request = json.loads(data)

            message = request.get("message", "")
            if not message:
                await websocket.send_text(json.dumps({"error": "Message is required"}))
                continue

            # Convert chat history to LangChain messages
            messages = []
            for msg in chat_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    from langchain_core.messages import AIMessage
                    messages.append(AIMessage(content=msg["content"]))

            # Add the current user message
            messages.append(HumanMessage(content=message))

            # Prepare the initial state
            initial_state: BRSState = {
                "messages": messages,
                "user_input": message,
                "response": "",
                "conversation_id": conversation_id,
                "context": {
                    "llm_provider": "gemini",  # Default provider for WebSocket
                },
                "sources": [],
                "confidence": 0.0,
                "query_type": "unknown",
                "retrieved_docs": [],
                "agent_feedback": {},
                "current_agent": "router"
            }

            # Invoke the workflow
            result = await brs_workflow.invoke(
                initial_state,
                config={
                    "configurable": {
                        "thread_id": conversation_id
                    }
                }
            )

            # Update chat history
            chat_history.append({"role": "user", "content": message})
            chat_history.append({"role": "assistant", "content": result.get("response", "")})

            # Send response back to client
            await websocket.send_text(json.dumps({
                "response": result.get("response", ""),
                "sources": result.get("sources", []),
                "confidence": result.get("confidence", 0.0)
            }))

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()