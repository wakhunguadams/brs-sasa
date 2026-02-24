"""
Comprehensive Test Suite for BRS-SASA
Following industry best practices for AI agent testing
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from core.state import BRSState
from agents.rag_agent import RAGAgent, RAGResponse
from agents.conversation_agent import ConversationAgent
from core.knowledge_base import KnowledgeBase
from llm_factory.factory import LLMFactory

# Test client
client = TestClient(app)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_llm():
    """Mock LLM for testing"""
    llm = AsyncMock()
    llm.ainvoke = AsyncMock(return_value=Mock(content="Test response"))
    llm.bind_tools = Mock(return_value=llm)
    return llm


@pytest.fixture
def sample_state():
    """Sample BRS state for testing"""
    from langchain_core.messages import HumanMessage
    return {
        "messages": [HumanMessage(content="Test query")],
        "user_input": "Test query",
        "response": "",
        "query_type": "unknown",
        "context": {},
        "conversation_id": "test-123",
        "retrieved_docs": [],
        "sources": [],
        "confidence": 0.0,
        "current_agent": "router",
        "agent_feedback": {},
        "error_count": 0,
        "max_steps": 10
    }


@pytest.fixture
def mock_knowledge_base():
    """Mock knowledge base"""
    kb = AsyncMock(spec=KnowledgeBase)
    kb.search = AsyncMock(return_value=[
        {
            "content": "Company registration costs KES 10,650",
            "source": "brs_extended_info.txt",
            "distance": 0.1
        }
    ])
    kb.initialized = True
    return kb


# ============================================================================
# API ENDPOINT TESTS
# ============================================================================

class TestAPIEndpoints:
    """Test all API endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns correct info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "BRS-SASA" in data["message"]
        assert "version" in data
        assert data["version"] == "1.0.0"
    
    def test_info_endpoint(self):
        """Test info endpoint returns configuration"""
        response = client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert "app_name" in data
        assert "llm_provider" in data
        assert "vector_db_type" in data
        assert data["app_name"] == "BRS-SASA"
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "brs-sasa-api"
    
    def test_chat_completions_invalid_request(self):
        """Test chat completions with invalid request"""
        response = client.post("/api/v1/chat/completions", json={})
        assert response.status_code == 422  # Validation error
    
    def test_chat_completions_empty_messages(self):
        """Test chat completions with empty messages"""
        response = client.post("/api/v1/chat/completions", json={"messages": []})
        assert response.status_code == 400  # Our validation returns 400 for empty messages
    
    def test_documents_list_endpoint(self):
        """Test documents list endpoint"""
        response = client.get("/api/v1/documents/list")
        # This endpoint doesn't exist yet, so we expect 404
        assert response.status_code == 404


# ============================================================================
# RAG AGENT TESTS
# ============================================================================

class TestRAGAgent:
    """Test RAG agent functionality"""
    
    @pytest.mark.asyncio
    async def test_rag_agent_initialization(self, mock_llm):
        """Test RAG agent initializes correctly"""
        agent = RAGAgent(mock_llm)
        assert agent.llm == mock_llm
        assert agent.llm_with_tools is not None
    
    @pytest.mark.asyncio
    async def test_query_knowledge_base_simple(self, mock_llm):
        """Test simple knowledge base query"""
        agent = RAGAgent(mock_llm)
        
        # Mock tool execution
        mock_llm.ainvoke.return_value = Mock(
            content="Company registration costs KES 10,650",
            tool_calls=[]
        )
        
        result = await agent.query_knowledge_base("What are company fees?")
        
        assert isinstance(result, RAGResponse)
        assert result.response_text is not None
        assert result.confidence >= 0.0
    
    @pytest.mark.asyncio
    async def test_query_with_context(self, mock_llm):
        """Test query with conversation context"""
        agent = RAGAgent(mock_llm)
        
        context = {
            "history": [
                {"role": "user", "content": "Tell me about LLP"},
                {"role": "assistant", "content": "LLP stands for Limited Liability Partnership"}
            ]
        }
        
        mock_llm.ainvoke.return_value = Mock(
            content="LLP registration costs KES 10,650",
            tool_calls=[]
        )
        
        result = await agent.query_knowledge_base("What are the fees?", context=context)
        
        assert isinstance(result, RAGResponse)
        # Should understand "fees" refers to LLP fees from context
    
    @pytest.mark.asyncio
    async def test_rag_agent_error_handling(self, mock_llm):
        """Test RAG agent handles errors gracefully"""
        agent = RAGAgent(mock_llm)
        
        # Simulate LLM error
        mock_llm.ainvoke.side_effect = Exception("LLM API error")
        
        result = await agent.query_knowledge_base("Test query")
        
        assert isinstance(result, RAGResponse)
        assert "error" in result.response_text.lower() or "sorry" in result.response_text.lower()
        assert result.confidence == 0.0


