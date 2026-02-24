"""
Test critical fixes for production readiness
"""
import asyncio
from core.workflow import brs_workflow
from core.logger import setup_logger

logger = setup_logger(__name__)

async def test_edge_cases():
    """Test edge case handling"""
    print("="*80)
    print("TESTING EDGE CASE HANDLING")
    print("="*80)
    
    edge_cases = [
        ("", "Empty query"),
        ("a" * 5000, "Too long query"),
        ("bcdfg", "Gibberish"),
        ("How do I register", "Ambiguous query"),
        ("What's the weather?", "Out of scope"),
    ]
    
    passed = 0
    failed = 0
    
    for query, description in edge_cases:
        print(f"\nTest: {description}")
        print(f"Query: {query[:50]}...")
        
        try:
            await brs_workflow.initialize()
            
            inputs = {
                "user_input": query,
                "messages": [],
                "conversation_id": f"test_{description.replace(' ', '_')}",
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
            
            # Check if response is helpful
            if response and len(response) > 20:
                print(f"✅ PASS - Got helpful response")
                print(f"Response: {response[:100]}...")
                passed += 1
            else:
                print(f"❌ FAIL - Response too short or empty")
                failed += 1
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            failed += 1
    
    print(f"\n{'='*80}")
    print(f"Edge Cases: {passed}/{len(edge_cases)} passed")
    print(f"{'='*80}\n")
    
    return passed, failed

async def test_feedback_collection():
    """Test feedback collection"""
    print("="*80)
    print("TESTING FEEDBACK COLLECTION")
    print("="*80)
    
    feedback_queries = [
        "I'm concerned about the registration fees being too high",
        "I suggest reducing the family trust fee",
        "I think the Trust Bill should include more protections",
    ]
    
    passed = 0
    failed = 0
    
    for query in feedback_queries:
        print(f"\nTest: {query[:50]}...")
        
        try:
            await brs_workflow.initialize()
            
            inputs = {
                "user_input": query,
                "messages": [],
                "conversation_id": f"test_feedback_{passed}",
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
            
            # Check if feedback was collected
            if 'feedback' in response.lower() and ('recorded' in response.lower() or 'id' in response.lower()):
                print(f"✅ PASS - Feedback collected")
                print(f"Response: {response[:150]}...")
                passed += 1
            else:
                print(f"❌ FAIL - Feedback not confirmed")
                print(f"Response: {response[:150]}...")
                failed += 1
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            failed += 1
    
    print(f"\n{'='*80}")
    print(f"Feedback Collection: {passed}/{len(feedback_queries)} passed")
    print(f"{'='*80}\n")
    
    return passed, failed

async def test_contact_info():
    """Test contact information"""
    print("="*80)
    print("TESTING CONTACT INFORMATION")
    print("="*80)
    
    contact_queries = [
        "How can I contact BRS?",
        "What's the phone number for BRS?",
        "What's the email for BRS?",
    ]
    
    passed = 0
    failed = 0
    
    for query in contact_queries:
        print(f"\nTest: {query}")
        
        try:
            await brs_workflow.initialize()
            
            inputs = {
                "user_input": query,
                "messages": [],
                "conversation_id": f"test_contact_{passed}",
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
            
            # Check if contact info is in response
            has_phone = '+254' in response or '11 112 7000' in response
            has_email = 'eo@brs.go.ke' in response or 'email' in response.lower()
            
            if has_phone or has_email:
                print(f"✅ PASS - Contact info found")
                print(f"Response: {response[:150]}...")
                passed += 1
            else:
                print(f"❌ FAIL - Contact info missing")
                print(f"Response: {response[:150]}...")
                failed += 1
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            failed += 1
    
    print(f"\n{'='*80}")
    print(f"Contact Information: {passed}/{len(contact_queries)} passed")
    print(f"{'='*80}\n")
    
    return passed, failed

async def main():
    """Run all critical tests"""
    print("\n" + "="*80)
    print("BRS-SASA CRITICAL FIXES TEST")
    print("="*80)
    
    edge_passed, edge_failed = await test_edge_cases()
    feedback_passed, feedback_failed = await test_feedback_collection()
    contact_passed, contact_failed = await test_contact_info()
    
    total_passed = edge_passed + feedback_passed + contact_passed
    total_failed = edge_failed + feedback_failed + contact_failed
    total_tests = total_passed + total_failed
    
    print("\n" + "="*80)
    print("OVERALL RESULTS")
    print("="*80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed} ({total_passed/total_tests*100:.1f}%)")
    print(f"Failed: {total_failed} ({total_failed/total_tests*100:.1f}%)")
    print("="*80)
    
    if total_passed / total_tests >= 0.8:
        print("✅ CRITICAL FIXES WORKING - Ready for full testing")
    else:
        print("❌ CRITICAL FIXES NEED MORE WORK")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
