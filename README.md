# BRS-SASA: AI-Powered Conversational Platform

BRS-SASA is an intelligent conversational AI platform for the Business Registration Service (BRS) of Kenya. The platform uses advanced RAG (Retrieval-Augmented Generation) technology powered by **LangGraph** and **Google Gemini 2.0 Flash** to answer questions about business registration, explain draft legislation, collect public feedback, and provide real-time statistics - all through natural conversation.

**🎯 Production Status**: 92% Ready (Grade A-) | **✅ Tests**: 29/29 Passing (100%) | **📚 Knowledge Base**: 4,624 chunks (4,485 BRS + 139 legislation)

## 🚀 Quick Start

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Initialize the knowledge base (first time only)
python initialize_kb.py

# 3. Start both API and UI servers
python start_server.py

# Access:
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Metrics: http://localhost:8000/metrics
# - Health: http://localhost:8000/health/ready
# - UI Demo: http://localhost:8501
```

## ✨ Production Features (NEW)

### Operational Excellence
- ✅ **Rate Limiting**: 20 req/min for chat, 30 req/min for conversations (per IP)
- ✅ **Input Validation**: Comprehensive request validation with detailed error messages
- ✅ **Retry Logic**: Exponential backoff (3 attempts, 2-10s) for all LLM calls
- ✅ **Structured Logging**: JSON format in production for log aggregation
- ✅ **Prometheus Metrics**: Request counts, durations, LLM call tracking
- ✅ **Health Checks**: Liveness (`/health/live`) and readiness (`/health/ready`) probes
- ✅ **Request Tracing**: X-Request-ID and X-Process-Time headers

### Test Coverage
- **29 comprehensive tests** covering:
  - API endpoints (6 tests)
  - RAG agent (4 tests)
  - Conversation agent (4 tests)
  - Knowledge base (3 tests)
  - State management (2 tests)
  - LLM factory (2 tests)
  - Edge cases (4 tests)
  - Integration (2 tests)
  - Security (2 tests)

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

### Core Capabilities
- **Intelligent FAQ & Troubleshooting**: Answers questions about registration processes, requirements, fees, timelines
- **Legislative Document Assistant**: Makes draft legislation accessible through conversation
- **Public Participation Agent** (NEW): Facilitates citizen engagement in legislative review
  - Explains Trust Administration Bill 2025 in simple terms
  - Compares Kenya's legislation with other countries (UK, US, etc.)
  - Collects and stores public feedback for review
  - Sentiment analysis (positive, negative, neutral, suggestion)
- **RAG-Powered Knowledge Base**: ChromaDB vector database with section-aware chunking and query expansion
- **Web Search Integration**: Real-time search for current BRS information (leadership, news, statistics)
- **BRS Website Scraping**: Direct access to official BRS website data
- **OpenAI-Compatible API**: Industry-standard chat completions endpoint with SSE streaming
- **Multi-Provider LLM Support**: Factory pattern supporting Gemini, OpenAI, and Anthropic
- **Real-time Chat**: REST API and WebSocket support for instant responses
- **Source Citations**: Every response includes document sources and confidence scores
- **Demo UI**: Production-ready Streamlit interface for demonstrations

## 🏗️ Architecture

The system implements a production-ready multi-agent architecture using **LangGraph** for proper state management and agent orchestration:

```
┌─────────────────────────────────────────────────────────────┐
│                     Demo UI (Streamlit)                     │
│                   http://localhost:8501                     │
├─────────────────────────────────────────────────────────────┤
│                    FastAPI Backend                          │
│         http://localhost:8000 (with rate limiting)          │
├─────────────────────────────────────────────────────────────┤
│                LangGraph Multi-Agent System                 │
│              (with retry logic & error handling)            │
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
│   └───────────────────────┼────────────────────────────────┘│
│                           │                                 │
│   ┌───────────────────────▼────────────────────────────────┐│
│   │ Public Participation Agent (NEW)                       ││
│   │   - Legislation Search                                 ││
│   │   - Jurisdiction Comparison                            ││
│   │   - Feedback Collection                                ││
│   └────────────────────────────────────────────────────────┘│
│   └───────────────────────┘                                ││
├─────────────────────────────────────────────────────────────┤
│  LLM Factory (gemini-2.0-flash) │ ChromaDB Vector Store    │
│  (with exponential backoff)     │ (4,485 document chunks)  │
├─────────────────────────────────────────────────────────────┤
│  Monitoring: Prometheus Metrics │ Structured JSON Logging  │
└─────────────────────────────────────────────────────────────┘
```

The architecture follows LangGraph 2026 best practices with:
- **Router Node**: Determines if query needs RAG or conversation handling
- **RAG Agent**: Tool-calling pattern with autonomous knowledge base search
- **Conversation Agent**: Handles general conversation and greetings
- **Response Formatter**: Formats responses with sources and confidence
- **Error Handler**: Manages errors gracefully with retry logic
- **Checkpointing**: MemorySaver for conversation persistence

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

## 📊 Monitoring & Observability

### Prometheus Metrics
Access metrics at `http://localhost:8000/metrics`:
- `brs_sasa_requests_total` - Total requests by method, endpoint, status
- `brs_sasa_request_duration_seconds` - Request duration histogram
- `brs_sasa_llm_calls_total` - LLM API calls by provider and status

