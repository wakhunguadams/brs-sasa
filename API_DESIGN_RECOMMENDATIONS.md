# API Design Analysis & Recommendations

## Executive Summary

After researching industry best practices from OpenAI, LangGraph documentation, and production conversational AI systems, here are the key improvements recommended for BRS-SASA's API design.

---

## Current vs Recommended API Design

### 1. Endpoint Structure

| Aspect | Current | Recommended | Why |
|--------|---------|-------------|-----|
| Chat endpoint | `POST /api/v1/chat/` | `POST /api/v1/completions` | Follows OpenAI naming convention |
| Conversations | None | `GET/POST /api/v1/conversations` | Resource-based REST design |
| Message history | In request body | Stored server-side | Better conversation persistence |

**Current:**
```
POST /api/v1/chat/
```

**Recommended:**
```
POST /api/v1/completions          # Main chat endpoint
GET  /api/v1/conversations        # List conversations
POST /api/v1/conversations        # Create conversation
GET  /api/v1/conversations/{id}   # Get conversation
PATCH /api/v1/conversations/{id}  # Update status
```

---

### 2. Request Payload

**Current:**
```json
{
  "message": "How do I register a company?",
  "history": [
    {"role": "user", "content": "Hello"}
  ],
  "provider": "gemini"
}
```

**Recommended (OpenAI-compatible):**
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful BRS assistant."},
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hello! How can I help?"},
    {"role": "user", "content": "How do I register a company?"}
  ],
  "conversation_id": "conv-abc123",
  "model": "gemini-2.0-flash",
  "provider": "gemini",
  "stream": false,
  "temperature": 0.7,
  "use_knowledge_base": true
}
```

**Benefits:**
- Compatible with OpenAI client libraries
- Supports system messages for custom prompts
- Conversation persistence via ID
- Streaming toggle
- Model configuration options

---

### 3. Response Payload

**Current:**
```json
{
  "response": "To register a company...",
  "sources": ["doc1.pdf"],
  "confidence": 0.85
}
```

**Recommended (OpenAI-compatible):**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1706000000,
  "model": "gemini-2.0-flash",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "To register a company..."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 50,
    "completion_tokens": 200,
    "total_tokens": 250
  },
  "conversation_id": "conv-abc123",
  "sources": ["CompaniesAct17of2015.pdf"],
  "confidence": 0.85
}
```

**Benefits:**
- Unique response ID for tracking
- Token usage statistics
- Standard `choices` array (extensible)
- Finish reason for debugging
- BRS extensions (`sources`, `confidence`) preserved

---

### 4. Streaming (SSE vs WebSocket)

**Current:** WebSocket only

**Recommended:** Server-Sent Events (SSE) + WebSocket

**SSE Streaming Response:**
```
POST /api/v1/completions
Content-Type: application/json

{"messages": [...], "stream": true}
```

**Response (text/event-stream):**
```
data: {"id":"chatcmpl-123","choices":[{"delta":{"content":"To "}}]}

data: {"id":"chatcmpl-123","choices":[{"delta":{"content":"register "}}]}

data: {"id":"chatcmpl-123","choices":[{"delta":{"content":"a company..."}}]}

data: {"id":"chatcmpl-123","choices":[{"delta":{},"finish_reason":"stop"}],"sources":["doc.pdf"],"confidence":0.85}

data: [DONE]
```

**Why SSE over WebSocket for streaming:**
- Simpler to implement and debug
- Works through HTTP proxies
- Auto-reconnection built into EventSource
- Better for unidirectional streams (LLM output)
- WebSocket still available for bidirectional needs

---

### 5. Error Handling

**Current:**
```json
{
  "detail": "Error processing chat request: ..."
}
```

**Recommended:**
```json
{
  "error": {
    "code": "invalid_request",
    "message": "The conversation_id provided does not exist",
    "type": "invalid_request_error",
    "param": "conversation_id"
  },
  "request_id": "req-abc123def456"
}
```

**Benefits:**
- Structured error codes for programmatic handling
- Request ID for debugging and support
- Parameter identification
- Consistent format across all errors

---

### 6. Headers

**Recommended Headers:**

| Header | Purpose |
|--------|---------|
| `X-Request-ID` | Trace requests through logs |
| `Idempotency-Key` | Prevent duplicate processing |
| `Authorization` | Bearer token auth (future) |

---

### 7. Conversation Management

**New Endpoints:**

```python
# Create a conversation with custom system prompt
POST /api/v1/conversations
{
  "title": "Company Registration Help",
  "system_message": "You are an expert on Kenyan business registration."
}

# Response
{
  "id": "conv-abc123",
  "title": "Company Registration Help",
  "status": "active",
  "messages": [{
    "role": "system",
    "content": "You are an expert..."
  }],
  "created_at": "2026-01-23T12:00:00Z"
}
```

**Status Management:**
```python
# Archive a conversation
PATCH /api/v1/conversations/conv-abc123
{
  "status": "archived"
}
```

---

## Implementation Files

Two new files have been created:

1. **`schemas/chat_v2.py`** - New Pydantic models
   - `ChatCompletionRequest` - OpenAI-compatible request
   - `ChatCompletionResponse` - OpenAI-compatible response
   - `Conversation` - Conversation management
   - `ChatCompletionChunk` - Streaming chunks
   - `APIError` - Standardized errors
   - Legacy compatibility wrappers

2. **`api/v1/endpoints/chat_v2.py`** - New endpoints
   - `POST /completions` - Main chat endpoint
   - `GET/POST/PATCH /conversations` - Conversation CRUD
   - SSE streaming support
   - WebSocket with structured messages
   - Legacy `/` endpoint preserved

---

## Migration Path

### Phase 1: Add New Endpoints (Non-breaking)
1. Register new router alongside existing
2. Both old and new endpoints work
3. Document new API for integrators

### Phase 2: Deprecation Notice
1. Add deprecation headers to old endpoints
2. Log usage of old endpoints
3. Communicate timeline to users

### Phase 3: Migration
1. Update UI to use new endpoints
2. Update any external integrations
3. Monitor old endpoint usage

### Phase 4: Removal
1. Remove old endpoints after grace period
2. Or keep as permanent legacy support

---

## Quick Integration Guide

### Using New API with Python
```python
import httpx

response = httpx.post(
    "http://localhost:8000/api/v1/completions",
    json={
        "messages": [
            {"role": "user", "content": "How do I register a company?"}
        ],
        "stream": False
    }
)

data = response.json()
print(data["choices"][0]["message"]["content"])
print(f"Sources: {data['sources']}")
print(f"Confidence: {data['confidence']}")
```

### Using Streaming with JavaScript
```javascript
const eventSource = new EventSource('/api/v1/completions', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        messages: [{role: 'user', content: 'Hello'}],
        stream: true
    })
});

eventSource.onmessage = (event) => {
    if (event.data === '[DONE]') {
        eventSource.close();
        return;
    }
    const chunk = JSON.parse(event.data);
    const content = chunk.choices[0]?.delta?.content || '';
    document.getElementById('output').textContent += content;
};
```

---

## Summary of Changes

| Change | Impact | Priority |
|--------|--------|----------|
| OpenAI-compatible payloads | High (industry standard) | High |
| Conversation persistence | High (better UX) | High |
| SSE streaming | Medium (real-time feel) | Medium |
| Request IDs | Medium (debugging) | Medium |
| Error standardization | Medium (DX) | Medium |
| Idempotency | Low (edge cases) | Low |

The new design maintains backward compatibility while providing a modern, industry-standard API that will be familiar to developers who have worked with OpenAI, Anthropic, or similar APIs.
