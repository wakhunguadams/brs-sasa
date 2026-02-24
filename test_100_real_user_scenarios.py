"""
100 Real User Scenarios Test
Simulates actual conversations real users would have with BRS-SASA
"""
import asyncio
from core.workflow import brs_workflow
from core.logger import setup_logger
import time

logger = setup_logger(__name__)

# 100 Real User Scenarios
REAL_USER_SCENARIOS = [
    # Business Registration Queries (20 scenarios)
    "Hi, I want to start a business in Kenya",
    "How much does it cost to register a company?",
    "I need to register my tech startup",
    "What documents do I need for company registration?",
    "Can I register a business online?",
    "How long will it take to get my business registered?",
    "I want to register a business name for my shop",
    "Do I need a lawyer to register a company?",
    "Can foreigners own businesses in Kenya?",
    "What's the difference between a company and a business name?",
    "I already have a business name, can I convert it to a company?",
    "How do I register a partnership with my friend?",
    "What is an LLP and should I register one?",
    "I want to register a company with 3 directors",
    "Can I be the only director and shareholder?",
    "Do I need a physical office to register?",
    "What's the minimum capital for a private company?",
    "Can I register a company from outside Kenya?",
    "I lost my certificate of incorporation, how do I get a copy?",
    "How do I change my company name?",
    
    # Fee-Related Queries (15 scenarios)
    "How much is business name registration?",
    "What are all the fees I need to pay?",
    "Is there a discount for students?",
    "Can I pay in installments?",
    "What payment methods do you accept?",
    "Why are the fees so expensive?",
    "Are there any hidden charges?",
    "Do I pay VAT on registration fees?",
    "How much to register a company with KES 100,000 capital?",
    "What's cheaper, business name or company?",
    "Do I pay annual fees after registration?",
    "How much for name reservation?",
    "Is registration free for NGOs?",
    "What if I can't afford the fees?",
    "Can the government waive fees for startups?",
    
    # Process & Timeline Queries (15 scenarios)
    "How fast can I get registered?",
    "What's the step by step process?",
    "Can I get same day registration?",
    "Why is my application taking so long?",
    "What happens after I submit my application?",
    "How do I track my application status?",
    "Can I expedite the process?",
    "What if my application is rejected?",
    "Do I need to come to the office in person?",
    "Can someone else submit on my behalf?",
    "What are the office hours?",
    "Do you work on weekends?",
    "How do I book an appointment?",
    "What if I made a mistake in my application?",
    "Can I cancel my application and get a refund?",
    
    # Contact & Support Queries (10 scenarios)
    "How can I reach you?",
    "What's your phone number?",
    "Do you have WhatsApp?",
    "Where is your office located?",
    "Can I email you my documents?",
    "Who do I talk to about my issue?",
    "Is there a helpline?",
    "Do you have customer support?",
    "Can I visit your office today?",
    "How do I make a complaint?",
    
    # Trust Administration Bill Queries (10 scenarios)
    "What is this Trust Bill about?",
    "Do I need to register my family trust?",
    "How much will trust registration cost?",
    "When does the Trust Bill become law?",
    "How does this affect existing trusts?",
    "What are the penalties for not registering?",
    "Can I give feedback on the Trust Bill?",
    "I think the fees are too high",
    "This bill will hurt small family trusts",
    "How is Kenya's trust law different from Tanzania?",
    
    # Feedback & Opinions (10 scenarios)
    "I'm not happy with the service",
    "The registration process is too complicated",
    "You should make it easier for young entrepreneurs",
    "Why can't I register on my phone?",
    "The website is confusing",
    "I suggest reducing fees for first-time businesses",
    "Great service, very helpful!",
    "The staff at the office were rude",
    "Can you add Mpesa payment option?",
    "I love the new online system",
    
    # Troubleshooting & Problems (10 scenarios)
    "My payment went through but no confirmation",
    "I can't log into eCitizen",
    "The website is not working",
    "I got an error message",
    "My documents were rejected",
    "Why was my name reservation declined?",
    "I paid twice by mistake",
    "Someone else registered my business name",
    "I think there's fraud on my account",
    "How do I report a problem?",
    
    # Conversational & Casual (5 scenarios)
    "Hey there!",
    "Good morning",
    "Thanks for your help",
    "You're very helpful",
    "Okay, I understand now",
    
    # Out of Scope (5 scenarios)
    "What's the weather like today?",
    "Who won the election?",
    "Can you help me with my taxes?",
    "How do I get a passport?",
    "Tell me a joke",
]