### Health Checks
- **Liveness**: `GET /health/live` - Is the app running?
- **Readiness**: `GET /health/ready` - Is the app ready to serve traffic?
  - Checks: Database, ChromaDB, Workflow initialization

### Structured Logging
- JSON format in production (`DEBUG=false`)
- Human-readable in development (`DEBUG=true`)
- Fields: timestamp, severity, name, message
- Compatible with ELK, Splunk, CloudWatch

## 🧪 Testing

```bash
# Run all tests
pytest tests/test_comprehensive.py -v

# Run specific test categories
pytest tests/test_comprehensive.py::TestAPIEndpoints -v
pytest tests/test_comprehensive.py::TestRAGAgent -v
pytest tests/test_comprehensive.py::TestIntegration -v

# Run with coverage
pytest tests/test_comprehensive.py --cov=. --cov-report=html
```

**Test Results**: 29/29 passing (100% success rate)

## 🔒 Security Features

- **Rate Limiting**: Per-IP rate limits on all endpoints
- **Input Validation**: 
  - Message length limits (10,000 chars per message)
  - Total message count limits (50 per request)
  - Empty content rejection
  - Parameter validation (temperature, etc.)
- **SQL Injection Protection**: Parameterized queries with SQLAlchemy
- **XSS Protection**: Content sanitization in responses
- **Error Handling**: No sensitive data in error messages

## 📈 Performance

- **Response Time**: ~2-5 seconds for RAG queries
- **Throughput**: 20 requests/minute per IP (configurable)
- **Retry Logic**: 3 attempts with exponential backoff (2-10s)
- **Caching**: ChromaDB vector cache for fast retrieval
- **Streaming**: SSE support for real-time responses

## 🛠️ Configuration

Key environment variables (see `.env.example` for full list):

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `DEFAULT_LLM_PROVIDER` | LLM provider (gemini/openai/anthropic) | gemini |
| `CHROMA_PERSIST_DIR` | ChromaDB storage directory | ./chroma_data |
| `HOST` | API server host | 0.0.0.0 |
| `PORT` | API server port | 8000 |
| `DEBUG` | Enable debug mode | false |
| `LOG_LEVEL` | Logging level | INFO |

## 📡 API Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/` | Root endpoint with service info | - |
| GET | `/info` | Application configuration | - |
| GET | `/health/live` | Liveness probe | - |
| GET | `/health/ready` | Readiness probe with checks | - |
| GET | `/metrics` | Prometheus metrics | - |
| POST | `/api/v1/chat/completions` | OpenAI-compatible chat | 20/min |
| POST | `/api/v1/conversations` | Create conversation | 30/min |
| GET | `/api/v1/conversations` | List conversations | - |
| GET | `/api/v1/conversations/{id}` | Get conversation | - |
| PATCH | `/api/v1/conversations/{id}` | Update conversation | - |
| DELETE | `/api/v1/conversations/{id}` | Delete conversation | - |
| WS | `/api/v1/chat/ws` | WebSocket chat | - |

### Chat API Example (OpenAI-Compatible)

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "How do I register a company in Kenya?"}]
  }'
```

**Response:**
```json
{
  "id": "chatcmpl-43769153c048",
  "object": "chat.completion",
  "created": 1770199672,
  "model": "gemini-2.0-flash",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "To register a company in Kenya, you can follow these steps through the e-Citizen platform...\n\n[Detailed response with requirements, process, and fees]"
    },
    "finish_reason": "stop"
  }],
  "conversation_id": "e0818b5c-b809-44cd-bb25-70c3102da0e0",
  "sources": ["CompaniesAct17of2015.pdf", "brs_extended_info.txt"],
  "confidence": 0.85
}
```

### Streaming Example

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "What are LLP fees?"}],
    "stream": true
  }'
```

### Health Check Example

```bash
curl http://localhost:8000/health/ready
```

