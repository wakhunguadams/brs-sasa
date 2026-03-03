# BRS-SASA: Technical Questions - Quick Answers

## Q1: What type of AI approach is central to your current build?

**Answer**: **GenAI/LLM** (Generative AI with Large Language Models)

**Details**:
- Primary: Google Gemini 2.0 Flash for natural language processing
- Secondary: Computer Vision (screenshot analysis with OCR)
- Architecture: Multi-agent system with 5 specialized AI agents
- Framework: LangGraph for agent orchestration

---

## Q2: What task is the AI currently performing in your solution?

**Answer**: Multiple AI tasks across different agents:

### Primary Tasks:
1. **Classification** - Routing queries to appropriate agents
2. **Question Answering** - Conversational responses about business registration
3. **Information Retrieval** - Semantic search through BRS documentation
4. **Summarization** - Condensing legislation and policy documents
5. **Sentiment Analysis** - Analyzing user feedback on legislation

### Secondary Tasks:
6. **Image Analysis** - Screenshot OCR and error detection
7. **Data Extraction** - Parsing registration numbers and status
8. **Recommendation** - Suggesting next steps in processes
9. **Comparison** - Jurisdiction analysis (Kenya vs other countries)
10. **Conversation Management** - Multi-turn context-aware dialogue

---

## Q3: What is one known limitation/failure case in the current AI system?

**Answer**: **Hallucination Risk** - LLM may generate plausible but incorrect information

**Details**:
- **Occurrence Rate**: 5-10% of responses may contain minor inaccuracies
- **Impact**: Users might receive slightly incorrect procedural information
- **Mitigation**: 
  - RAG (Retrieval Augmented Generation) grounds responses in actual BRS documentation
  - Confidence scores displayed to users
  - Critical information includes source citations
  - Fallback to "contact BRS directly" for uncertain queries

**Other Known Limitations**:
- Screenshot OCR fails on low-quality images (~15-20% failure rate)
- API dependency (BRS Pesaflow API unavailability affects status checks)
- Context window limits (conversations >50 messages may lose early context)
- English-only (Swahili support not yet implemented)

---

## Q4: What are the main tools/platforms your team is currently using?

**Selected Tools** (from your list):

✅ **Python** - 100% of backend code  
✅ **LLM/API platforms** - Google Gemini, OpenAI, Anthropic  
✅ **ML frameworks** - LangChain, LangGraph, ChromaDB  
✅ **Data tools** - SQL (SQLite), Python notebooks  
✅ **Database tools** - SQLAlchemy ORM, SQLite/PostgreSQL  
✅ **DevOps/deployment tools** - Docker, Docker Compose, Git  

❌ **Not Using**:
- JavaScript/TypeScript
- No-code/low-code platforms
- Cloud platforms (currently local deployment)
- Mobile app frameworks
- GIS/geospatial tools

---

## Q5: Which 2-3 tools are most critical to your current build?

### 1. **LangGraph** (Most Critical)
**What it does**: Multi-agent AI orchestration and workflow management

**Why critical**:
- Coordinates 5 specialized AI agents (Router, RAG, Conversation, Public Participation, Application Assistant)
- Manages conversation state and routing logic
- Enables dynamic tool-calling and decision-making
- Provides conversation persistence with checkpointing

**Without it**: Would need 3-4x more custom code to manage agent coordination

---

### 2. **Google Gemini 2.0 Flash** (Core Intelligence)
**What it does**: Primary Large Language Model for all AI capabilities

**Why critical**:
- Powers natural language understanding across all 5 agents
- Handles query classification, response generation, tool selection
- Provides vision capabilities for screenshot analysis
- Fast (<2s response time) and cost-effective ($0.001-0.002 per request)

**Without it**: No AI assistant - the entire system depends on LLM intelligence

---

### 3. **ChromaDB** (Knowledge Base)
**What it does**: Vector database for semantic search and RAG (Retrieval Augmented Generation)

**Why critical**:
- Stores embeddings of ~500 BRS documents (policies, legislation, FAQs)
- Enables semantic search (finds relevant info even with different wording)
- Grounds AI responses in actual documentation (reduces hallucination)
- Powers the RAG agent with accurate, source-cited information

**Without it**: System would rely purely on LLM's training data (higher hallucination risk, no source citations)

---

## Technology Stack Summary

```
User Layer:     Streamlit (UI) + FastAPI (API)
                        ↓
AI Layer:       LangGraph + LangChain
                (5 specialized agents)
                        ↓
Intelligence:   Google Gemini 2.0 + ChromaDB
                (LLM + Vector Store)
                        ↓
Data Layer:     SQLite + SQLAlchemy
                (Conversations, Feedback, Issues)
```

---

## Quick Stats

- **Language**: 100% Python
- **Lines of Code**: ~15,000
- **AI Agents**: 5 specialized agents
- **LangChain Tools**: 12 custom tools
- **API Endpoints**: 15+ REST endpoints
- **Response Time**: 1-3 seconds average
- **Accuracy**: 85-90% (based on testing)
- **Cost**: $0.001-0.002 per query

---

**Prepared For**: Paul Kariuki, Director ICT, BRS  
**Date**: March 2026  
**Document**: Technical Overview for AI Implementation