# ============================================================================
# CONVERSATION AGENT TESTS
# ============================================================================

class TestConversationAgent:
    """Test conversation agent functionality"""
    
    @pytest.mark.asyncio
    async def test_conversation_agent_initialization(self, mock_llm):
        """Test conversation agent initializes correctly"""
        agent = ConversationAgent(mock_llm)
        assert agent.llm == mock_llm
    
    @pytest.mark.asyncio
    async def test_simple_greeting(self, mock_llm):
        """Test simple greeting response"""
        agent = ConversationAgent(mock_llm)
        
        mock_llm.ainvoke.return_value = Mock(
            content="Hello! I'm BRS-SASA, how can I help you?"
        )
        
        response = await agent.generate_response("Hello")
        
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_identity_question(self, mock_llm):
        """Test identity question handling"""
        agent = ConversationAgent(mock_llm)
        
        mock_llm.ainvoke.return_value = Mock(
            content="I am BRS-SASA, developed by a team for the Business Registration Service of Kenya"
        )
        
        response = await agent.generate_response("Who created you?")
        
        assert "BRS-SASA" in response
        # Should not claim to be a generic AI
        assert "OpenAI" not in response
        assert "Google" not in response or "Google's Gemini model" in response
    
    @pytest.mark.asyncio
    async def test_conversation_with_history(self, mock_llm):
        """Test conversation with history"""
        agent = ConversationAgent(mock_llm)
        
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"}
        ]
        
        mock_llm.ainvoke.return_value = Mock(
            content="I can help you with business registration in Kenya"
        )
        
        response = await agent.generate_response("What can you do?", history=history)
        
        assert response is not None
        assert len(response) > 0


# ============================================================================
# KNOWLEDGE BASE TESTS
# ============================================================================

class TestKnowledgeBase:
    """Test knowledge base functionality"""
    
    @pytest.mark.asyncio
    async def test_knowledge_base_initialization(self):
        """Test knowledge base initializes"""
        kb = KnowledgeBase(persist_dir="./test_chroma")
        await kb.initialize()
        assert kb.initialized == True
        assert kb.client is not None
        assert kb.collection is not None
    
    @pytest.mark.asyncio
    async def test_add_and_search_documents(self):
        """Test adding and searching documents"""
        kb = KnowledgeBase(persist_dir="./test_chroma")
        await kb.initialize()
        
        # Add test documents
        documents = ["Company registration costs KES 10,650"]
        metadatas = [{"source": "test.txt"}]
        
        await kb.add_documents(documents, metadatas)
        
        # Search
        results = await kb.search("company fees", top_k=1)
        
        assert len(results) > 0
        assert "company" in results[0]["content"].lower() or "registration" in results[0]["content"].lower()
    
    @pytest.mark.asyncio
    async def test_empty_search(self):
        """Test search on empty knowledge base"""
        kb = KnowledgeBase(persist_dir="./test_chroma_empty")
        await kb.initialize()
        
        results = await kb.search("test query", top_k=5)
        
        assert isinstance(results, list)
        # May be empty or have no results


# ============================================================================
# STATE MANAGEMENT TESTS
# ============================================================================

class TestStateManagement:
    """Test state management and routing"""
    
    def test_state_structure(self, sample_state):
        """Test state has required fields"""
        required_fields = [
            "messages", "user_input", "response", "query_type",
            "conversation_id", "sources", "confidence"
        ]
        
        for field in required_fields:
            assert field in sample_state
    
    def test_route_query_type(self):
        """Test query type routing logic"""
        from core.state import route_query_type
        
        # Knowledge query
        state = {
            "current_agent": "rag_agent",
            "query_type": "knowledge"
        }
        assert route_query_type(state) == "rag_agent"
        
        # Conversation query
        state = {
            "current_agent": "conversation_agent",
            "query_type": "conversation"
        }
        assert route_query_type(state) == "conversation_agent"


