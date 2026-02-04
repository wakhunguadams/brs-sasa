# BRS-SASA: AI-Powered Conversational Platform

BRS-SASA is an intelligent conversational AI platform for the Business Registration Service (BRS) of Kenya. The platform uses advanced RAG (Retrieval-Augmented Generation) technology powered by **LangGraph** and **Google Gemini 2.5 Flash** to answer questions about business registration, explain draft legislation, collect public feedback, and provide real-time statistics - all through natural conversation.

## Quick Start

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Initialize the knowledge base (first time only)
python initialize_kb.py

# 3. Start both API and UI servers
python start_server.py

# Access:
# - API: http://localhost:8000
# - UI Demo: http://localhost:8501
# - API Docs: http://localhost:8000/docs
```

## Project Structure

```
brs_sasa/
├── api/                    # API endpoints
│   └── v1/
│       └── endpoints/
│           ├── chat.py     # Chat functionality (REST + WebSocket)
│           ├── health.py   # Health checks
│           └── documents.py # Document management
├── agents/                 # AI agents
│   ├── conversation_agent.py  # General conversation handling
│   ├── rag_agent.py          # RAG-based knowledge retrieval
│   ├── langgraph_nodes.py    # LangGraph node implementations
│   └── __init__.py
├── core/                   # Core utilities
│   ├── config.py          # Configuration (Pydantic Settings)
│   ├── logger.py          # Logging setup
│   ├── state.py           # LangGraph state definition
│   ├── workflow.py        # LangGraph workflow orchestration
│   ├── knowledge_base.py  # ChromaDB knowledge base management
│   └── __init__.py
├── llm_factory/            # LLM provider abstraction
│   └── factory.py         # Multi-provider factory (Gemini, OpenAI, Anthropic)
├── utils/
│   └── document_loader.py # Document loading and chunking
├── schemas/                # Pydantic schemas
│   └── chat.py
├── knowledge_docs/         # Knowledge base documents
│   ├── brs_extended_info.txt  # Extended FAQ with fees, contacts, processes
│   └── ...
├── acts/                  # Legal documents (Companies Act, etc.)
├── regulations/           # Regulatory documents
├── ui_demo.py             # Streamlit demo UI
├── main.py                # FastAPI application entry point
├── start_server.py        # Server startup script
├── initialize_kb.py       # Knowledge base initialization script
├── requirements.txt       # Dependencies
├── .env                   # Environment configuration
└── tests/                 # Test suite
    └── test_main.py
```

## Features

- **Intelligent FAQ & Troubleshooting**: Answers questions about registration processes, requirements, fees, timelines
- **Legislative Document Assistant**: Makes draft legislation accessible through conversation
- **RAG-Powered Knowledge Base**: ChromaDB vector database with section-aware chunking and query expansion
- **OpenAI-Compatible API**: Industry-standard chat completions endpoint with SSE streaming
- **Multi-Provider LLM Support**: Factory pattern supporting Gemini, OpenAI, and Anthropic
- **Real-time Chat**: REST API and WebSocket support for instant responses
- **Source Citations**: Every response includes document sources and confidence scores
- **Demo UI**: Production-ready Streamlit interface for demonstrations

## Architecture

The system implements a multi-agent architecture using **LangGraph** for proper state management and agent orchestration:

```
┌─────────────────────────────────────────────────────────────┐
│                     Demo UI (Streamlit)                     │
│                   http://localhost:8501                     │
├─────────────────────────────────────────────────────────────┤
│                    FastAPI Backend                          │
│                   http://localhost:8000                     │
├─────────────────────────────────────────────────────────────┤
│                LangGraph Multi-Agent System                 │
│                                                             │
│  ┌─────────────┐                                           │
│  │   Router    │───────────────────────────────────────────┐│
│  │    Node     │                                           ││
│  └─────┬───────┘                              ┌──────────┴─┤
│        │                                      │   Error    ││
│        │                                      │  Handler   ││
│   ┌────▼─────┐  ┌──────────────────┐         │    Node    ││
│   │ RAG Agent│  │ Response Formatter│         └────────────┘│
│   │   Node   │  │      Node         │                       │
│   └────┬─────┘  └─────────▲────────┘                       │
│        │                  │                                │
│   ┌────▼──────────────────┼────────────────────────────────┐│
│   │ Conversation Agent    │                                ││
│   │        Node           │                                ││
│   └───────────────────────┘                                ││
├─────────────────────────────────────────────────────────────┤
│  LLM Factory (gemini-2.5-flash) │ ChromaDB Vector Store    │
├─────────────────────────────────────────────────────────────┤
│  Knowledge Base: Acts, Regulations, FAQs, Extended Info     │
└─────────────────────────────────────────────────────────────┘
```

The architecture follows LangGraph best practices with conditional routing:
- **Router Node**: Determines if query needs RAG or conversation handling
- **RAG Agent**: Processes knowledge-based queries with document retrieval
- **Conversation Agent**: Handles general conversation and greetings
- **Response Formatter**: Formats responses with sources and confidence
- **Error Handler**: Manages errors gracefully with fallback responses

## Installation

1. Clone the repository
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
   # Edit .env with your API keys:
   # - GEMINI_API_KEY (required for default LLM)
   # - OPENAI_API_KEY (optional)
   # - ANTHROPIC_API_KEY (optional)
   ```
