# BRS-SASA: Technical Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [API Reference](#api-reference)
7. [Testing](#testing)
8. [Deployment](#deployment)

## Overview

BRS-SASA is an intelligent conversational AI platform for the Business Registration Service (BRS) of Kenya. The platform uses advanced RAG (Retrieval-Augmented Generation) technology powered by **LangGraph** and **Google Gemini 2.0 Flash** to answer questions about business registration, explain draft legislation, and provide information about fees, requirements, and processes.

### Key Features
- **Intelligent FAQ & Troubleshooting**: Answers questions about registration processes, requirements, fees, timelines
- **Legislative Document Assistant**: Makes legal documents accessible through conversation
- **RAG-Powered Knowledge Base**: ChromaDB vector database with intelligent document chunking
- **Multi-Provider LLM Support**: Factory pattern supporting Gemini, OpenAI, and Anthropic
- **Source Citations**: Every response includes document sources and confidence scores

## Architecture

The system follows a multi-agent architecture built on FastAPI with LangGraph orchestration:

```
┌─────────────────────────────────────────────────────────────┐
│                     Demo UI (Streamlit)                     │
│                   http://localhost:8501                     │
├─────────────────────────────────────────────────────────────┤
│                    FastAPI Backend                          │
│                   http://localhost:8000                     │
├─────────────────────────────────────────────────────────────┤
│                LangGraph Multi-Agent System                 │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │   Router    │→ │  RAG Agent  │→ │ Response Formatter│   │
│  │    Node     │  │    Node     │  │      Node         │   │
│  └─────────────┘  └─────────────┘  └──────────────────┘   │
│         ↓              ↓                                   │
│  ┌─────────────┐  ┌─────────────┐                         │
│  │Conversation │  │   Error     │                         │
│  │   Agent     │  │  Handler    │                         │
│  └─────────────┘  └─────────────┘                         │
├─────────────────────────────────────────────────────────────┤
│  LLM Factory (Gemini 2.0 Flash) │ ChromaDB Vector Store   │
├─────────────────────────────────────────────────────────────┤
│  Knowledge Base: Acts, Regulations, FAQs, Extended Info   │
└─────────────────────────────────────────────────────────────┘
```

## Components

### Core Modules

#### 1. FastAPI Web Framework (`main.py`)
- RESTful API endpoints for all platform functionality
- WebSocket support for real-time chat interactions
- Built-in automatic API documentation (Swagger/OpenAPI)
- Asynchronous processing for high performance
- CORS middleware for cross-origin requests

#### 2. LangGraph Multi-Agent System (`core/workflow.py`)
The system uses LangGraph for orchestrating multiple AI agents with proper state management:
- **State Management**: Typed state schema with reducer functions for safe state updates
- **Agent Orchestration**: Router, RAG agent, conversation agent, and response formatter nodes
- **Error Handling**: Built-in error handling and retry mechanisms
- **Checkpointing**: MemorySaver for conversation persistence

##### State Schema (`core/state.py`)
```python
from typing import Annotated, TypedDict, Optional, List, Dict, Any
from langgraph.graph.message import add_messages

class BRSState(TypedDict):
    messages: Annotated[list, add_messages]  # Chat history with reducer
    user_input: str  # Current user input
    response: str  # Final response to user
    query_type: str  # Type of query ('knowledge', 'conversation', 'mixed')
    context: Optional[Dict[str, Any]]  # Additional context
    conversation_id: str  # Unique conversation identifier
    retrieved_docs: Annotated[List[Dict[str, Any]], lambda x, y: x + y]  # Accumulate docs
    sources: Annotated[List[str], lambda x, y: list(set(x + y if y else []))]  # Deduplicate
    confidence: float  # Confidence score
    current_agent: str  # Currently active agent
    agent_feedback: Optional[Dict[str, Any]]  # Feedback from agents
    error_count: int  # Error counter for flow control
    max_steps: int  # Max steps to prevent infinite loops (default: 10)
```

#### 3. LLM Factory Pattern (`llm_factory/factory.py`)
The LLM factory provides abstraction over multiple LLM providers:

```python
from llm_factory.factory import LLMFactory

factory = LLMFactory()
llm = factory.get_llm("gemini")  # or "openai", "anthropic"
```

**Supported Providers:**
| Provider | Model | Package |
|----------|-------|---------|
| Gemini (default) | gemini-2.0-flash | google-genai |
| OpenAI | gpt-4 | openai |
| Anthropic | claude-3 | anthropic |

#### 4. AI Agents (`agents/`)

##### LangGraph Nodes (`agents/langgraph_nodes.py`)

###### Router Node
Determines which agent should handle the incoming query:
```python
async def router_node(state: BRSState) -> Dict[str, str]:
    # Analyzes user input and routes to appropriate agent
    # Returns: {"current_agent": "rag_agent" | "conversation_agent"}
```

###### RAG Agent Node (`agents/rag_agent.py`)
Handles knowledge-based queries by retrieving relevant documents:
```python
async def rag_agent_node(state: BRSState) -> Dict[str, Any]:
    # Performs RAG operations:
    # 1. Search ChromaDB for relevant chunks
    # 2. Build context from retrieved documents
    # 3. Generate response with Gemini
    # 4. Extract and clean source filenames
    # Returns: {response, sources, confidence, retrieved_docs}
```

###### Conversation Agent Node (`agents/conversation_agent.py`)
Handles general conversation and greetings:
```python
async def conversation_agent_node(state: BRSState) -> Dict[str, Any]:
    # Processes conversational queries without RAG
    # Returns: {response, sources, confidence}
```

###### Response Formatter Node
Formats the final response with sources and confidence:
```python
async def response_formatter_node(state: BRSState) -> Dict[str, Any]:
    # Formats response, adds AI message to history
    # Returns: {response, messages}
```

#### 5. Knowledge Base Management (`core/knowledge_base.py`)

**Features:**
- Document ingestion with intelligent chunking
- ChromaDB vector database for semantic search
- Sentence-transformers for embeddings (`all-MiniLM-L6-v2`)
- Section-based chunking for structured documents
- Query expansion for improved retrieval accuracy

**Document Chunking (`utils/document_loader.py`):**
```python
class TextChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        # Splits documents at natural boundaries (paragraphs, sentences)
        # Creates overlapping chunks for better context preservation
    
    def split_by_sections(self, text: str) -> List[str]:
        # Section-aware chunking that preserves document structure
        # Keeps headers with their content (e.g., fee schedules stay together)
        # Prefixes chunks with section headers: [COMPANY REGISTRATION], [LLP], etc.
```

**Query Expansion (`agents/rag_agent.py`):**
The RAG agent automatically expands user queries to improve retrieval accuracy:
- Fee queries: Adds KES amounts and entity-specific terms
- Registration queries: Adds process and requirement keywords
- Contact queries: Adds phone, email, address terms
- LLP/Foreign queries: Adds specific terminology and fee amounts

Example: "What are LLP fees?" expands to:
- "What are LLP fees?"
- "LLP Registration Fees KES 10,650"
- "LLP Agreement filing KES 2,000"
- "LIMITED LIABILITY PARTNERSHIP requirements partners"

**Initialization:**
```bash
python initialize_kb.py
```

This ingests:
- Legal acts (Companies Act, Business Names Act, LLP Act)
- Regulatory documents
- FAQs (PDF)
- Extended BRS information (fees, contacts, processes)

#### 6. Demo UI (`ui_demo.py`)
Streamlit-based demo interface featuring:
- Native `st.chat_message()` components for proper theming
- Real-time chat with the API backend
- Source citations and confidence indicators
- Quick query buttons in sidebar
- Session management

## Installation

### Prerequisites
- Python 3.9+
- pip package manager
- Google Gemini API key (get one at https://aistudio.google.com/)

### Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd brs-sasa/brs_sasa
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. Initialize the knowledge base:
```bash
python initialize_kb.py
```

## Configuration

The application uses environment variables for configuration via Pydantic Settings:

### Required Settings
| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |

### Optional Settings
| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | BRS-SASA |
| `DEBUG` | Enable debug mode | false |
| `HOST` | API server host | 0.0.0.0 |
| `PORT` | API server port | 8000 |
| `DEFAULT_LLM_PROVIDER` | LLM provider | gemini |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `VECTOR_DB_TYPE` | Vector database type | chroma |
| `CHROMA_PERSIST_DIR` | ChromaDB storage | ./chroma_data |
| `LOG_LEVEL` | Logging level | INFO |
| `ALLOWED_ORIGINS` | CORS origins | ["*"] |

## API Reference

### Base URL
`http://localhost:8000`

### OpenAI-Compatible Endpoints

The API follows OpenAI's chat completions format for easy integration with existing tools.

#### POST /api/v1/chat/completions
OpenAI-compatible chat completions endpoint with optional streaming.

**Request Body:**
```json
{
  "messages": [
    {"role": "user", "content": "What are the LLP registration fees?"}
  ],
  "model": "gemini-2.0-flash",
  "stream": false,
  "conversation_id": "optional-uuid"
}
```

**Response:**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1706000000,
  "model": "gemini-2.0-flash",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "The fees for registering an LLP are:\n- Name Reservation: KES 150\n- LLP Registration: KES 10,650\n- LLP Agreement filing: KES 2,000"
    },
    "finish_reason": "stop"
  }],
  "conversation_id": "uuid",
  "sources": ["brs_extended_info.txt"],
  "confidence": 0.85
}
```

**Streaming (SSE):**
Set `"stream": true` to receive Server-Sent Events:
```
data: {"id":"chatcmpl-abc","choices":[{"delta":{"content":"The "}}]}
data: {"id":"chatcmpl-abc","choices":[{"delta":{"content":"fees "}}]}
...
data: [DONE]
```

#### POST /api/v1/chat/conversations
Create or continue a conversation with server-side persistence.

#### GET /api/v1/chat/conversations/{conversation_id}
Retrieve conversation history.

### Legacy Endpoints

#### GET /
Root endpoint with service information.

**Response:**
```json
{
  "message": "Welcome to BRS-SASA...",
  "version": "1.0.0",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

#### GET /info
Application configuration (non-sensitive).

**Response:**
```json
{
  "app_name": "BRS-SASA",
  "debug": false,
  "version": "1.0.0",
  "llm_provider": "gemini",
  "vector_db_type": "chroma",
  "timestamp": 1706000000
}
```

#### GET /api/v1/health/
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1706000000,
  "service": "brs-sasa-api"
}
```

#### POST /api/v1/chat/
Main chat endpoint using LangGraph multi-agent system.

**Request Body:**
```json
{
  "message": "How do I register a business?",
  "history": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hello! How can I help you?"}
  ],
  "provider": "gemini",
  "context": {}
}
```

**Response:**
```json
{
  "response": "To register a business in Kenya, you need to...",
  "sources": ["brs_extended_info.txt", "CompaniesAct17of2015.pdf"],
  "confidence": 0.85,
  "timestamp": "2026-01-23T12:00:00Z"
}
```

#### WebSocket /api/v1/chat/ws
Real-time chat via WebSocket.

**Send:**
```json
{"message": "How much does registration cost?"}
```

**Receive:**
```json
{
  "response": "Business name registration costs KES 950...",
  "sources": ["brs_extended_info.txt"],
  "confidence": 0.92
}
```

#### GET /api/v1/documents/list
List documents in the knowledge base.

#### POST /api/v1/documents/upload
Upload a document to the knowledge base.

## Testing

Run the test suite:

```bash
# All tests
pytest

