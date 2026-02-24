# BRS-SASA System Architecture

## Complete System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │
│  │  Streamlit UI    │  │   REST API       │  │   WebSocket      │    │
│  │  (Port 8501)     │  │   (Port 8000)    │  │   (Port 8000)    │    │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘    │
│           │                     │                      │               │
│           └─────────────────────┴──────────────────────┘               │
│                                 │                                       │
└─────────────────────────────────┼───────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────────┐
│                         FASTAPI BACKEND                                 │
├─────────────────────────────────┼───────────────────────────────────────┤
│                                 │                                       │
│  ┌──────────────────────────────▼────────────────────────────────┐    │
│  │                    API ENDPOINTS                               │    │
│  │  • /api/v1/chat/message      - Chat endpoint                  │    │
│  │  • /api/v1/chat/ws           - WebSocket endpoint             │    │
│  │  • /api/v1/feedback/submit   - Submit feedback                │    │
│  │  • /api/v1/feedback/list     - List feedback                  │    │
│  │  • /api/v1/feedback/stats    - Feedback statistics            │    │
│  │  • /health/live              - Liveness probe                 │    │
│  │  • /health/ready             - Readiness probe                │    │
│  │  • /metrics                  - Prometheus metrics             │    │
│  └────────────────────────────────┬──────────────────────────────┘    │
│                                   │                                    │
│  ┌────────────────────────────────▼──────────────────────────────┐    │
│  │              MIDDLEWARE & PRODUCTION FEATURES                  │    │
│  │  • Rate Limiting (20-30 req/min per IP)                       │    │
│  │  • Input Validation (Pydantic schemas)                        │    │
│  │  • Request Tracing (X-Request-ID)                             │    │
│  │  • Structured Logging (JSON format)                           │    │
│  │  • CORS (Cross-Origin Resource Sharing)                       │    │
│  └────────────────────────────────┬──────────────────────────────┘    │
│                                   │                                    │
└───────────────────────────────────┼────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼────────────────────────────────────┐
│                    LANGGRAPH MULTI-AGENT SYSTEM                        │
├───────────────────────────────────┼────────────────────────────────────┤
│                                   │                                    │
│  ┌────────────────────────────────▼──────────────────────────────┐    │
│  │                         ROUTER NODE                            │    │
│  │  • LLM-based query classification                             │    │
│  │  • Routes to: RAG | Conversation | Public Participation       │    │
│  │  • Keywords: legislation, knowledge, conversation             │    │
│  └────────────────────────────────┬──────────────────────────────┘    │
│                                   │                                    │
│         ┌─────────────────────────┼─────────────────────────┐         │
│         │                         │                         │         │
│  ┌──────▼──────┐         ┌────────▼────────┐      ┌────────▼────────┐│
│  │  RAG AGENT  │         │  CONVERSATION   │      │    PUBLIC       ││
│  │    NODE     │         │   AGENT NODE    │      │ PARTICIPATION   ││
│  │             │         │                 │      │   AGENT NODE    ││
│  │ • Knowledge │         │ • General chat  │      │                 ││
│  │   base      │         │ • Web search    │      │ • Legislation   ││
│  │   search    │         │ • BRS scraper   │      │   search        ││
│  │ • Legal     │         │ • News search   │      │ • Jurisdiction  ││
│  │   documents │         │ • Contact info  │      │   comparison    ││
│  │             │         │                 │      │ • Feedback      ││
│  │ Tools: 1    │         │ Tools: 5        │      │   collection    ││
│  └──────┬──────┘         └────────┬────────┘      │                 ││
│         │                         │               │ Tools: 4        ││
│         │                         │               └────────┬────────┘│
│         │                         │                        │         │
│         └─────────────────────────┼────────────────────────┘         │
│                                   │                                   │
│  ┌────────────────────────────────▼──────────────────────────────┐   │
│  │                   RESPONSE FORMATTER NODE                      │   │
│  │  • Formats final response                                     │   │
│  │  • Adds sources and confidence                                │   │
│  │  • Creates AI message for history                             │   │
│  └────────────────────────────────┬──────────────────────────────┘   │
│                                   │                                   │
│  ┌────────────────────────────────▼──────────────────────────────┐   │
│  │                      ERROR HANDLER NODE                        │   │
│  │  • Handles errors gracefully                                  │   │
│  │  • Retry logic (max 3 attempts)                               │   │
│  │  • Fallback responses                                         │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼────────────────────────────────────┐
│                              TOOLS LAYER                               │
├───────────────────────────────────┼────────────────────────────────────┤
│                                   │                                    │
│  ┌────────────────────────────────▼──────────────────────────────┐    │
│  │                      BRS TOOLS (5 tools)                       │    │
│  │  1. search_brs_knowledge      - Knowledge base search         │    │
│  │  2. search_web_duckduckgo     - Web search                    │    │
│  │  3. search_brs_news           - News search                   │    │
│  │  4. scrape_brs_website        - Website scraping              │    │
│  │  5. get_brs_contact_info      - Contact information           │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │           PUBLIC PARTICIPATION TOOLS (4 tools)                 │    │
│  │  1. search_legislation_knowledge  - Legislation search        │    │
│  │  2. search_web_duckduckgo         - Web search (shared)       │    │
│  │  3. search_brs_news               - News search (shared)      │    │
│  │  4. collect_legislation_feedback  - Feedback collection       │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼────────────────────────────────────┐
│                          DATA & STORAGE LAYER                          │
├───────────────────────────────────┼────────────────────────────────────┤
│                                   │                                    │
│  ┌────────────────────────────────▼──────────────────────────────┐    │
│  │                    CHROMADB KNOWLEDGE BASE                     │    │
│  │  • 4,624 total chunks                                         │    │
│  │    - 4,485 BRS documents (acts, regulations, FAQs)           │    │
│  │    - 139 legislation chunks (Trust Administration Bill)       │    │
│  │  • Vector embeddings for semantic search                      │    │
│  │  • Metadata filtering (type: legislation, type: brs)          │    │
│  │  • Section-aware chunking                                     │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    SQLITE DATABASE                             │    │
│  │  Tables:                                                       │    │
│  │  • conversations  - Conversation metadata                     │    │
│  │  • messages       - Chat message history                      │    │
│  │  • feedback       - Public participation feedback             │    │
│  │                                                                │    │
│  │  Feedback Fields:                                             │    │
│  │  • user_query, feedback_text, legislation_section             │    │
│  │  • sentiment (positive/negative/neutral/suggestion)           │    │
│  │  • created_at, feedback_metadata                              │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼────────────────────────────────────┐
│                        EXTERNAL SERVICES                               │
├───────────────────────────────────┼────────────────────────────────────┤
│                                   │                                    │
│  ┌────────────────────────────────▼──────────────────────────────┐    │
│  │                    LLM PROVIDERS                               │    │
│  │  • Google Gemini 2.0 Flash (primary)                          │    │
│  │  • OpenAI GPT-4 (optional)                                    │    │
│  │  • Anthropic Claude (optional)                                │    │
│  │                                                                │    │
│  │  Features:                                                     │    │
│  │  • Retry logic (3 attempts, exponential backoff)              │    │
│  │  • Error handling and fallbacks                               │    │
│  │  • Prometheus metrics tracking                                │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    WEB SERVICES                                │    │
│  │  • DuckDuckGo Search API - Web search                         │    │
│  │  • BRS Website (https://brs.go.ke/) - Official data          │    │
│  │  • HTTP requests with retry logic                             │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼────────────────────────────────────┐
│                      MONITORING & OBSERVABILITY                        │
├───────────────────────────────────┼────────────────────────────────────┤
│                                   │                                    │
│  ┌────────────────────────────────▼──────────────────────────────┐    │
│  │                    PROMETHEUS METRICS                          │    │
│  │  • brs_sasa_requests_total       - Request count by endpoint  │    │
│  │  • brs_sasa_request_duration_seconds - Request duration       │    │
│  │  • brs_sasa_llm_calls_total      - LLM API calls              │    │
│  │                                                                │    │
│  │  Exposed at: /metrics                                         │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    STRUCTURED LOGGING                          │    │
│  │  • JSON format for log aggregation                            │    │
│  │  • Log levels: DEBUG, INFO, WARNING, ERROR                    │    │
│  │  • Request tracing with X-Request-ID                          │    │
│  │  • Agent routing and tool usage tracking                      │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Examples

### Example 1: Business Registration Query
```
User: "How do I register a company in Kenya?"
  ↓
FastAPI Endpoint (/api/v1/chat/message)
  ↓
Router Node (LLM classification)
  ↓ "knowledge" query
RAG Agent Node
  ↓
search_brs_knowledge tool
  ↓
ChromaDB (search BRS documents)
  ↓
Response Formatter Node
  ↓
User: "To register a company in Kenya, you need to..."
```

### Example 2: Current Information Query
```
User: "Who is the Director General of BRS?"
  ↓
FastAPI Endpoint
  ↓
Router Node
  ↓ "conversation" query
Conversation Agent Node
  ↓
scrape_brs_website tool
  ↓
BRS Website (https://brs.go.ke/)
  ↓
Response Formatter Node
  ↓
User: "The Director General of BRS is..."
```

### Example 3: Legislation Query
```
User: "What is the Trust Administration Bill about?"
  ↓
FastAPI Endpoint
  ↓
Router Node
  ↓ "legislation" query
Public Participation Agent Node
  ↓
search_legislation_knowledge tool
  ↓
ChromaDB (filter: type="legislation")
  ↓
Response Formatter Node
  ↓
User: "The Trust Administration Bill 2025 is designed to..."
```

### Example 4: Feedback Collection
```
User: "I think the Trust Bill should include more protections"
  ↓
FastAPI Endpoint
  ↓
Router Node
  ↓ "legislation" query
Public Participation Agent Node
  ↓
collect_legislation_feedback tool
  ↓
SQLite Database (feedback table)
  ↓
Response Formatter Node
  ↓
User: "Thank you for your feedback! Your input has been recorded..."
```

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Async Runtime**: asyncio, uvicorn
- **Agent Framework**: LangGraph 0.2+
- **LLM**: Google Gemini 2.0 Flash (primary)

### Data Storage
- **Vector Database**: ChromaDB (persistent)
- **Relational Database**: SQLite (SQLAlchemy ORM)
- **Embeddings**: ChromaDB default embeddings

### Tools & Integrations
- **Web Search**: DuckDuckGo (ddgs library)
- **Web Scraping**: httpx + BeautifulSoup4
- **Document Processing**: python-docx, PyPDF2

### Production Features
- **Rate Limiting**: slowapi
- **Retry Logic**: tenacity
- **Logging**: python-json-logger
- **Metrics**: prometheus-client
- **Validation**: Pydantic

### Development
- **Testing**: pytest, pytest-asyncio
- **UI Demo**: Streamlit
- **Documentation**: Markdown

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION DEPLOYMENT                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Load Balancer / Reverse Proxy           │  │
│  │                    (nginx/traefik)                   │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │              BRS-SASA API Instances                  │  │
│  │         (Multiple instances for scaling)             │  │
│  │                                                       │  │
│  │  Instance 1  │  Instance 2  │  Instance 3            │  │
│  │  Port 8000   │  Port 8001   │  Port 8002             │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │              Shared Data Layer                       │  │
│  │                                                       │  │
│  │  • ChromaDB (persistent volume)                      │  │
│  │  • SQLite/PostgreSQL (database)                      │  │
│  │  • Logs (centralized logging)                        │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Monitoring Stack                         │  │
│  │                                                       │  │
│  │  • Prometheus (metrics collection)                   │  │
│  │  • Grafana (visualization)                           │  │
│  │  • ELK Stack (log aggregation)                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Security Considerations

1. **Rate Limiting**: Prevents abuse (20-30 req/min per IP)
2. **Input Validation**: Pydantic schemas validate all inputs
3. **SQL Injection**: Protected by SQLAlchemy ORM
4. **CORS**: Configured for specific origins
5. **API Keys**: Environment variables, never committed
6. **Request Tracing**: X-Request-ID for audit trails
7. **Error Handling**: No sensitive data in error messages

## Performance Characteristics

- **Average Response Time**: 2-10 seconds (depending on query type)
- **Concurrent Users**: Tested with 10 concurrent users
- **Knowledge Base Search**: Sub-second vector search
- **Rate Limit**: 20-30 requests/min per IP
- **Uptime**: 99.9% target (with health checks)

## Scalability

- **Horizontal Scaling**: Multiple API instances behind load balancer
- **Database**: Can migrate from SQLite to PostgreSQL
- **Caching**: Can add Redis for session/response caching
- **CDN**: Static assets can be served via CDN
- **Queue**: Can add Celery for async tasks

---

**Last Updated**: February 10, 2026
**Version**: 1.0.0
**Status**: Production Ready
