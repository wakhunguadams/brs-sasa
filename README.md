# BRS-SASA: AI-Powered Conversational Platform

BRS-SASA is an intelligent conversational AI platform for the Business Registration Service (BRS) of Kenya. The platform uses advanced RAG (Retrieval-Augmented Generation) technology to answer questions about business registration, explain draft legislation, collect public feedback, and provide real-time statistics - all through natural conversation.

## Project Structure

```
brs_sasa/
├── api/                    # API endpoints
│   └── v1/
│       ├── __init__.py
│       └── endpoints/
│           ├── chat.py     # Chat functionality
│           ├── health.py   # Health checks
│           └── documents.py # Document management
├── agents/                 # AI agents
│   ├── conversation_agent.py
│   ├── rag_agent.py
│   ├── langgraph_nodes.py  # LangGraph nodes
│   └── __init__.py
├── core/                   # Core utilities
│   ├── config.py          # Configuration
│   ├── logger.py          # Logging setup
│   ├── state.py           # LangGraph state definition
│   ├── workflow.py        # LangGraph workflow
│   └── __init__.py
├── llm_factory/            # LLM provider abstraction
│   └── factory.py
├── models/                 # Data models (to be implemented)
├── schemas/                # Pydantic schemas
│   └── chat.py
├── ui_demo.py              # Streamlit demo UI
├── utils/                  # Utility functions (to be implemented)
├── main.py                 # Application entry point
├── start_server.py         # Server startup script
├── initialize_kb.py        # Knowledge base initialization
├── requirements.txt        # Dependencies
├── .env.example           # Environment configuration template
├── README.md              # This file
├── DOCUMENTATION.md       # Technical documentation
├── LANGGRAPH_BEST_PRACTICES.txt # LangGraph best practices guide
├── acts/                  # Legal documents
├── regulations/           # Regulatory documents
├── BRS-sasa.pdf           # Project specification
├── BRS-sasa.txt           # Project specification (text)
├── FAQs.pdf               # Frequently asked questions
├── IMPLEMENTATION_PLAN.md # Implementation roadmap
└── __init__.py
```

## Features

- **Intelligent FAQ & Troubleshooting**: Answers questions about registration processes, requirements, fees, timelines
- **Legislative Document Assistant**: Makes draft legislation accessible through conversation
- **Public Participation Hub**: Collects citizen feedback on draft legislation
- **Statistics & Analytics**: Provides real-time statistics through natural language queries
- **Smart Escalation**: Recognizes when a query needs human expertise

## Architecture

The system implements a multi-agent architecture using **LangGraph** for proper state management and agent orchestration:

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
│  ├─ Router Node: Determines query routing                │
│  ├─ RAG Agent Node: Handles knowledge queries            │
│  ├─ Conversation Agent Node: Handles general queries      │
│  ├─ Response Formatter Node: Formats responses           │
│  └─ Error Handler Node: Manages errors                   │
├─────────────────────────────────────────────────────────────┤
│  AI Factory & LLM Integration                            │
├─────────────────────────────────────────────────────────────┤
│  RAG System (Integrated in Agents)                       │
├─────────────────────────────────────────────────────────────┤
│  Data Storage & Integration Layer                        │
└─────────────────────────────────────────────────────────────┘
```

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
4. Copy the environment file and configure your settings:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```
5. Run the application:
   ```bash
   python start_server.py
   ```

## Running the Application

The application can be run in different modes:

- **Both API and UI**: `python start_server.py` (default)
- **API only**: `python start_server.py --mode api`
- **UI only**: `python start_server.py --mode ui`

The API server runs on `http://localhost:8000` and the UI on `http://localhost:8501`.

## Configuration

The application uses environment variables for configuration. See `.env.example` for all available options.

## API Endpoints

- `GET /` - Root endpoint with basic info
- `GET /info` - Application information
- `GET /api/v1/health` - Health check
- `POST /api/v1/chat/` - Chat endpoint (uses LangGraph multi-agent system)
- `WS /api/v1/chat/ws` - WebSocket chat endpoint (uses LangGraph multi-agent system)
- `POST /api/v1/documents/upload` - Document upload
- `GET /api/v1/documents/list` - List documents

## LangGraph Multi-Agent System

The system uses LangGraph for orchestrating multiple AI agents with proper state management:

- **State Management**: Typed state schema with reducer functions for safe state updates
- **Agent Orchestration**: Router, RAG agent, conversation agent, and response formatter nodes
- **Error Handling**: Built-in error handling and retry mechanisms
- **Checkpointing**: Persistent memory across conversations using LangGraph checkpoints

## LLM Provider Factory

The application supports multiple LLM providers through a factory pattern:
- Google Gemini (default)
- OpenAI GPT
- Anthropic Claude

To switch providers, specify the provider in the chat request or set the default in configuration.

## Demo UI

The project includes a Streamlit-based demo UI that provides a chat interface to interact with the BRS-SASA system. The UI features:
- Real-time chat interface
- Source citations for responses
- Confidence indicators
- Common query suggestions
- Session management

## Phase 1 Implementation

Phase 1 includes:
- ✅ FastAPI web framework setup with RESTful API endpoints
- ✅ LangGraph orchestrator to coordinate agent interactions
- ✅ Conversation Agent: Handles user interactions and maintains context
- ✅ RAG Agent: Manages document retrieval and knowledge base queries
- ✅ Router Agent: Determines which agent should handle each query
- ✅ Response Formatter: Formats responses with sources and confidence
- ✅ Error Handler: Manages errors in the workflow
- ✅ Simple chat interface with WebSocket support
- ✅ AI factory pattern supporting multiple LLM providers
- ✅ Basic RAG system with vector database (Chroma) using local documents
- ✅ Core conversation flow implementation with proper state management
- ✅ Streamlit demo UI for easy interaction

## License

This project is licensed under the MIT License.