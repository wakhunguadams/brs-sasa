# Public Participation Agent - Feature Documentation

## Overview

The Public Participation Agent is a new specialized agent in the BRS-SASA multi-agent system designed to facilitate public participation in the legislative review process, specifically for the Trust Administration Bill 2025.

## Purpose

Enable citizens to:
1. **Understand Legislation**: Get clear explanations of complex legal documents
2. **Compare Jurisdictions**: See how Kenya's proposed laws compare with other countries
3. **Provide Feedback**: Submit comments, concerns, and suggestions on legislation
4. **Participate Democratically**: Engage in the legislative process

## Architecture

### Agent Components

**Public Participation Agent** (`agents/public_participation_agent.py`)
- Specialized LangGraph agent with tool-calling capability
- Uses RAG for legislation search
- Uses web search for international comparisons
- Collects and stores user feedback

### Tools Available

1. **search_legislation_knowledge** - Search Trust Administration Bill 2025
2. **search_web_duckduckgo** - Compare with other countries' laws
3. **search_brs_news** - Find recent legislative updates
4. **collect_legislation_feedback** - Store user feedback in database

### Database Model

**FeedbackModel** (`core/models.py`)
```python
- id: Unique identifier
- user_query: Original user question
- feedback_text: User's feedback/comment
- legislation_section: Relevant section (optional)
- sentiment: positive/negative/neutral/suggestion
- feedback_metadata: Additional JSON data
- created_at: Timestamp
```

### API Endpoints

**POST /api/v1/feedback/submit** - Submit feedback
**GET /api/v1/feedback/list** - List all feedback (admin)
**GET /api/v1/feedback/stats** - Get feedback statistics

## Routing Logic

The router node classifies queries into three categories:

1. **legislation** → Public Participation Agent
   - Keywords: trust, bill, law, legislation, public participation, feedback, jurisdiction
   
2. **knowledge** → RAG Agent
   - Keywords: register, business, company, fee, cost, process
   
3. **conversation** → Conversation Agent
   - Keywords: hello, hi, who are you, greetings

## Knowledge Base

### Legislation Documents

- **Trust Administration Bill 2025** (139 chunks)
  - Converted from .doc to .txt format
  - Tagged with metadata: `type: "legislation"`
  - Searchable via legislation-specific tool

### Document Processing

```bash
# Convert .doc to .txt
libreoffice --headless --convert-to txt --outdir legislation legislation/Trust-Administration-Bill-2025.doc

# Process and add to knowledge base
python3 process_legislation.py
```

## Usage Examples

### 1. Understanding Legislation

**User**: "What is the Trust Administration Bill 2025 about?"

**Agent**: Searches legislation knowledge base and provides clear explanation

### 2. Jurisdiction Comparison

**User**: "How does Kenya's Trust Administration Bill compare to UK trust laws?"

**Agent**: 
1. Searches legislation knowledge for Kenya's bill
2. Searches web for UK trust laws
3. Provides comparative analysis

### 3. Collecting Feedback

**User**: "I think the Trust Administration Bill should include more protections for beneficiaries"

**Agent**:
1. Recognizes this as feedback
2. Calls `collect_legislation_feedback` tool
3. Stores in database with sentiment: "suggestion"
4. Thanks user for participation

## Testing

### Run Tests

```bash
# Test public participation agent
python3 test_public_participation.py

# Test via API endpoint
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the Trust Administration Bill about?", "conversation_id": "test123"}'
```

### Test Scenarios

1. ✅ Legislation explanation queries
2. ✅ International comparison queries
3. ✅ Feedback collection
4. ✅ Mixed queries (legislation + business registration)
5. ✅ Routing accuracy

## Feedback Management

### View Feedback Statistics

```bash
curl http://localhost:8000/api/v1/feedback/stats
```

Response:
```json
{
  "total_feedback": 25,
  "by_sentiment": {
    "positive": 8,
    "negative": 5,
    "neutral": 7,
    "suggestion": 5
  }
}
```

### List Recent Feedback

```bash
curl http://localhost:8000/api/v1/feedback/list?limit=10
```

### Filter by Sentiment

```bash
curl http://localhost:8000/api/v1/feedback/list?sentiment=suggestion&limit=20
```

## Future Enhancements

### Phase 1 (Current)
- ✅ Basic legislation search
- ✅ Web search for comparisons
- ✅ Feedback collection in database

### Phase 2 (Planned)
- 🔄 CRM integration for feedback management
- 🔄 Email notifications for feedback submissions
- 🔄 Sentiment analysis using LLM
- 🔄 Feedback categorization and tagging

### Phase 3 (Future)
- 📋 Public dashboard for feedback statistics
- 📋 Export feedback reports (PDF, Excel)
- 📋 Multi-language support
- 📋 Integration with government systems

## Configuration

### Environment Variables

```bash
# Required for LLM
GEMINI_API_KEY=your_api_key_here

# Database (SQLite by default)
DATABASE_URL=sqlite:///./brs_sasa.db

# Knowledge Base
CHROMA_PERSIST_DIR=./chroma_data
```

### Adding New Legislation

1. Place document in `legislation/` folder
2. Convert to .txt if needed
3. Update `process_legislation.py` to include new document
4. Run processing script
5. Restart server

## Performance

- **Legislation Search**: ~2-3 seconds
- **Web Comparison**: ~5-7 seconds
- **Feedback Collection**: <1 second
- **Concurrent Requests**: Supports 20-30 req/min per IP

## Security

- Rate limiting: 20-30 requests/min per IP
- Input validation on all endpoints
- SQL injection protection via SQLAlchemy ORM
- No PII stored without consent

## Monitoring

### Metrics Available

- `brs_sasa_requests_total` - Total requests by agent
- `brs_sasa_request_duration_seconds` - Request duration
- `brs_sasa_llm_calls_total` - LLM API calls

### Logs

```bash
# View agent routing
grep "Routing to public participation agent" logs/*.log

# View feedback collection
grep "Feedback collected" logs/*.log
```

## Support

For issues or questions:
- Check logs in `logs/` directory
- Review test results from `test_public_participation.py`
- Contact BRS technical team

## License

Developed for the Business Registration Service (BRS) of Kenya
