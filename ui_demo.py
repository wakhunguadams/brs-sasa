"""
BRS-SASA Demo UI - Production-Ready Streamlit Interface
Features: Streaming responses, conversation management, modern design
"""
import streamlit as st
import httpx
import json
import uuid
from typing import Optional
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="BRS-SASA: AI Business Registration Assistant",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1/chat"

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "streaming_enabled" not in st.session_state:
    st.session_state.streaming_enabled = True


# ============================================
# API Functions
# ============================================

def create_conversation(title: Optional[str] = None, system_message: Optional[str] = None) -> dict:
    """Create a new conversation via API."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{API_BASE_URL}/conversations",
                json={
                    "title": title,
                    "system_message": system_message
                }
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        st.error(f"Failed to create conversation: {e}")
        return None


def send_message(messages: list, conversation_id: Optional[str] = None, stream: bool = False) -> dict:
    """Send a message and get response."""
    try:
        with httpx.Client(timeout=60.0) as client:
            payload = {
                "messages": messages,
                "conversation_id": conversation_id,
                "stream": False,  # We handle streaming separately
                "provider": "gemini"
            }
            
            response = client.post(
                f"{API_BASE_URL}/completions",
                json=payload,
                headers={"X-Request-ID": f"ui-{uuid.uuid4().hex[:8]}"}
            )
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        return {"error": "Request timed out. Please try again."}
    except Exception as e:
        return {"error": str(e)}


def send_message_streaming(messages: list, conversation_id: Optional[str] = None):
    """Send a message with SSE streaming."""
    try:
        with httpx.Client(timeout=60.0) as client:
            payload = {
                "messages": messages,
                "conversation_id": conversation_id,
                "stream": True,
                "provider": "gemini"
            }
            
            with client.stream(
                "POST",
                f"{API_BASE_URL}/completions",
                json=payload,
                headers={"Accept": "text/event-stream"}
            ) as response:
                response.raise_for_status()
                
                full_content = ""
                sources = []
                confidence = 0.0
                conv_id = conversation_id
                
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        
                        if data == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            
                            # Extract content from delta
                            if "choices" in chunk and chunk["choices"]:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    full_content += content
                                    yield {"type": "content", "content": content}
                            
                            # Extract metadata from final chunk
                            if chunk.get("sources"):
                                sources = chunk["sources"]
                            if chunk.get("confidence"):
                                confidence = chunk["confidence"]
                            if chunk.get("conversation_id"):
                                conv_id = chunk["conversation_id"]
                                
                        except json.JSONDecodeError:
                            continue
                
                # Yield final metadata
                yield {
                    "type": "done",
                    "content": full_content,
                    "sources": sources,
                    "confidence": confidence,
                    "conversation_id": conv_id
                }
                
    except Exception as e:
        yield {"type": "error", "error": str(e)}


# ============================================
# UI Components
# ============================================

def render_header():
    """Render the application header."""
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1 style="color: #1f4e79; margin-bottom: 0.5rem;">
            🏛️ BRS-SASA
        </h1>
        <p style="color: #666; font-size: 1.1rem;">
            AI-Powered Business Registration Assistant for Kenya
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with controls and info."""
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Streaming toggle
        st.session_state.streaming_enabled = st.toggle(
            "Enable Streaming",
            value=st.session_state.streaming_enabled,
            help="Stream responses in real-time"
        )
        
        st.divider()
        
        # Conversation controls
        st.header("💬 Conversation")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🆕 New Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.conversation_id = None
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        
        if st.session_state.conversation_id:
            st.caption(f"ID: `{st.session_state.conversation_id[:12]}...`")
        
        st.divider()
        
        # Quick queries
        st.header("📋 Quick Questions")
        
        quick_queries = [
            "How do I register a company in Kenya?",
            "What are the registration fees?",
            "Can foreigners own companies?",
            "What documents are required?",
            "How long does registration take?",
            "What are BRS contact details?"
        ]
        
        for query in quick_queries:
            if st.button(query, key=f"quick_{hash(query)}", use_container_width=True):
                return query  # Return the query to be processed
        
        st.divider()
        
        # About section
        st.header("ℹ️ About")
        st.markdown("""
        **BRS-SASA** uses AI to help you understand:
        - Company registration processes
        - Legal requirements & documents
        - Fees and timelines
        - Contact information
        
        *Powered by LangGraph & Gemini 2.0*
        """)
        
        # API Status
        st.divider()
        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.get("http://localhost:8000/api/v1/health/")
                if response.status_code == 200:
                    st.success("🟢 API Connected")
                else:
                    st.warning("🟡 API Degraded")
        except:
            st.error("🔴 API Offline")
    
    return None


