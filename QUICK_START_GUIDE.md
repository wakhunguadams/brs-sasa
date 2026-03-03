# BRS-SASA Quick Start Guide

Get BRS-SASA up and running in 5 minutes.

## Prerequisites

- Python 3.11+
- Google Gemini API key
- 2GB RAM minimum

## Installation

### 1. Clone and Setup

```bash
git clone <repository-url>
cd brs-sasa
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env  # Add your API keys
```

Required:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 3. Start Services

```bash
python start_all_services.py
```

Wait 10 seconds for all services to start.

## Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **User Interface** | http://localhost:8501 | Public chat |
| **CRM Dashboard** | http://localhost:8502 | Admin panel |
| **API Docs** | http://localhost:8000/docs | API reference |

## Quick Test

### User Interface (http://localhost:8501)
1. Ask: "How do I register a company?"
2. Ask: "What is my business registration status BN-YZC6PY7"
3. Ask: "Tell me about the Trust Administration Bill"
4. Say: "I suggest they should reduce the fee"
5. Upload a screenshot using 📷 button

### CRM Dashboard (http://localhost:8502)
1. View real-time statistics
2. Check **Feedback** tab for collected feedback
3. Check **Issues** tab for screenshot reports
4. Check **Conversations** tab for chat history
5. Check **Analytics** tab for trends

## Docker Deployment

```bash
# Start with Docker
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

Or use Makefile:
```bash
make up      # Start
make logs    # View logs
make down    # Stop
make health  # Check status
```

## Common Commands

```bash
# Check database
python -c "
from core.database import SessionLocal
from core.models import FeedbackModel, ConversationModel
db = SessionLocal()
print(f'Feedback: {db.query(FeedbackModel).count()}')
print(f'Conversations: {db.query(ConversationModel).count()}')
db.close()
"

# View logs
tail -f logs/brs_sasa.log

# Check health
curl http://localhost:8000/api/v1/health/
```

## Troubleshooting

### Port in use
```bash
lsof -i :8501  # Find process
kill -9 <PID>  # Kill it
```

### Database error
```bash
rm -rf data/
mkdir data
python -c "from core.database import init_db; init_db()"
```

### Services won't start
```bash
# Check logs
tail -f logs/brs_sasa.log

# Restart
pkill -f "streamlit\|uvicorn"
python start_all_services.py
```

## Next Steps

- Read [README.md](README.md) for full documentation
- Check [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) for technical details
- Review [CRM_DASHBOARD_GUIDE.md](CRM_DASHBOARD_GUIDE.md) for admin features
- See [DOCKER_GUIDE.md](DOCKER_GUIDE.md) for deployment options

## Support

- Logs: `logs/brs_sasa.log`
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health/

---

**Ready in 5 minutes!** 🚀
