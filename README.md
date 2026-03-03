# BRS-SASA: AI-Powered Business Registration Assistant

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

BRS-SASA is an intelligent AI assistant for the Business Registration Service (BRS) of Kenya. It uses a multi-agent architecture powered by LangGraph and Google Gemini to help users with business registration, legislation review, and application tracking.

## 🌟 Features

### Core Capabilities
- **Multi-Agent System**: 5 specialized agents (Router, RAG, Conversation, Public Participation, Application Assistant)
- **Business Registration Guidance**: Step-by-step help with company registration in Kenya
- **Application Tracking**: Real-time status checks using BRS API integration
- **Legislation Review**: Public participation on Trust Administration Bill 2025
- **Screenshot Analysis**: AI-powered issue detection and troubleshooting
- **Feedback Collection**: Automated sentiment analysis and CRM integration
- **Knowledge Base**: RAG system with BRS documentation and legislation

### User Interfaces
- **Public Chat Interface** (Port 8501): Streamlit-based user-facing chatbot
- **CRM Dashboard** (Port 8502): Admin interface for monitoring and analytics
- **API Documentation** (Port 8000): FastAPI with interactive Swagger docs

### Technical Features
- **Streaming Responses**: Real-time message streaming with SSE
- **Conversation Management**: Persistent chat history with SQLite
- **Multi-Provider LLM**: Support for Gemini, OpenAI, and Anthropic
- **Vector Search**: ChromaDB for semantic document retrieval
- **Web Search**: DuckDuckGo integration for current information
- **Docker Support**: Full containerization with docker-compose

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Gemini API key (required)
- 2GB RAM minimum
- 5GB disk space

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd brs-sasa
```

2. **Set up environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
nano .env  # Add your API keys
```

Required variables:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite:///./data/brs_sasa.db
CHROMA_PERSIST_DIR=./chroma_data
```

4. **Start all services**
```bash
python start_all_services.py
```

### Access Points
- **User Interface**: http://localhost:8501
- **CRM Dashboard**: http://localhost:8502
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health/

## 🐳 Docker Deployment

### Quick Start with Docker

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Using Makefile

```bash
# Start development
make up

# View logs
make logs

# Stop services
make down

# Check health
make health

# Backup data
make backup
```

See [DOCKER_GUIDE.md](DOCKER_GUIDE.md) for detailed Docker documentation.

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) | Step-by-step setup and usage guide |
| [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) | Technical architecture and design |
| [CRM_DASHBOARD_GUIDE.md](CRM_DASHBOARD_GUIDE.md) | Admin dashboard documentation |
| [DOCKER_GUIDE.md](DOCKER_GUIDE.md) | Complete Docker deployment guide |
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | Production deployment checklist |
| [DEMO_GUIDE.md](DEMO_GUIDE.md) | Demo scenarios and workflows |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Quick command reference |

## 🏗️ Architecture

### Multi-Agent System

```
┌─────────────────────────────────────────────────────────┐
│                    User Query                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
            ┌────────────────┐
            │  Router Agent  │  (LLM-based classification)
            └────────┬───────┘
                     │
        ┌────────────┼────────────┬──────────────┐
        │            │            │              │
        ▼            ▼            ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│   RAG    │  │Conversa- │  │  Public  │  │  App     │
│  Agent   │  │tion Agent│  │Particip. │  │Assistant │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
     │             │              │              │
     └─────────────┴──────────────┴──────────────┘
                     │
                     ▼
            ┌────────────────┐
            │    Response    │
            │   Formatter    │
            └────────────────┘