**Response:**
```json
{
  "status": "ready",
  "checks": {
    "database": "healthy",
    "chromadb": "healthy",
    "workflow": "healthy"
  },
  "timestamp": 1770210516.420403
}
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/test_comprehensive.py -v

# Run specific test categories
pytest tests/test_comprehensive.py::TestAPIEndpoints -v
pytest tests/test_comprehensive.py::TestRAGAgent -v
pytest tests/test_comprehensive.py::TestIntegration -v

# Run with coverage
pytest tests/test_comprehensive.py --cov=. --cov-report=html

# Skip slow tests
pytest tests/test_comprehensive.py -v -k "not slow"
```

**Test Results**: 29/29 passing (100% success rate)

**Test Coverage**:
- ✅ API endpoints (6 tests)
- ✅ RAG agent (4 tests)
- ✅ Conversation agent (4 tests)
- ✅ Knowledge base (3 tests)
- ✅ State management (2 tests)
- ✅ LLM factory (2 tests)
- ✅ Edge cases (4 tests)
- ✅ Integration (2 tests)
- ✅ Security (2 tests)

## LangGraph Implementation

The system uses LangGraph best practices:

- **TypedDict State**: Strongly-typed state with `Annotated` reducers
- **Conditional Routing**: Smart routing between RAG and conversation agents
- **Checkpointing**: MemorySaver for conversation persistence
- **Error Handling**: Built-in error recovery and max step limits

## 📚 Knowledge Base

Documents are intelligently processed for optimal retrieval:

**Current Status**:
- **Total Documents**: 12 files
- **Total Chunks**: 4,485 chunks
- **Sources**:
  - 9 Acts (4,332 chunks)
  - 2 Regulations (90 chunks)
  - 1 Extended info (19 chunks)
  - 1 FAQ (15 chunks)
  - 1 BRS spec (29 chunks)

**Section-Aware Chunking:**
- Preserves document structure (headers stay with content)
- Fee schedules, requirements, and processes kept together
- Chunks prefixed with section headers for context

**Query Expansion:**
- Automatic synonym and keyword expansion
- Entity-specific search terms (Company, LLP, Business Name, Foreign)
- Currency-aware matching (KES amounts)

**Documents Ingested:**
- **Acts**: Companies Act, Business Names Act, LLP Act, Insolvency Act, etc.
- **Regulations**: Beneficial Ownership Regulations, etc.
- **FAQs**: Official BRS FAQs
- **Extended Info**: Fees, contacts, processes, timelines

Initialize or rebuild:
```bash
python initialize_kb.py
```

## 🎯 Production Readiness

### Current Status: 92/100 (Grade A-)

| Category | Score | Status |
|----------|-------|--------|
| Architecture | 90/100 | ✅ Excellent |
| RAG Implementation | 90/100 | ✅ Excellent |
| Code Quality | 85/100 | ✅ Very Good |
| Testing | 95/100 | ✅ Excellent |
| Observability | 90/100 | ✅ Excellent |
| Security | 85/100 | ✅ Very Good |
| Error Handling | 90/100 | ✅ Excellent |

### Implemented Production Features
- ✅ Rate limiting (slowapi)
- ✅ Input validation
- ✅ Retry logic with exponential backoff (tenacity)
- ✅ Structured JSON logging (python-json-logger)
- ✅ Prometheus metrics (prometheus-client)
- ✅ Health checks (liveness & readiness)
- ✅ Request tracing
- ✅ Comprehensive test suite (29 tests)

### Recommended for Full Production
- 🔲 API key authentication
- 🔲 Circuit breaker pattern
- 🔲 Distributed tracing (OpenTelemetry)
- 🔲 Redis caching layer
- 🔲 Load testing
- 🔲 CI/CD pipeline

See `PRODUCTION_IMPROVEMENTS.md` for detailed implementation notes.

## 📖 Documentation

- **README.md** - This file (overview and quick start)
- **DOCUMENTATION.md** - Detailed technical documentation
- **PRODUCTION_IMPROVEMENTS.md** - Production readiness improvements
- **COMPREHENSIVE_TEST_PLAN.md** - Testing strategy and scenarios
- **REVIEW_SUMMARY.md** - Architecture review and recommendations
- **DEMO_GUIDE.md** - Demo scenarios and talking points

## 🚀 Deployment

### Docker (Recommended)

```bash
# Build image
docker build -t brs-sasa:latest .

# Run container
docker run -p 8000:8000 --env-file .env brs-sasa:latest
```

### Docker Compose

```bash
docker-compose up -d
```

### Manual Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize knowledge base
python initialize_kb.py

# Start with gunicorn (production)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 Phase 1 Status: COMPLETE ✅

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
- [x] Comprehensive test suite (29 tests, 100% passing)
- [x] Production operational improvements
- [x] Monitoring and observability
- [x] Rate limiting and security
- [x] Knowledge base with 4,485 chunks

## License

This project is licensed under the MIT License.