import streamlit as st
import asyncio
import httpx
import uuid
from typing import Dict, Any

# Set page config
st.set_page_config(
    page_title="BRS-SASA: AI-Powered Business Registration Assistant",
    page_icon="🏛️",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        text-align: center;
        color: #1f4e79;
        margin-bottom: 2rem;
    }
    .sub-header {
        text-align: center;
        color: #555;
        margin-bottom: 2rem;
    }
    .user-message {
        background-color: #e3f2fd;
        padding: 10px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f5f5f5;
        padding: 10px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #4caf50;
    }
    .source-box {
        background-color: #fff3e0;
        padding: 8px;
        border-radius: 4px;
        margin-top: 5px;
        font-size: 0.9em;
    }
    .confidence-box {
        background-color: #e8f5e9;
        padding: 5px;
        border-radius: 4px;
        display: inline-block;
        margin-top: 5px;
        font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🏛️ BRS-SASA: AI-Powered Business Registration Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Your intelligent assistant for Kenyan Business Registration Service (BRS) queries</p>', unsafe_allow_html=True)

# Initialize API client
async def get_ai_response(message: str, history: list) -> Dict[str, Any]:
    """
    Get response from the BRS-SASA backend API
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/v1/chat/",
                json={
                    "message": message,
                    "history": history,
                    "provider": "gemini"
                }
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            return {
                "response": f"Error connecting to the API: {str(e)}",
                "sources": [],
                "confidence": 0.0
            }
        except httpx.HTTPStatusError as e:
            return {
                "response": f"API returned an error: {e.response.status_code}",
                "sources": [],
                "confidence": 0.0
            }

# Display chat messages
for message in st.session_state.messages:
    with st.container():
        if message["role"] == "user":
            st.markdown(f'<div class="user-message"><strong>You:</strong> {message["content"]}</div>', 
                       unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="assistant-message"><strong>🤖 BRS-SASA:</strong> {message["content"]}</div>', 
                       unsafe_allow_html=True)
            
            # Show sources and confidence if available
            if message.get("sources"):
                sources_text = ", ".join(message["sources"][:3])  # Limit to first 3 sources
                if len(message["sources"]) > 3:
                    sources_text += f" and {len(message['sources']) - 3} more"
                st.markdown(f'<div class="source-box"><strong>Sources:</strong> {sources_text}</div>', 
                           unsafe_allow_html=True)
            
            if "confidence" in message and message["confidence"] > 0:
                confidence_pct = message["confidence"] * 100
                st.markdown(f'<div class="confidence-box">Confidence: {confidence_pct:.1f}%</div>', 
                           unsafe_allow_html=True)

# Input section
st.markdown("---")
input_container = st.container()

with input_container:
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input("Ask about business registration, laws, or procedures:", 
                                  placeholder="e.g., How do I register a company in Kenya?")
    
    with col2:
        send_button = st.button("Send", type="primary")

# Handle user input
if send_button and user_input.strip():
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Get AI response
    with st.spinner("Thinking..."):
        # Convert session state messages to the format expected by the API
        history = [{"role": m["role"], "content": m["content"]} 
                  for m in st.session_state.messages[:-1]]  # Exclude current message
        
        response_data = asyncio.run(get_ai_response(user_input, history))
    
    # Add AI response to history
    ai_response = {
        "role": "assistant", 
        "content": response_data.get("response", "Sorry, I couldn't process that request."),
        "sources": response_data.get("sources", []),
        "confidence": response_data.get("confidence", 0.0)
    }
    st.session_state.messages.append(ai_response)
    
    # Rerun to display the new messages
    st.rerun()

elif user_input and not send_button:
    # If user pressed Enter without clicking button, simulate button click
    pass

# Sidebar with information
with st.sidebar:
    st.header("ℹ️ About BRS-SASA")
    st.write("""
    BRS-SASA is an AI-powered conversational platform for the 
    Business Registration Service (BRS) of Kenya.
    
    **Capabilities:**
    - Answer FAQs about registration processes
    - Explain legal documents in plain language
    - Provide registration requirements and fees
    - Compare Kenyan laws with international jurisdictions
    - Collect public feedback on draft legislation
    """)
    
    st.header("📋 Common Queries")
    common_queries = [
        "How do I register a business name?",
        "What are the requirements for a private limited company?",
        "How much does company registration cost?",
        "What documents do I need for LLP registration?",
        "How long does the registration process take?"
    ]
    
    for query in common_queries:
        if st.button(query, key=f"query_{query}"):
            st.session_state.messages.append({"role": "user", "content": query})
            st.rerun()
    
    st.divider()
    st.write("**Current Session ID:**")
    st.code(st.session_state.conversation_id[:12] + "...")

# Footer
st.markdown("---")
st.markdown('<p style="text-align: center; color: #888;">BRS-SASA: AI-Powered Business Registration Assistant | Powered by LangGraph & Gemini</p>', 
           unsafe_allow_html=True)