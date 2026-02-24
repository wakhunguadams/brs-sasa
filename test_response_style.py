"""
Test response style - should be direct, not overly polite
"""
import asyncio
from core.workflow import brs_workflow
from core.logger import setup_logger

logger = setup_logger(__name__)

async def test_response_style():
    """Test that responses are direct and conversational"""
    
    queries = [
        "What is the Trust Administration Bill about?",
        "How does Kenya's Trust Administration Bill compare to Uganda's trust laws?",
        "Compare trust laws in Kenya and Tanzania"
    ]
    
    print("=" * 80)
    print("RESPONSE STYLE TEST")
    print("=" * 80)
    print("\nChecking for:")
    print("  ❌ Should NOT start with 'Thank you for your question'")
    print("  ❌ Should NOT be overly formal")
    print("  ✅ Should be direct and conversational")
    print("  ✅ Should get straight to the answer")
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
                "conversation_id": f"test_style_{i}",
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
            
            response = result.get('response', '')
            first_sentence = response.split('.')[0] if response else ''
            
            print(f"Agent: {result.get('current_agent', 'unknown')}")
            print(f"\nFirst sentence: {first_sentence}...")
            print(f"\nFull response (first 300 chars):\n{response[:300]}...")
            
            # Check for overly polite phrases
            polite_phrases = [
                'thank you for your question',
                'thank you for asking',
                'i appreciate your question',
                'thanks for your question'
            ]
            
            is_polite = any(phrase in response.lower() for phrase in polite_phrases)
            
            if is_polite:
                print("\n❌ ISSUE: Response is overly polite/formal")
            else:
                print("\n✅ GOOD: Response is direct and conversational")
            
            print(f"\nConfidence: {result.get('confidence', 0.0):.0%}")
            
        except Exception as e:
            logger.error(f"Error in test {i}: {str(e)}")
            print(f"ERROR: {str(e)}")
        
        if i < len(queries):
            print("\n" + "="*80)
            print("Press Enter to continue...")
            input()
    
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(test_response_style())