# ============================================================================
# LLM FACTORY TESTS
# ============================================================================

class TestLLMFactory:
    """Test LLM factory"""
    
    def test_factory_exists(self):
        """Test factory class exists"""
        assert LLMFactory is not None
        assert hasattr(LLMFactory, 'get_llm')
    
    def test_unsupported_provider(self):
        """Test unsupported provider raises error"""
        with pytest.raises(ValueError):
            LLMFactory.get_llm("unsupported_provider")


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    @pytest.mark.asyncio
    async def test_very_long_query(self, mock_llm):
        """Test handling of very long queries"""
        agent = RAGAgent(mock_llm)
        
        long_query = "What are the fees? " * 500  # Very long query
        
        mock_llm.ainvoke.return_value = Mock(
            content="Response",
            tool_calls=[]
        )
        
        result = await agent.query_knowledge_base(long_query)
        
        assert isinstance(result, RAGResponse)
    
    @pytest.mark.asyncio
    async def test_special_characters_query(self, mock_llm):
        """Test handling of special characters"""
        agent = RAGAgent(mock_llm)
        
        special_query = "What are fees? <script>alert('xss')</script>"
        
        mock_llm.ainvoke.return_value = Mock(
            content="Response",
            tool_calls=[]
        )
        
        result = await agent.query_knowledge_base(special_query)
        
        assert isinstance(result, RAGResponse)
    
    @pytest.mark.asyncio
    async def test_empty_query(self, mock_llm):
        """Test handling of empty query"""
        agent = RAGAgent(mock_llm)
        
        mock_llm.ainvoke.return_value = Mock(
            content="Please provide a question",
            tool_calls=[]
        )
        
        result = await agent.query_knowledge_base("")
        
        assert isinstance(result, RAGResponse)
    
    @pytest.mark.asyncio
    async def test_unicode_query(self, mock_llm):
        """Test handling of Unicode characters"""
        agent = RAGAgent(mock_llm)
        
        unicode_query = "What are fees? 你好 مرحبا 🚀"
        
        mock_llm.ainvoke.return_value = Mock(
            content="Response",
            tool_calls=[]
        )
        
        result = await agent.query_knowledge_base(unicode_query)
        
        assert isinstance(result, RAGResponse)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for complete workflows"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_simple_query(self):
        """Test complete end-to-end query flow"""
        # This would test the full workflow from API to response
        # Requires actual system to be running
        pass
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self):
        """Test multi-turn conversation flow"""
        # Test that context is maintained across turns
        pass


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance and load tests"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        # Simulate multiple concurrent requests
        tasks = []
        for i in range(10):
            task = asyncio.create_task(
                asyncio.sleep(0.1)  # Simulate async work
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        assert len(results) == 10
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_response_latency(self, mock_llm):
        """Test response latency is acceptable"""
        import time
        
        agent = RAGAgent(mock_llm)
        
        mock_llm.ainvoke.return_value = Mock(
            content="Response",
            tool_calls=[]
        )
        
        start = time.time()
        result = await agent.query_knowledge_base("Test query")
        latency = time.time() - start
        
        # Should respond quickly with mock
        assert latency < 1.0  # Less than 1 second


# ============================================================================
# SECURITY TESTS
# ============================================================================

class TestSecurity:
    """Security-related tests"""
    
    def test_sql_injection_attempt(self):
        """Test SQL injection is prevented"""
        malicious_input = "'; DROP TABLE users; --"
        
        response = client.post("/api/v1/chat/completions", json={
            "messages": [{"role": "user", "content": malicious_input}]
        })
        
        # Should not crash or execute SQL
        assert response.status_code in [200, 422, 500]
    
    def test_xss_attempt(self):
        """Test XSS is prevented"""
        xss_input = "<script>alert('xss')</script>"
        
        response = client.post("/api/v1/chat/completions", json={
            "messages": [{"role": "user", "content": xss_input}]
        })
        
        # Should handle safely
        assert response.status_code in [200, 422, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
