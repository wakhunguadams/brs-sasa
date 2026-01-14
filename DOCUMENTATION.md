# BRS-SASA: AI-Powered Conversational Platform - Technical Documentation

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

BRS-SASA is an intelligent conversational AI platform for the Business Registration Service (BRS) of Kenya. The platform uses advanced RAG (Retrieval-Augmented Generation) technology to answer questions about business registration, explain draft legislation, collect public feedback, and provide real-time statistics - all through natural conversation.

### Key Features
- **Intelligent FAQ & Troubleshooting**: Answers questions about registration processes, requirements, fees, timelines
- **Legislative Document Assistant**: Makes draft legislation accessible through conversation
- **Public Participation Hub**: Collects citizen feedback on draft legislation
- **Statistics & Analytics**: Provides real-time statistics through natural language queries
- **Smart Escalation**: Recognizes when a query needs human expertise

## Architecture

The system follows a microservices architecture built on FastAPI with the following layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    External Systems                         │
├─────────────────────────────────────────────────────────────┤
│  BRS Website + Chat Widget | CRM System | Database        │
├─────────────────────────────────────────────────────────────┤
│                    BRS-SASA AI Backend                      │
├─────────────────────────────────────────────────────────────┤
│  API Gateway & Load Balancer                              │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Application Server                               │
├─────────────────────────────────────────────────────────────┤
│  LangGraph Multi-Agent System                            │
├─────────────────────────────────────────────────────────────┤
│  AI Factory & LLM Integration                            │
├─────────────────────────────────────────────────────────────┤
│  RAG System (Integrated in Agents)                       │
├─────────────────────────────────────────────────────────────┤
│  Data Storage & Integration Layer                        │
└─────────────────────────────────────────────────────────────┘
```

## Components

### Core Modules

#### 1. FastAPI Web Framework
- RESTful API endpoints for all platform functionality
- WebSocket support for real-time chat interactions
- Built-in automatic API documentation (Swagger/OpenAPI)
- Asynchronous processing for high performance
- Security middleware (authentication, rate limiting)

#### 2. LangGraph Multi-Agent System
The system uses LangGraph for orchestrating multiple AI agents with proper state management:
- **State Management**: Typed state schema with reducer functions for safe state updates
- **Agent Orchestration**: Router, RAG agent, conversation agent, and response formatter nodes
- **Error Handling**: Built-in error handling and retry mechanisms
- **Checkpointing**: Persistent memory across conversations using LangGraph checkpoints

##### State Schema
The system uses a well-defined state schema following LangGraph best practices:
```python
from typing import Annotated, TypedDict
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
    max_steps: int  # Max steps to prevent infinite loops
```

#### 3. LLM Factory Pattern
The LLM factory provides abstraction over multiple LLM providers:
- **Google Gemini** (default)
- **OpenAI GPT**
- **Anthropic Claude**

```python
from llm_factory.factory import LLMFactory

factory = LLMFactory()
llm = factory.get_llm("gemini")  # or "openai", "anthropic"
```

#### 4. AI Agents

##### LangGraph Nodes
The system implements several specialized nodes in the LangGraph workflow:

###### Router Node
Determines which agent should handle the incoming query based on content analysis:
```python
async def router_node(state: BRSState) -> Dict[str, str]:
    # Analyzes user input and routes to appropriate agent
    return {"current_agent": "rag_agent" if is_knowledge_query else "conversation_agent"}
```

###### RAG Agent Node
Handles knowledge-based queries by retrieving relevant documents:
```python
async def rag_agent_node(state: BRSState) -> Dict[str, Any]:
    # Performs RAG operations and returns structured response
    return {
        "response": response_text,
        "sources": sources_list,
        "confidence": confidence_score,
        "retrieved_docs": documents_list
    }
```

###### Conversation Agent Node
Handles general conversation and context management:
```python
async def conversation_agent_node(state: BRSState) -> Dict[str, Any]:
    # Processes conversational queries
    return {
        "response": response_text,
        "sources": sources_list,
        "confidence": confidence_score
    }
```

###### Response Formatter Node
Formats the final response for the user:
```python
async def response_formatter_node(state: BRSState) -> Dict[str, Any]:
    # Formats response with sources and confidence
    return {"response": formatted_response, "messages": [ai_message]}
