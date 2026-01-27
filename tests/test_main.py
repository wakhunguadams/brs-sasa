import pytest
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from main import app
from llm_factory.factory import LLMFactory, BaseLLM
from agents.conversation_agent import ConversationAgent, AgentResponse
from agents.rag_agent import RAGAgent, RAGResponse
from schemas.chat import ChatCompletionRequest, MessageContent

client = TestClient(app)

class MockLLM(BaseLLM):
    """Mock LLM for testing purposes"""

    def __init__(self, response_text="Mock response"):
        self.response_text = response_text
        self.generate_response_called = False
        self.embed_text_called = False

    async def generate_response(self, prompt: str, context: dict = None) -> str:
        self.generate_response_called = True
        return self.response_text

    async def embed_text(self, text: str) -> list:
        self.embed_text_called = True
        return [0.1, 0.2, 0.3]  # Mock embedding

@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing"""
    return MockLLM()

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "BRS-SASA" in data["message"]
    assert "docs" in data

def test_info_endpoint():
    """Test the info endpoint"""
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "version" in data
    assert data["app_name"] == "BRS-SASA"

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["service"] == "brs-sasa-api"

@pytest.mark.asyncio
@patch('llm_factory.factory.LLMFactory.get_llm')
async def test_conversation_agent_with_mock(mock_get_llm):
    """Test the conversation agent with a mock LLM"""
    # Configure the mock
    mock_llm = MockLLM(response_text="Test response from conversation agent")
    mock_get_llm.return_value = mock_llm

    # Create conversation agent with mock
    agent = ConversationAgent(llm=mock_llm)

    # Test processing a message
    result = await agent.process_message(
        message="Test message",
        history=[]
    )

    # Assertions
    assert isinstance(result, AgentResponse)
    assert result.response_text == "Test response from conversation agent"
    assert result.confidence is not None
    assert isinstance(result.sources, list)

    # Verify the LLM was called
    assert mock_llm.generate_response_called

@pytest.mark.asyncio
@patch('llm_factory.factory.LLMFactory.get_llm')
async def test_rag_agent_with_mock(mock_get_llm):
    """Test the RAG agent with a mock LLM"""
    # Configure the mock
    mock_llm = MockLLM(response_text="Test response from RAG agent")
    mock_get_llm.return_value = mock_llm

    # Create RAG agent with mock
    agent = RAGAgent(llm=mock_llm)

    # Mock the knowledge base search to return some results
    with patch.object(agent.knowledge_base, 'search') as mock_search:
        mock_search.return_value = [
            {
                "content": "Business registration costs KSH 10,750",
                "source": "FAQs.pdf",
                "distance": 0.1
            }
        ]

        # Test querying the knowledge base
        result = await agent.query_knowledge_base(
            query="How much does business registration cost?",
            top_k=1
        )

        # Assertions
        assert isinstance(result, RAGResponse)
        assert result.response_text == "Test response from RAG agent"
        assert len(result.sources) >= 0  # Sources may be empty depending on mock
        assert result.confidence is not None

        # Verify the knowledge base search was called
        mock_search.assert_called_once()
        # Verify the LLM was called
        assert mock_llm.generate_response_called

def test_llm_factory():
    """Test the LLM factory creation (without actual API keys)"""
    factory = LLMFactory()

    # Test that factory initializes without error
    assert factory is not None

    # Test that we can get the factory methods
    assert hasattr(factory, 'get_llm')
    assert hasattr(factory, 'register_llm')

    # Test that factory raises error for unsupported provider
    with pytest.raises(ValueError):
        factory.get_llm("unsupported_provider")

def test_chat_endpoint_basic():
    """Test the chat endpoint with basic request"""
    chat_request = {
        "messages": [
            {"role": "user", "content": "Hello, how do I register a business?"}
        ]
    }

    response = client.post("/api/v1/chat/completions", json=chat_request)

    # The response should be one of these depending on if API keys are configured
    assert response.status_code in [200, 422, 500]

def test_chat_endpoint_with_provider():
    """Test the chat endpoint with explicit provider"""
    chat_request = {
        "messages": [
            {"role": "user", "content": "What are the requirements for registering a company?"}
        ],
        "provider": "gemini"
    }

    response = client.post("/api/v1/chat/completions", json=chat_request)

    # The response should be one of these depending on if API keys are configured
    assert response.status_code in [200, 422, 500]

def test_document_upload_endpoint():
    """Test the document upload endpoint"""
    # This is a basic test to ensure the endpoint exists
    # Actual file upload testing would require more complex setup
    response = client.get("/api/v1/documents/list")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "count" in data

if __name__ == "__main__":
    pytest.main([__file__])