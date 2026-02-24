# BRS-SASA Quick Reference Guide

## 🚀 Quick Start Commands

```bash
# Start the system
source venv/bin/activate
python start_server.py

# Initialize knowledge base (first time only)
python initialize_kb.py

# Process legislation documents
python process_legislation.py

# Run tests
pytest tests/test_comprehensive.py -v
python core_functionality_test.py
python test_public_participation.py

# Run demos
python demo_public_participation.py
```

## 📡 API Endpoints

### Chat Endpoints
```bash
# Send a message
POST /api/v1/chat/message
Body: {"message": "Your question", "conversation_id": "user123"}

# WebSocket connection
WS /api/v1/chat/ws
```

### Feedback Endpoints
```bash
# Submit feedback
POST /api/v1/feedback/submit
Body: {"user_query": "...", "feedback_text": "...", "sentiment": "positive"}

# List feedback
GET /api/v1/feedback/list?limit=50&sentiment=positive

# Get statistics
GET /api/v1/feedback/stats
```

### Health & Monitoring
```bash
# Liveness probe
GET /health/live

# Readiness probe
GET /health/ready

# Prometheus metrics
GET /metrics
```

## 🤖 Agent Routing

### RAG Agent (Knowledge Base)
**Triggers**: business, register, company, fee, cost, process, requirements, documents
**Tools**: search_brs_knowledge
**Example**: "How do I register a company in Kenya?"

### Conversation Agent (General Chat + Web)
**Triggers**: hello, hi, who are you, greetings, current information
**Tools**: search_web_duckduckgo, search_brs_news, scrape_brs_website, get_brs_contact_info
**Example**: "Who is the Director General of BRS?"

### Public Participation Agent (Legislation)
**Triggers**: trust, bill, law, legislation, public participation, feedback, jurisdiction
**Tools**: search_legislation_knowledge, search_web_duckduckgo, search_brs_news, collect_legislation_feedback
**Example**: "What is the Trust Administration Bill about?"

## 🛠️ Tools Reference

### BRS Tools (5 total)
1. **search_brs_knowledge** - Search knowledge base for BRS information
2. **search_web_duckduckgo** - General web search
3. **search_brs_news** - Search for BRS news and updates
4. **scrape_brs_website** - Scrape official BRS website
5. **get_brs_contact_info** - Get current BRS contact information

### Public Participation Tools (4 total)
1. **search_legislation_knowledge** - Search Trust Administration Bill 2025
2. **search_web_duckduckgo** - Web search (shared)
3. **search_brs_news** - News search (shared)
4. **collect_legislation_feedback** - Collect and store feedback

## 📊 System Statistics

- **Agents**: 3 (RAG, Conversation, Public Participation)
- **Tools**: 8 total (5 BRS + 4 Public Participation, 1 shared)
- **Knowledge Base**: 4,624 chunks (4,485 BRS + 139 legislation)
- **API Endpoints**: 8 (chat, health, feedback)
- **Database Tables**: 3 (conversations, messages, feedback)
- **Test Coverage**: 100% (29/29 tests passing)
- **Production Grade**: A- (92/100)

## 🔧 Configuration

### Environment Variables
```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Database
DATABASE_URL=sqlite:///./brs_sasa.db

# Knowledge Base
CHROMA_PERSIST_DIR=./chroma_data
```

### Rate Limits
- Chat endpoint: 20 requests/min per IP
- Conversation list: 30 requests/min per IP
- Feedback endpoints: 30 requests/min per IP

## 📝 Common Tasks

### Add New Documents to Knowledge Base
```bash
# 1. Place documents in acts/ or regulations/ folder
# 2. Run initialization
python initialize_kb.py
```

### Add New Legislation
```bash
# 1. Convert to .txt if needed
libreoffice --headless --convert-to txt --outdir legislation your-bill.doc

# 2. Update process_legislation.py with new file
# 3. Run processing
python process_legislation.py
```

### View Logs
```bash
# Real-time logs
tail -f logs/brs_sasa.log

# Search for errors
grep "ERROR" logs/brs_sasa.log

# View agent routing
grep "Routing to" logs/brs_sasa.log
```