5. Initialize the knowledge base:
   ```bash
   python initialize_kb.py
   ```
6. Run the application:
   ```bash
   python start_server.py
   ```

## Running the Application

```bash
# Start both API and UI (recommended for demos)
python start_server.py

# API only
python start_server.py --mode api

# UI only (requires API to be running separately)
python start_server.py --mode ui

# Direct uvicorn (development)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Endpoints:**
- API Server: `http://localhost:8000`
- API Docs (Swagger): `http://localhost:8000/docs`
- Demo UI: `http://localhost:8501`

## Configuration

Key environment variables (see `.env.example` for full list):

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `DEFAULT_LLM_PROVIDER` | LLM provider (gemini/openai/anthropic) | gemini |
| `CHROMA_PERSIST_DIR` | ChromaDB storage directory | ./chroma_data |
| `HOST` | API server host | 0.0.0.0 |
| `PORT` | API server port | 8000 |
| `DEBUG` | Enable debug mode | false |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint with service info |
| GET | `/info` | Application configuration |
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/chat/completions` | OpenAI-compatible chat (supports streaming) |
| POST | `/api/v1/chat/conversations` | Create/continue conversation |
| GET | `/api/v1/chat/conversations/{id}` | Get conversation history |
| POST | `/api/v1/chat/` | Legacy chat endpoint |
| WS | `/api/v1/chat/ws` | WebSocket chat endpoint |
| POST | `/api/v1/documents/upload` | Document upload |
| GET | `/api/v1/documents/list` | List documents |

### Chat API Example (OpenAI-Compatible)

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "What are the LLP registration fees?"}]
  }'
```

**Response:**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "model": "gemini-2.5-flash",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "The fees for registering an LLP are:\n- Name Reservation: KES 150\n- LLP Registration: KES 10,650\n- LLP Agreement filing: KES 2,000"
    },
    "finish_reason": "stop"
  }],
  "sources": ["brs_extended_info.txt"],
  "confidence": 0.85
}
```

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_main.py
```

## LangGraph Implementation

The system uses LangGraph best practices:

- **TypedDict State**: Strongly-typed state with `Annotated` reducers
- **Conditional Routing**: Smart routing between RAG and conversation agents
- **Checkpointing**: MemorySaver for conversation persistence
- **Error Handling**: Built-in error recovery and max step limits

## Knowledge Base

Documents are intelligently processed for optimal retrieval:

**Section-Aware Chunking:**
- Preserves document structure (headers stay with content)
- Fee schedules, requirements, and processes kept together
- Chunks prefixed with section headers for context

**Query Expansion:**
- Automatic synonym and keyword expansion
- Entity-specific search terms (Company, LLP, Business Name, Foreign)
- Currency-aware matching (KES amounts)

**Documents Ingested:**
- **Acts**: Companies Act, Business Names Act, LLP Act
- **Regulations**: Various regulatory documents
- **FAQs**: Official BRS FAQs
- **Extended Info**: Fees, contacts, processes, timelines

Initialize or rebuild:
```bash
python initialize_kb.py
```

## Phase 1 Status: COMPLETE

- [x] FastAPI web framework with REST + WebSocket endpoints
- [x] LangGraph multi-agent orchestration
- [x] RAG Agent with ChromaDB vector store
- [x] Conversation Agent for general queries
- [x] Router Node for intelligent query routing
- [x] Response Formatter with source citations
- [x] Error Handler with retry logic
- [x] Multi-provider LLM factory (Gemini 2.0 Flash default)
- [x] Section-aware document chunking
- [x] Query expansion for improved retrieval
- [x] OpenAI-compatible API with SSE streaming
- [x] Streamlit Demo UI
- [x] Unit tests (9 passing)
- [x] Knowledge base with extended BRS information

## License

This project is licensed under the MIT License.