async def test_scenario(scenario_num: int, query: str) -> dict:
    """Test a single scenario"""
    try:
        await brs_workflow.initialize()
        
        inputs = {
            "user_input": query,
            "messages": [],
            "conversation_id": f"real_user_{scenario_num}",
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
        
        start_time = time.time()
        result = await brs_workflow.invoke(inputs)
        response_time = time.time() - start_time
        
        response = result.get('response', '')
        agent = result.get('current_agent', 'unknown')
        
        # Evaluate response quality
        has_response = len(response) > 20
        is_helpful = any(word in response.lower() for word in ['register', 'fee', 'contact', 'brs', 'kenya', 'trust', 'bill'])
        is_error = 'error' in response.lower() or 'try again' in response.lower()
        
        return {
            "scenario_num": scenario_num,
            "query": query,
            "response": response,
            "agent": agent,
            "response_time": response_time,
            "has_response": has_response,
            "is_helpful": is_helpful,
            "is_error": is_error,
            "passed": has_response and not is_error
        }
        
    except Exception as e:
        logger.error(f"Error in scenario {scenario_num}: {str(e)}")
        return {
            "scenario_num": scenario_num,
            "query": query,
            "response": "",
            "agent": "error",
            "response_time": 0,
            "has_response": False,
            "is_helpful": False,
            "is_error": True,
            "passed": False
        }

async def run_all_scenarios():
    """Run all 100 scenarios"""
    print("\n" + "="*80)
    print("BRS-SASA: 100 REAL USER SCENARIOS TEST")
    print("="*80)
    print(f"Total Scenarios: {len(REAL_USER_SCENARIOS)}")
    print("="*80 + "\n")
    
    results = []
    passed = 0
    failed = 0
    total_time = 0
    
    for i, query in enumerate(REAL_USER_SCENARIOS, 1):
        print(f"\r[{i}/{len(REAL_USER_SCENARIOS)}] Testing: {query[:50]}...", end="", flush=True)
        
        result = await test_scenario(i, query)
        results.append(result)
        
        if result['passed']:
            passed += 1
        else:
            failed += 1
        
        total_time += result['response_time']
    
    print("\n\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)
    
    # Overall stats
    print(f"\nTotal Scenarios: {len(results)}")
    print(f"Passed: {passed} ({passed/len(results)*100:.1f}%)")
    print(f"Failed: {failed} ({failed/len(results)*100:.1f}%)")
    print(f"Average Response Time: {total_time/len(results):.2f}s")
    
    # Agent breakdown
    agent_counts = {}
    for result in results:
        agent = result['agent']
        agent_counts[agent] = agent_counts.get(agent, 0) + 1
    
    print(f"\nAgent Breakdown:")
    for agent, count in sorted(agent_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {agent}: {count} ({count/len(results)*100:.1f}%)")
    
    # Response time breakdown
    fast = sum(1 for r in results if r['response_time'] < 5)
    medium = sum(1 for r in results if 5 <= r['response_time'] < 10)
    slow = sum(1 for r in results if r['response_time'] >= 10)
    
    print(f"\nResponse Time Breakdown:")
    print(f"  Fast (<5s): {fast} ({fast/len(results)*100:.1f}%)")
    print(f"  Medium (5-10s): {medium} ({medium/len(results)*100:.1f}%)")
    print(f"  Slow (>10s): {slow} ({slow/len(results)*100:.1f}%)")
    
    # Failed scenarios
    failed_results = [r for r in results if not r['passed']]
    if failed_results:
        print(f"\n{'='*80}")
        print(f"FAILED SCENARIOS ({len(failed_results)})")
        print(f"{'='*80}")
        for result in failed_results[:10]:  # Show first 10
            print(f"\n{result['scenario_num']}. {result['query']}")
            print(f"   Agent: {result['agent']}")
            print(f"   Response: {result['response'][:100]}...")
        
        if len(failed_results) > 10:
            print(f"\n... and {len(failed_results)-10} more failed scenarios")
    
    # Sample successful responses
    successful_results = [r for r in results if r['passed']]
    if successful_results:
        print(f"\n{'='*80}")
        print(f"SAMPLE SUCCESSFUL RESPONSES (5 random)")
        print(f"{'='*80}")
        import random
        samples = random.sample(successful_results, min(5, len(successful_results)))
        for result in samples:
            print(f"\nUser: {result['query']}")
            print(f"Agent: {result['agent']}")
            print(f"Response: {result['response'][:200]}...")
            print(f"Time: {result['response_time']:.2f}s")
    
    # Production readiness assessment
    print(f"\n{'='*80}")
    print("PRODUCTION READINESS ASSESSMENT")
    print(f"{'='*80}")
    
    pass_rate = passed / len(results) * 100
    avg_time = total_time / len(results)
    
    if pass_rate >= 90 and avg_time < 10:
        grade = "A - EXCELLENT"
        status = "✅ PRODUCTION READY"
    elif pass_rate >= 80 and avg_time < 15:
        grade = "B - GOOD"
        status = "✅ READY FOR STAGING"
    elif pass_rate >= 70:
        grade = "C - FAIR"
        status = "⚠️  NEEDS IMPROVEMENT"
    else:
        grade = "D - POOR"
        status = "❌ NOT READY"
    
    print(f"\nOverall Grade: {grade}")
    print(f"Status: {status}")
    print(f"\nKey Metrics:")
    print(f"  Pass Rate: {pass_rate:.1f}% (Target: >90%)")
    print(f"  Avg Response Time: {avg_time:.2f}s (Target: <10s)")
    print(f"  Error Rate: {failed/len(results)*100:.1f}% (Target: <10%)")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")
    
    return results

if __name__ == "__main__":
    print("\n⚠️  This test will run 100 scenarios and may take 10-20 minutes")
    print("⚠️  Make sure the system is running properly")
    input("\nPress Enter to start...")
    
    asyncio.run(run_all_scenarios())
