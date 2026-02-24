"""
Test jurisdiction comparison capability
"""
import asyncio
from core.workflow import brs_workflow
from core.logger import setup_logger

logger = setup_logger(__name__)

async def test_jurisdiction_comparison():
    """Test comparing Kenya's laws with other countries"""
    
    queries = [
        # Neighboring East African countries
        "How does Kenya's Trust Administration Bill compare to Uganda's trust laws?",
        "Compare Kenya's Trust Administration Bill with Tanzania's trust legislation",
        "What are the differences between Kenya and Rwanda trust laws?",
        
        # Other African countries
        "How does Kenya's Trust Administration Bill compare to South Africa trust legislation?",
        
        # International comparisons
        "Compare Kenya's Trust Administration Bill with UK trust laws",
        "How does Kenya's trust legislation compare to India's trust laws?"
    ]
    
    print("=" * 80)
    print("JURISDICTION COMPARISON TEST - NEIGHBORING & INTERNATIONAL")
    print("=" * 80)
    print("\nTesting comparisons with:")
    print("  - East African neighbors: Uganda, Tanzania, Rwanda")
    print("  - Other African countries: South Africa")
    print("  - International: UK, India")
    print("=" * 80)
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/{len(queries)}: {query}")
        print(f"{'='*80}\n")
        
        try:
            await brs_workflow.initialize()
            
            inputs = {
                "user_input": query,
                "messages": [],
                "conversation_id": f"test_jurisdiction_{i}",
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
            
            result = await brs_workflow.invoke(inputs)
            
            print(f"Agent: {result.get('current_agent', 'unknown')}")
            print(f"\nResponse:\n{result.get('response', 'No response')[:500]}...")  # First 500 chars
            
            if result.get('sources'):
                print(f"\nSources: {', '.join(result['sources'])}")
            
            print(f"\nConfidence: {result.get('confidence', 0.0):.0%}")
            print(f"Response Length: {len(result.get('response', ''))} characters")
            
        except Exception as e:
            logger.error(f"Error in test {i}: {str(e)}")
            print(f"ERROR: {str(e)}")
        
        if i < len(queries):
            print("\n" + "="*80)
            print("Press Enter to continue to next test...")
            input()
    
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(test_jurisdiction_comparison())
