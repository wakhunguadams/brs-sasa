"""
Test the Public Participation Agent
"""
import asyncio
from core.workflow import brs_workflow
from core.logger import setup_logger

logger = setup_logger(__name__)

async def test_public_participation():
    """Test public participation agent with various queries"""
    
    test_queries = [
        # Legislation queries
        "What is the Trust Administration Bill 2025 about?",
        "Can you explain the key provisions of the Trust Administration Bill?",
        "How does Kenya's Trust Administration Bill compare to UK trust laws?",
        
        # Feedback scenarios
        "I think the Trust Administration Bill should include more protections for beneficiaries",
        "I'm concerned about the compliance requirements in section 5",
        
        # Mixed queries
        "What are the requirements for trust registration and how much will it cost?"
    ]
    
    print("=" * 80)
    print("PUBLIC PARTICIPATION AGENT TEST")
    print("=" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}: {query}")
        print(f"{'='*80}\n")
        
        try:
            # Initialize workflow
            await brs_workflow.initialize()
            
            # Create input
            inputs = {
                "user_input": query,
                "messages": [],
                "conversation_id": f"test_pp_{i}",
                "query_type": "",
                "response": "",
                "context": {},
                "retrieved_docs": [],
                "sources": [],
                "confidence": 0.0,
                "current_agent": "",
                "agent_feedback": {},
                "error_count": 0,
                "max_steps": 10
            }
            
            # Invoke workflow
            result = await brs_workflow.invoke(inputs)
            
            # Display results
            print(f"Agent: {result.get('current_agent', 'unknown')}")
            print(f"Response:\n{result.get('response', 'No response')}")
            
            if result.get('sources'):
                print(f"\nSources: {', '.join(result['sources'])}")
            
            print(f"\nConfidence: {result.get('confidence', 0.0):.0%}")
            
        except Exception as e:
            logger.error(f"Error in test {i}: {str(e)}")
            print(f"ERROR: {str(e)}")
    
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(test_public_participation())