def render_message(role: str, content: str, sources: list = None, confidence: float = None):
    """Render a single message."""
    with st.chat_message(role, avatar="👤" if role == "user" else "🤖"):
        st.markdown(content)
        
        if role == "assistant" and (sources or confidence):
            cols = st.columns([3, 1])
            
            with cols[0]:
                if sources and len(sources) > 0:
                    sources_display = ", ".join(sources[:3])
                    if len(sources) > 3:
                        sources_display += f" +{len(sources) - 3} more"
                    st.caption(f"📚 Sources: {sources_display}")
            
            with cols[1]:
                if confidence and confidence > 0:
                    st.caption(f"✅ {confidence * 100:.0f}% confident")


def render_chat_history():
    """Render the chat message history."""
    for msg in st.session_state.messages:
        render_message(
            msg["role"],
            msg["content"],
            msg.get("sources"),
            msg.get("confidence")
        )


def process_user_input(user_input: str):
    """Process user input and get AI response."""
    if not user_input.strip():
        return
    
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Display user message
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
    
    # Build messages for API
    api_messages = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in st.session_state.messages
    ]
    
    # Get AI response
    with st.chat_message("assistant", avatar="🤖"):
        if st.session_state.streaming_enabled:
            # Streaming response
            message_placeholder = st.empty()
            full_response = ""
            sources = []
            confidence = 0.0
            
            for chunk in send_message_streaming(
                api_messages,
                st.session_state.conversation_id
            ):
                if chunk["type"] == "content":
                    full_response += chunk["content"]
                    message_placeholder.markdown(full_response + "▌")
                elif chunk["type"] == "done":
                    full_response = chunk["content"]
                    sources = chunk.get("sources", [])
                    confidence = chunk.get("confidence", 0.0)
                    st.session_state.conversation_id = chunk.get("conversation_id")
                elif chunk["type"] == "error":
                    st.error(f"Error: {chunk['error']}")
                    return
            
            message_placeholder.markdown(full_response)
            
        else:
            # Non-streaming response
            with st.spinner("Thinking..."):
                response = send_message(
                    api_messages,
                    st.session_state.conversation_id
                )
            
            if "error" in response:
                st.error(f"Error: {response['error']}")
                return
            
            # Extract response data
            full_response = response["choices"][0]["message"]["content"]
            sources = response.get("sources", [])
            confidence = response.get("confidence", 0.0)
            st.session_state.conversation_id = response.get("conversation_id")
            
            st.markdown(full_response)
        
        # Display metadata
        cols = st.columns([3, 1])
        with cols[0]:
            if sources:
                sources_display = ", ".join(sources[:3])
                if len(sources) > 3:
                    sources_display += f" +{len(sources) - 3} more"
                st.caption(f"📚 Sources: {sources_display}")
        with cols[1]:
            if confidence > 0:
                st.caption(f"✅ {confidence * 100:.0f}% confident")
    
    # Add assistant message to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
        "sources": sources,
        "confidence": confidence
    })


# ============================================
# Main Application
# ============================================

def main():
    """Main application entry point."""
    
    # Render header
    render_header()
    
    # Render sidebar and get any quick query
    quick_query = render_sidebar()
    
    # Render chat history
    render_chat_history()
    
    # Handle quick query from sidebar
    if quick_query:
        process_user_input(quick_query)
        st.rerun()
    
    # Chat input
    if user_input := st.chat_input("Ask about business registration in Kenya..."):
        process_user_input(user_input)
        st.rerun()


if __name__ == "__main__":
    main()
