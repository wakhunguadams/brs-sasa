# BRS-SASA Demo Guide

## Quick Reference

### Starting the System
```bash
cd /home/eagle/FR/brs-sasa/brs_sasa
source venv/bin/activate
python initialize_kb.py  # First time only
python start_server.py

# Access points:
# - API: http://localhost:8000
# - UI: http://localhost:8501
# - Docs: http://localhost:8000/docs
```

---

## Opening Statement (30 seconds)

> "BRS-SASA is an AI-powered assistant that answers questions about business registration in Kenya. It uses Retrieval-Augmented Generation to provide accurate, cited answers from official BRS documents."

---

## Architecture Overview

```
User Query → Router (classifies intent)
           → RAG Agent (searches knowledge base)
           → LLM (generates response with citations)
           → Response with sources

Graph Flow:
router → rag_agent/conversation_agent → response_formatter → END
           ↘ error_handler ↗
```

**Key Point:** "The router prevents unnecessary knowledge base searches for simple greetings, reducing latency and cost."

---

## Demo Queries (In Order)

| # | Query | What It Demonstrates |
|---|-------|---------------------|
| 1 | "Hello" | Router sends to conversation agent (no RAG needed) |
| 2 | "What are the LLP registration fees?" | RAG retrieval + specific fee citation |
| 3 | "How do I register a company?" | Multi-step process explanation |
| 4 | "What are the BRS contact details?" | Factual retrieval with confidence |
| 5 | Follow-up: "What about foreign companies?" | Conversation memory + context awareness |

### Expected Responses

**Query: "What are the LLP registration fees?"**
- Name Reservation: KES 150
- LLP Registration: KES 10,650
- LLP Agreement filing: KES 2,000
- Source: brs_extended_info.txt

**Query: "What are the BRS contact details?"**
- Address: 17th Floor, UpperHill Chambers, Upper Hill Road, Nairobi
- Phone: +254 11 112 7000
- Email: eo@brs.go.ke
- Website: https://brs.go.ke

---

## Technical Feature Highlights

### 1. Streaming Demo (Terminal)
```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"What are company registration fees?"}],"stream":true}'
```

### 2. Conversation Persistence
```bash
# Create conversation
curl -X POST http://localhost:8000/api/v1/chat/conversations \
  -H "Content-Type: application/json" \
  -d '{"title":"Demo Session"}'

# Use conversation_id in subsequent requests
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"..."}],"conversation_id":"<id>"}'
```

### 3. API Documentation
Navigate to `http://localhost:8000/docs` for interactive Swagger UI.

---

## Explaining Technical Decisions

| Decision | Why |
|----------|-----|
| **LangGraph over LangChain LCEL** | LangGraph provides state persistence, conditional routing, and error recovery. LCEL is for simple linear chains. |
| **OpenAI-compatible API** | Industry standard. Any tool that works with ChatGPT can integrate with BRS-SASA. |
| **Tool-calling RAG** | The LLM decides when to search. More intelligent than always searching. |
| **SSE Streaming** | Users see responses as they generate. Better UX, matches ChatGPT experience. |
| **Confidence scores** | Transparency. Users know when to trust the answer vs. contact BRS directly. |
| **Source citations** | Accountability. Every answer is traceable to official documents. |

---

## API Design Rationale

### Request Format (OpenAI-Compatible)
```json
{
  "messages": [{"role": "user", "content": "..."}],
  "conversation_id": "optional-uuid",
  "model": "gemini-2.0-flash",
  "stream": false
}
```

### Response Format (Extended)
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "choices": [{"message": {"role": "assistant", "content": "..."}}],
  "conversation_id": "uuid",
  "sources": ["file.pdf"],
  "confidence": 0.85
}
```

### BRS-Specific Extensions
| Field | Purpose |
|-------|---------|
| `conversation_id` | Enables multi-turn conversations with server-side persistence |
| `sources` | RAG citations for transparency and accountability |
| `confidence` | Answer reliability indicator (0.0-1.0) |

---

## Industry Standards Compliance

| Pattern | Implementation | Standard |
|---------|---------------|----------|
| API Design | OpenAI-compatible `/completions` | ChatGPT, Claude, Gemini APIs |
| Streaming | Server-Sent Events (SSE) | OpenAI, Anthropic streaming |
| State Management | LangGraph TypedDict + reducers | LangGraph 2024-2026 best practice |
| LLM Abstraction | Factory pattern with LangChain | Provider-agnostic design |
| Tool Calling | `.bind_tools()` with ToolNode | Modern ReAct pattern |

---

## Phase 2 Discussion Points

Mention these as "future enhancements":

1. **Rate Limiting** - Production requirement for API protection
2. **Authentication** - API key management for secure access
3. **Caching** - RAG result caching for common queries
4. **Analytics** - Query pattern tracking for knowledge base improvement
5. **Multi-language** - English/Swahili support
6. **Legislative Agent** - Specialized agent for legal document analysis

---

## Troubleshooting

### Server Won't Start
```bash
# Check if port is in use
lsof -i :8000
pkill -f "uvicorn main:app"
```

### Knowledge Base Empty
```bash
rm -rf chroma_db
python initialize_kb.py
```

### API Returns Errors
```bash
# Check logs
tail -f /tmp/api_server.log

# Verify environment
cat .env | grep API_KEY
```
