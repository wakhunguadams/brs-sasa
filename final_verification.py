"""
Final Verification Script for BRS-SASA Production Deployment
Tests all critical functionality before deployment
"""
import asyncio
from core.workflow import brs_workflow
from core.logger import setup_logger

logger = setup_logger(__name__)

async def verify_system():
    """Run final verification checks"""
    print("\n" + "="*80)
    print("BRS-SASA FINAL VERIFICATION")
    print("="*80)
    print("\nVerifying system is ready for production deployment...\n")
    
    checks = []
    
    # Check 1: Edge Case Handling
    print("[1/7] Verifying edge case handling...")
    try:
        await brs_workflow.initialize()
        
        # Test empty query
        result = await brs_workflow.invoke({
            "user_input": "",
            "messages": [],
            "conversation_id": "verify_empty",
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
        })
        
        if "cannot be empty" in result.get('response', '').lower():
            print("  ✅ Edge case handling working")
            checks.append(True)
        else:
            print("  ❌ Edge case handling failed")
            checks.append(False)
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        checks.append(False)
    
    # Check 2: Contact Information
    print("[2/7] Verifying contact information...")
    try:
        result = await brs_workflow.invoke({
            "user_input": "What's the phone number for BRS?",
            "messages": [],
            "conversation_id": "verify_contact",
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
        })
        
        response = result.get('response', '')
        if '+254' in response or '11 112 7000' in response:
            print("  ✅ Contact information working")
            checks.append(True)
        else:
            print("  ❌ Contact information failed")
            checks.append(False)
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        checks.append(False)
    
    # Check 3: Feedback Collection
    print("[3/7] Verifying feedback collection...")
    try:
        result = await brs_workflow.invoke({
            "user_input": "I'm concerned about the registration fees",
            "messages": [],
            "conversation_id": "verify_feedback",
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
        })
        
        response = result.get('response', '')
        if 'feedback' in response.lower() and 'id' in response.lower():
            print("  ✅ Feedback collection working")
            checks.append(True)
        else:
            print("  ❌ Feedback collection failed")
            checks.append(False)
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        checks.append(False)
    
    # Check 4: RAG Agent
    print("[4/7] Verifying RAG agent...")
    try:
        result = await brs_workflow.invoke({
            "user_input": "How do I register a company?",
            "messages": [],
            "conversation_id": "verify_rag",
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
        })
        
        response = result.get('response', '')
        if len(response) > 100 and 'register' in response.lower():
            print("  ✅ RAG agent working")
            checks.append(True)
        else:
            print("  ❌ RAG agent failed")
            checks.append(False)
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        checks.append(False)
    
    # Check 5: Conversation Agent
    print("[5/7] Verifying conversation agent...")
    try:
        result = await brs_workflow.invoke({
            "user_input": "Who are you?",
            "messages": [],
            "conversation_id": "verify_conversation",
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
        })
        
        response = result.get('response', '')
        if 'BRS-SASA' in response or 'Business Registration Service' in response:
            print("  ✅ Conversation agent working")
            checks.append(True)
        else:
            print("  ❌ Conversation agent failed")
            checks.append(False)
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        checks.append(False)
    
    # Check 6: Public Participation Agent
    print("[6/7] Verifying public participation agent...")
    try:
        result = await brs_workflow.invoke({
            "user_input": "What is the Trust Administration Bill about?",
            "messages": [],
            "conversation_id": "verify_pp",
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
        })
        
        response = result.get('response', '')
        if len(response) > 50:
            print("  ✅ Public participation agent working")
            checks.append(True)
        else:
            print("  ❌ Public participation agent failed")
            checks.append(False)
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        checks.append(False)
    
    # Check 7: Out of Scope Handling
    print("[7/7] Verifying out of scope handling...")
    try:
        result = await brs_workflow.invoke({
            "user_input": "What's the weather in Nairobi?",
            "messages": [],
            "conversation_id": "verify_oos",
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
        })
        
        response = result.get('response', '')
        if 'cannot' in response.lower() or 'only provide' in response.lower():
            print("  ✅ Out of scope handling working")
            checks.append(True)
        else:
            print("  ❌ Out of scope handling failed")
            checks.append(False)
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        checks.append(False)
    
    # Summary
    print("\n" + "="*80)
    print("VERIFICATION RESULTS")
    print("="*80)
    
    passed = sum(checks)
    total = len(checks)
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\nTotal Checks: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    
    print("\n" + "="*80)
    
    if pass_rate >= 90:
        print("✅ SYSTEM READY FOR PRODUCTION DEPLOYMENT")
        print("="*80)
        print("\nAll critical systems verified and working correctly.")
        print("The system can be deployed to staging immediately.")
        return True
    else:
        print("❌ SYSTEM NOT READY FOR PRODUCTION")
        print("="*80)
        print(f"\nOnly {passed}/{total} checks passed.")
        print("Please fix failing checks before deployment.")
        return False

if __name__ == "__main__":
    result = asyncio.run(verify_system())
    exit(0 if result else 1)
