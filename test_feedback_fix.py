"""
Test feedback collection fixes
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.langgraph_nodes import router_node, public_participation_agent_node
from core.state import BRSState

async def test_feedback_scenarios():
    """Test various feedback collection scenarios"""
    
    print("="*60)
    print("Testing Feedback Collection Fixes")
    print("="*60)
    
    # Test 1: Direct opinion
    print("\n1. Testing direct opinion: 'I suggest they should reduce the fee'")
    state1 = BRSState(
        user_input="I suggest they should reduce the fee",
        messages=[],
        query_type="",
        current_agent="",
        response="",
        sources=[],
        confidence=0.0,
        conversation_id=None,
        agent_tracking=[],
        error_count=0
    )
    
    # Route the query
    router_result = await router_node(state1)
    print(f"   Router classification: {router_result.get('query_type')}")
    print(f"   Routed to: {router_result.get('current_agent')}")
    
    if router_result.get('query_type') == 'legislation':
        print("   ✅ Correctly routed to legislation/public participation")
    else:
        print(f"   ❌ FAILED: Should route to legislation, got {router_result.get('query_type')}")
    
    # Test 2: "record the feedback" after opinion
    print("\n2. Testing 'record the feedback' with history")
    state2 = BRSState(
        user_input="record the feedback",
        messages=[],
        query_type="",
        current_agent="",
        response="",
        sources=[],
        confidence=0.0,
        conversation_id=None,
        agent_tracking=[],
        error_count=0,
        history=[
            {"role": "user", "content": "tell me about trust administration bill"},
            {"role": "assistant", "content": "The Trust Administration Bill..."},
            {"role": "user", "content": "i suggest they should reduce the fee"},
            {"role": "assistant", "content": "I understand your suggestion..."}
        ]
    )
    
    router_result2 = await router_node(state2)
    print(f"   Router classification: {router_result2.get('query_type')}")
    print(f"   Routed to: {router_result2.get('current_agent')}")
    
    if router_result2.get('query_type') == 'legislation':
        print("   ✅ Correctly routed to legislation/public participation")
    else:
        print(f"   ❌ FAILED: Should route to legislation, got {router_result2.get('query_type')}")
    
    # Test 3: Various feedback keywords
    feedback_phrases = [
        "save my feedback",
        "submit this feedback",
        "log my opinion",
        "collect my feedback",
        "I support this bill",
        "I'm concerned about the penalties",
        "I think they should change this"
    ]
    
    print("\n3. Testing various feedback keywords:")
    for phrase in feedback_phrases:
        state = BRSState(
            user_input=phrase,
            messages=[],
            query_type="",
            current_agent="",
            response="",
            sources=[],
            confidence=0.0,
            conversation_id=None,
            agent_tracking=[],
            error_count=0
        )
        
        result = await router_node(state)
        routed_to = result.get('query_type')
        
        if routed_to == 'legislation':
            print(f"   ✅ '{phrase}' → legislation")
        else:
            print(f"   ❌ '{phrase}' → {routed_to} (should be legislation)")
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print("If all tests show ✅, the feedback collection is fixed!")
    print("If any show ❌, there are still issues to address.")

if __name__ == "__main__":
    asyncio.run(test_feedback_scenarios())