```

#### 5. Knowledge Base Management
- Document ingestion pipeline for legislation, acts, regulations and FAQs
- Vector database (Chroma) for knowledge storage
- Multi-modal retrieval (text, tables, structured data)
- Semantic search with hybrid retrieval methods

#### 6. Configuration Management
Centralized configuration using Pydantic Settings:
- Environment variable loading
- Type validation
- Default values
- Sensitive data handling

## Installation

### Prerequisites
- Python 3.9+
- pip package manager

### Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd brs-sasa
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

4. Copy the environment file and configure your settings:
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

## Configuration

The application uses environment variables for configuration. The following settings are available:

### Application Settings
- `APP_NAME`: Name of the application (default: "BRS-SASA")
- `DEBUG`: Enable debug mode (default: false)
- `HOST`: Host to bind to (default: "0.0.0.0")
- `PORT`: Port to bind to (default: 8000)

### CORS Settings
- `ALLOWED_ORIGINS`: List of allowed origins for CORS (default: ["*"])

### Database Settings
- `DATABASE_URL`: Database connection string (default: "sqlite:///./brs_sasa.db")

### LLM Settings
- `DEFAULT_LLM_PROVIDER`: Default LLM provider to use (default: "gemini")
- `GEMINI_API_KEY`: Google Gemini API key
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key

### Vector Database Settings
- `VECTOR_DB_TYPE`: Type of vector database to use (default: "chroma")
- `CHROMA_PERSIST_DIR`: Directory for ChromaDB persistence (default: "./chroma_data")

### Logging Settings
- `LOG_LEVEL`: Logging level (default: "INFO")
- `LOG_FORMAT`: Log message format

## API Reference

### Base URL
`http://localhost:8000` (or your configured host/port)

### Endpoints

#### GET /
Root endpoint with basic information about the service.

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
Returns application information and configuration (without sensitive data).

**Response:**
```json
{
  "app_name": "BRS-SASA",
  "debug": false,
  "version": "1.0.0",
  "llm_provider": "gemini",
  "vector_db_type": "chroma",
  "timestamp": 1234567890
}
```

#### GET /api/v1/health/
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1234567890,
  "service": "brs-sasa-api"
}
```

#### POST /api/v1/chat/
Handle a chat request and return a response.

**Request Body:**
```json
{
  "message": "How do I register a business?",
  "history": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": "2023-01-01T00:00:00Z"
    },
    {
      "role": "assistant", 
      "content": "Hello! How can I help you?",
      "timestamp": "2023-01-01T00:00:00Z"
    }
  ],
  "provider": "gemini",
  "context": {}
}
```

**Response:**
```json
{
  "response": "To register a business in Kenya...",
  "sources": ["FAQs.pdf", "CompaniesAct17of2015.pdf"],
  "confidence": 0.85,
  "timestamp": "2023-01-01T00:00:00Z"
}
```

#### WebSocket /api/v1/chat/ws
WebSocket endpoint for real-time chat.

**Send Message:**
```json
{
  "message": "How much does registration cost?"
}
```

**Receive Response:**
```json
{
  "response": "Business registration costs KSH 10,750...",
  "sources": ["FAQs.pdf"],
  "confidence": 0.92
}
```

#### GET /api/v1/documents/list
List all documents in the knowledge base.

**Response:**
```json
{
  "documents": [],
  "count": 0
}
```

## Testing

Run the test suite using pytest:

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest brs_sasa/tests/test_main.py
```

The test suite includes:
- Unit tests for core components
- Integration tests for API endpoints
- Mock-based tests for LLM interactions
- Validation tests for configuration

## Deployment

### Local Development
```bash
python start_server.py
```

Or directly:
```bash
uvicorn brs_sasa.main:app --reload
```

### Production Deployment

For production deployment, consider:

1. Use a WSGI/ASGI server like Gunicorn:
```bash
gunicorn brs_sasa.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

2. Set DEBUG=false in production
3. Use proper reverse proxy (nginx, Apache)
4. Configure SSL/TLS
5. Set up proper logging
6. Use a production-ready database (PostgreSQL)

### Docker Deployment

Create a Dockerfile:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "brs_sasa.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t brs-sasa .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key_here brs-sasa
```

## Phase 1 Implementation Status

Phase 1 includes:
- ✅ FastAPI web framework setup with RESTful API endpoints
- ✅ LangGraph orchestrator to coordinate agent interactions (planned for next phase)
- ✅ Conversation Agent: Handles user interactions and maintains context
- ✅ RAG Agent: Manages document retrieval and knowledge base queries
- ✅ Simple chat interface with WebSocket support
- ✅ AI factory pattern supporting multiple LLM providers
- ✅ Basic RAG system with vector database (Chroma) using local documents
- ✅ Core conversation flow implementation
- ✅ Unit tests and basic documentation

## Future Enhancements

### Phase 2: Knowledge Management
- Document ingestion pipeline for legislation, acts, regulations and FAQs
- Vector database (Chroma/Pinecone) setup and integration
- Multi-modal retrieval capabilities
- Legislative Agent: Specialized for legal document analysis and comparison
- Feedback Agent: Manages public participation and feedback collection

### Phase 3: Advanced Integrations
- CRM system integration for issue escalation and case management
- Database integration for real-time statistics and company registration progress
- Statistics Agent: Handles data queries from BRS database
- Escalation Agent: Routes complex queries to human agents via CRM integration

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.