# Verbose output
pytest -v

# Specific file
pytest tests/test_main.py

# With coverage
pytest --cov=. --cov-report=html
```

### Test Suite Contents
- Configuration validation tests
- LLM factory tests
- RAG agent tests
- State management tests
- API endpoint tests

All 9 tests currently passing.

## Deployment

### Local Development
```bash
# Both API and UI
python start_server.py

# API only
python start_server.py --mode api

# Direct uvicorn with reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Deployment

1. Use Gunicorn with Uvicorn workers:
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

2. Environment settings:
   - Set `DEBUG=false`
   - Configure proper `ALLOWED_ORIGINS`
   - Use SSL/TLS termination at reverse proxy

3. Docker deployment:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python initialize_kb.py

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t brs-sasa .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key brs-sasa
```

## Phase 1 Implementation Status

### Completed
- [x] FastAPI web framework with REST + WebSocket endpoints
- [x] LangGraph multi-agent orchestration with StateGraph
- [x] RAG Agent with ChromaDB vector store
- [x] Conversation Agent for general queries
- [x] Router Node for intelligent query routing
- [x] Response Formatter with source citations
- [x] Error Handler with retry logic
- [x] Multi-provider LLM factory (Gemini 2.0 Flash default)
- [x] Section-aware document chunking (preserves structure)
- [x] Query expansion for improved retrieval accuracy
- [x] OpenAI-compatible API with SSE streaming
- [x] Conversation persistence (server-side)
- [x] Streamlit Demo UI with native components
- [x] Unit tests (9 passing)
- [x] Extended knowledge base (fees, contacts, processes)

### Verified Query Coverage
| Query Type | Status | Example Response |
|------------|--------|------------------|
| Company Fees | PASS | KES 10,650 for private company |
| Business Name Fees | PASS | KES 950 registration |
| LLP Fees | PASS | KES 10,650 + KES 2,000 agreement |
| Foreign Company Fees | PASS | KES 25,000+ registration |
| Contact Details | PASS | Full address, phone, email |
| Processing Times | PASS | 24-48 hours |

### Future Phases
- Phase 2: Legislative Agent, Feedback Agent, Multi-language support
- Phase 3: CRM integration, Database integration, Statistics Agent

## License

This project is licensed under the MIT License.