### Check System Health
```bash
# Health check
curl http://localhost:8000/health/ready

# Metrics
curl http://localhost:8000/metrics

# Feedback stats
curl http://localhost:8000/api/v1/feedback/stats
```

## 🧪 Testing

### Run All Tests
```bash
# Comprehensive test suite
pytest tests/test_comprehensive.py -v

# Core functionality
python core_functionality_test.py

# Public participation
python test_public_participation.py

# Stress test
python stress_test.py
```

### Test Specific Features
```bash
# Web search
python test_web_search.py

# BRS scraper
python test_brs_scraper.py

# Endpoints
python test_endpoints_final.py
```

## 🐛 Troubleshooting

### Issue: Knowledge base not initialized
```bash
# Solution
python initialize_kb.py
```

### Issue: LLM API errors
```bash
# Check API key
echo $GEMINI_API_KEY

# Check logs
grep "LLM" logs/brs_sasa.log
```

### Issue: Rate limit exceeded
```bash
# Wait 1 minute or use different IP
# Check rate limit headers in response
```

### Issue: Feedback not saving
```bash
# Check database
sqlite3 brs_sasa.db "SELECT COUNT(*) FROM feedback;"

# Reinitialize database
python -c "from core.database import init_db; init_db()"
```

## 📚 Documentation Files

### User Documentation
- `README.md` - Main documentation
- `QUICK_START.md` - Quick start guide
- `QUICK_REFERENCE.md` - This file
- `DEMO_GUIDE.md` - Demo instructions

### Feature Documentation
- `PUBLIC_PARTICIPATION_FEATURE.md` - Public participation
- `WEB_SEARCH_FEATURE.md` - Web search
- `BRS_WEBSITE_SCRAPER_FEATURE.md` - Website scraper

### Technical Documentation
- `SYSTEM_ARCHITECTURE.md` - System architecture
- `PRODUCTION_IMPROVEMENTS.md` - Production features
- `SESSION_SUMMARY.md` - Development summary

## 🎯 Example Queries

### Business Registration
```
"How do I register a company in Kenya?"
"What are the fees for business registration?"
"What documents do I need to register a partnership?"
```

### Current Information
```
"Who is the Director General of BRS?"
"What is the contact information for BRS?"
"What are the latest news about BRS?"
```

### Legislation
```
"What is the Trust Administration Bill 2025 about?"
"How does Kenya's Trust Bill compare to UK trust laws?"
"I think the Trust Bill should include more protections"
```

### General
```
"Hello, what can you help me with?"
"Who created you?"
"What services does BRS provide?"
```

## 🔐 Security Best Practices

1. **Never commit API keys** - Use .env file
2. **Rotate API keys regularly** - Every 90 days
3. **Monitor rate limits** - Check /metrics endpoint
4. **Review logs regularly** - Check for suspicious activity
5. **Keep dependencies updated** - Run `pip list --outdated`
6. **Use HTTPS in production** - Configure reverse proxy
7. **Backup database regularly** - SQLite file + ChromaDB

## 📞 Support

### Check Logs
```bash
tail -f logs/brs_sasa.log
```

### Run Diagnostics
```bash
# Health check
curl http://localhost:8000/health/ready

# Test query
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "conversation_id": "test"}'
```

### Common Error Codes
- **429**: Rate limit exceeded - Wait 1 minute
- **500**: Server error - Check logs
- **422**: Validation error - Check request format
- **503**: Service unavailable - Check health endpoint

## 🚀 Deployment Checklist

- [ ] Set environment variables
- [ ] Initialize knowledge base
- [ ] Process legislation documents
- [ ] Run all tests
- [ ] Configure rate limiting
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure logging
- [ ] Set up backup strategy
- [ ] Configure reverse proxy (nginx)
- [ ] Enable HTTPS
- [ ] Test health endpoints
- [ ] Load test with stress_test.py
- [ ] Document API for users
- [ ] Train support team

---

**Quick Links**:
- API Docs: http://localhost:8000/docs
- UI Demo: http://localhost:8501
- Metrics: http://localhost:8000/metrics
- Health: http://localhost:8000/health/ready

**Version**: 1.0.0
**Last Updated**: February 10, 2026