```

### Technology Stack
- **Backend**: FastAPI, LangGraph, LangChain
- **LLM**: Google Gemini 2.0 Flash (primary)
- **Database**: SQLite with SQLAlchemy ORM
- **Vector Store**: ChromaDB
- **Frontend**: Streamlit
- **Deployment**: Docker, Docker Compose

## 🎯 Use Cases

### 1. Business Registration
```
User: "How do I register a company in Kenya?"
System: Provides step-by-step guide with requirements and fees
```

### 2. Application Tracking
```
User: "What is my business registration status BN-YZC6PY7"
System: Checks BRS API and returns current status
```

### 3. Legislation Review
```
User: "Tell me about the Trust Administration Bill"
System: Explains bill provisions and collects feedback
```

### 4. Issue Reporting
```
User: [Uploads screenshot of error]
System: Analyzes image, identifies issue, provides solution
```

## 🔧 Development

### Project Structure
```
brs-sasa/
├── agents/              # LangGraph agent implementations
├── api/                 # FastAPI endpoints
├── core/                # Core utilities and config
├── tools/               # LangChain tools
├── data/                # SQLite database
├── chroma_data/         # Vector store
├── logs/                # Application logs
├── ui_demo.py           # User interface
├── crm_dashboard.py     # Admin dashboard
├── main.py              # FastAPI application
└── start_all_services.py # Startup script
```

### Running Tests
```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run specific test
python test_feedback_fix.py

# Check database
python verify_database.py
```

### Adding New Features
1. Create agent in `agents/` directory
2. Add tools in `tools/` directory
3. Update router in `agents/langgraph_nodes.py`
4. Add API endpoints in `api/v1/endpoints/`
5. Update documentation

## 📊 CRM Dashboard

The admin dashboard provides:
- **Real-time Statistics**: Feedback, issues, conversations, messages
- **Feedback Management**: Filter by sentiment, view trends
- **Issue Tracking**: Screenshot analysis results, resolution status
- **Conversation History**: Full chat logs with metadata
- **Analytics**: Time-based charts and trends

Access at http://localhost:8502

See [CRM_DASHBOARD_GUIDE.md](CRM_DASHBOARD_GUIDE.md) for details.

## 🔐 Security

- Input validation and sanitization
- Rate limiting with SlowAPI
- SQL injection prevention with ORM
- XSS protection in UI
- Environment variable management
- Non-root Docker containers
- Health check endpoints

## 🚀 Deployment

### Development
```bash
python start_all_services.py
```

### Production with Docker
```bash
docker compose -f docker-compose.prod.yml up -d
```

### Production Checklist
- [ ] Set DEBUG=false
- [ ] Use strong API keys
- [ ] Configure HTTPS/SSL
- [ ] Set up firewall rules
- [ ] Enable monitoring
- [ ] Configure backups
- [ ] Review security settings

See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for complete list.

## 📈 Performance

- **Response Time**: < 2s for most queries
- **Concurrent Users**: Supports 100+ simultaneous connections
- **Database**: SQLite (development), PostgreSQL recommended for production
- **Caching**: ChromaDB vector cache, LLM response caching
- **Scalability**: Horizontal scaling with Docker replicas

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is proprietary software developed for the Business Registration Service (BRS) of Kenya.

## 🆘 Support

### Common Issues

**Services won't start**
```bash
# Check if ports are in use
lsof -i :8000
lsof -i :8501
lsof -i :8502

# Kill processes if needed
kill -9 <PID>
```

**Database errors**
```bash
# Reset database
rm -rf data/
mkdir data
python -c "from core.database import init_db; init_db()"
```

**Docker issues**
```bash
# Rebuild without cache
docker compose build --no-cache
docker compose up -d
```

### Getting Help
- Check logs: `tail -f logs/brs_sasa.log`
- View API docs: http://localhost:8000/docs
- Review documentation in `docs/` directory
- Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

## 📞 Contact

- **BRS Website**: https://brs.go.ke
- **Email**: eo@brs.go.ke
- **Phone**: +254 11 112 7000

## 🙏 Acknowledgments

- Business Registration Service (BRS) of Kenya
- LangChain and LangGraph teams
- Google Gemini AI
- Streamlit community

---

**Version**: 1.0.0  
**Last Updated**: March 2026  
**Status**: Production Ready ✅
