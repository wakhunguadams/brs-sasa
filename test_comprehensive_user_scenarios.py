"""
Comprehensive User Scenario Tests for BRS-SASA
Tests all three agents (RAG, Conversation, Public Participation) with real-world scenarios
"""
import asyncio
from core.workflow import brs_workflow
from core.logger import setup_logger

logger = setup_logger(__name__)

# Test scenarios organized by agent
TEST_SCENARIOS = {
    "rag_agent": [
        {
            "name": "Basic Company Registration",
            "query": "How do I register a private limited company in Kenya?",
            "expected_keywords": ["private limited company", "KES 10,450", "registration"],
            "description": "Tests basic business registration query"
        },
        {
            "name": "Business Name Fees",
            "query": "What are the fees for registering a business name?",
            "expected_keywords": ["KES 500", "business name", "fee"],
            "description": "Tests fee-specific query"
        },
        {
            "name": "Registration Timeline",
            "query": "How long does company registration take?",
            "expected_keywords": ["3-5", "business days", "timeline"],
            "description": "Tests timeline query"
        },
        {
            "name": "LLP Documents",
            "query": "What documents do I need to register an LLP?",
            "expected_keywords": ["LLP", "documents", "registration"],
            "description": "Tests document requirements query"
        },
        {
            "name": "Foreign Director",
            "query": "Can a foreigner be a director in a Kenyan company?",
            "expected_keywords": ["foreigner", "director", "Kenyan"],
            "description": "Tests foreign ownership question"
        },
        {
            "name": "Registration Status",
            "query": "My registration number is PVT-ABCD1234, what's the status?",
            "expected_keywords": ["status", "registration", "PVT-ABCD1234"],
            "description": "Tests registration status check"
        },
        {
            "name": "Contact Information",
            "query": "How can I contact BRS?",
            "expected_keywords": ["contact", "phone", "email"],
            "description": "Tests contact information request"
        },
        {
            "name": "Cooperative Society",
            "query": "What are the fees for registering a cooperative society?",
            "expected_keywords": ["cooperative", "society", "fee"],
            "description": "Tests knowledge base not found scenario"
        },
        {
            "name": "Company Types",
            "query": "What are the different types of companies in Kenya?",
            "expected_keywords": ["company", "types", "private", "public"],
            "description": "Tests company types query"
        },
        {
            "name": "Registration Process",
            "query": "What is the step-by-step process for company registration?",
            "expected_keywords": ["step", "process", "registration"],
            "description": "Tests process query"
        }
    ],
    "conversation_agent": [
        {
            "name": "Current Director General",
            "query": "Who is the Director General of BRS?",
            "expected_keywords": ["Director General", "BRS", "Kenneth", "Gathuma"],
            "description": "Tests current leadership query"
        },
        {
            "name": "BRS Phone Number",
            "query": "What's the phone number for BRS?",
            "expected_keywords": ["phone", "+254", "11 112 7000"],
            "description": "Tests contact information query"
        },
        {
            "name": "Who Are You",
            "query": "Who are you?",
            "expected_keywords": ["BRS-SASA", "Business Registration Service"],
            "description": "Tests identity question"
        },
        {
            "name": "Greeting",
            "query": "Hello, how are you?",
            "expected_keywords": ["Hello", "BRS-SASA", "assistant"],
            "description": "Tests greeting response"
        },
        {
            "name": "Latest BRS News",
            "query": "What's the latest news about BRS?",
            "expected_keywords": ["news", "BRS", "latest"],
            "description": "Tests news query"
        },
        {
            "name": "BRS Revenue",
            "query": "What's the revenue of BRS for 2024?",
            "expected_keywords": ["revenue", "2024", "BRS"],
            "description": "Tests web search for current info"
        },
        {
            "name": "Office Location",
            "query": "Where is the BRS headquarters?",
            "expected_keywords": ["headquarters", "Ngong Road", "Nairobi"],
            "description": "Tests office location query"
        },
        {
            "name": "Office Hours",
            "query": "What are BRS office hours?",
            "expected_keywords": ["office hours", "8am", "5pm"],
            "description": "Tests hours of operation query"
        },
        {
            "name": "eCitizen Portal",
            "query": "What is the eCitizen portal for BRS?",
            "expected_keywords": ["eCitizen", "portal", "brs"],
            "description": "Tests eCitizen portal query"
        },
        {
            "name": "BRS Services",
            "query": "What services does BRS offer?",
            "expected_keywords": ["services", "registration", "BRS"],
            "description": "Tests services query"
        },
        {
            "name": "Board of Directors",
            "query": "Who is on the BRS Board of Directors?",
            "expected_keywords": ["Board", "Directors", "BRS"],
            "description": "Tests board of directors query"
        },
        {
            "name": "BRS Mission",
            "query": "What is BRS's mission?",
            "expected_keywords": ["mission", "BRS", "vision"],
            "description": "Tests mission/vision query"
        }
    ],
    "public_participation_agent": [
        {
            "name": "Trust Bill Overview",
            "query": "What is the Trust Administration Bill 2025 about?",
            "expected_keywords": ["Trust Administration Bill", "2025", "trust"],
            "description": "Tests legislation explanation"
        },
        {
            "name": "Uganda Comparison",
            "query": "How does Kenya's Trust Administration Bill compare to Uganda's trust laws?",
            "expected_keywords": ["Kenya", "Uganda", "compare", "trust"],
            "description": "Tests jurisdiction comparison - East Africa"
        },
        {
            "name": "Multiple Country Comparison",
            "query": "Compare trust laws in Kenya, Uganda, and Tanzania",
            "expected_keywords": ["Kenya", "Uganda", "Tanzania", "compare"],
            "description": "Tests multiple country comparison"
        },
        {
            "name": "Positive Feedback",
            "query": "I support the Trust Administration Bill, it's a good step forward",
            "expected_keywords": ["feedback", "recorded", "support"],
            "description": "Tests positive feedback collection"
        },
        {
            "name": "Negative Feedback",
            "query": "I'm concerned about the registration fees being too high",
            "expected_keywords": ["feedback", "concerned", "fees"],
            "description": "Tests negative feedback collection"
        },
        {
            "name": "Suggestion Feedback",
            "query": "I suggest reducing the family trust fee from KES 5,000 to KES 1,000",
            "expected_keywords": ["feedback", "suggest", "fee"],
            "description": "Tests suggestion feedback collection"
        },
        {
            "name": "Section 12 Query",
            "query": "What does Section 12 of the Trust Administration Bill say?",
            "expected_keywords": ["Section 12", "Trust Administration Bill"],
            "description": "Tests specific section query"
        },
        {
            "name": "UK Comparison",
            "query": "How does Kenya's Trust Bill compare to UK trust law?",
            "expected_keywords": ["Kenya", "UK", "compare", "trust"],
            "description": "Tests international comparison - UK"
        },
        {
            "name": "Complex Feedback",
            "query": "I think the Trust Bill should include more protections for vulnerable beneficiaries",
            "expected_keywords": ["feedback", "protections", "beneficiaries"],
            "description": "Tests complex feedback collection"
        },
        {
            "name": "Mixed Query",
            "query": "The Trust Administration Bill requires registration within 60 days, but I think this is too short",
            "expected_keywords": ["60 days", "feedback", "registration"],
            "description": "Tests mixed information + opinion query"
        }
    ],
    "edge_cases": [
        {
            "name": "Empty Query",
            "query": "",
            "expected_keywords": ["empty", "cannot", "provide"],
            "description": "Tests empty query handling"
        },
        {
            "name": "Very Long Query",
            "query": "This is a very long query with lots of text. " * 20,
            "expected_keywords": ["long", "query", "information"],
            "description": "Tests very long query handling"
        },
        {
            "name": "Ambiguous Query",
            "query": "How do I register?",
            "expected_keywords": ["register", "what", "company"],
            "description": "Tests ambiguous query handling"
        },
        {
            "name": "Out of Scope",
            "query": "What's the weather in Nairobi?",
            "expected_keywords": ["weather", "Nairobi", "BRS"],
            "description": "Tests out-of-scope query handling"
        },
        {
            "name": "Gibberish Input",
            "query": "asdkjh234kjhasd98f7qwe",
            "expected_keywords": ["understand", "question", "BRS"],
            "description": "Tests gibberish input handling"
        },
        {
            "name": "Special Characters",
            "query": "<script>alert('test')</script> Is this safe?",
            "expected_keywords": ["safe", "BRS", "question"],
            "description": "Tests special characters handling"
        },
        {
            "name": "Emoji Input",
            "query": " Kenya 🇰🇪 Business 🏢 Registration 💼 How?",
            "expected_keywords": ["Kenya", "Business", "Registration"],
            "description": "Tests emoji input handling"
        },
        {
            "name": "Multi-turn Context",
            "query": "What are the fees for that?",
            "context": ["How do I register a company?"],
            "expected_keywords": ["fees", "that", "registration"],
            "description": "Tests multi-turn context"
        }
    ]
}

async def run_test_scenario(agent_type: str, scenario: dict) -> dict:
    """Run a single test scenario"""
    query = scenario["query"]
    description = scenario["description"]
    
    print(f"\n{'='*80}")
    print(f"TEST: {scenario['name']}")
    print(f"Agent: {agent_type}")
    print(f"Description: {description}")
    print(f"Query: {query[:100]}{'...' if len(query) > 100 else ''}")
    print(f"{'='*80}")
    
    try:
        await brs_workflow.initialize()
        
        inputs = {
            "user_input": query,
            "messages": [],
            "conversation_id": f"test_{agent_type}_{scenario['name'].replace(' ', '_')}",
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
        agent = result.get('current_agent', 'unknown')
        sources = result.get('sources', [])
        confidence = result.get('confidence', 0.0)
        
        # Check expected keywords
        response_lower = response.lower()
        found_keywords = [kw for kw in scenario['expected_keywords'] if kw.lower() in response_lower]
        missing_keywords = [kw for kw in scenario['expected_keywords'] if kw.lower() not in response_lower]
        
        passed = len(missing_keywords) == 0
        
        return {
            "scenario": scenario['name'],
            "agent_type": agent_type,
            "query": query,
            "response": response,
            "agent": agent,
            "sources": sources,
            "confidence": confidence,
            "passed": passed,
            "found_keywords": found_keywords,
            "missing_keywords": missing_keywords,
            "error": None
        }
        
    except Exception as e:
        logger.error(f"Error in test {scenario['name']}: {str(e)}")
        return {
            "scenario": scenario['name'],
            "agent_type": agent_type,
            "query": query,
            "response": "",
            "agent": "error",
            "sources": [],
            "confidence": 0.0,
            "passed": False,
            "found_keywords": [],
            "missing_keywords": scenario['expected_keywords'],
            "error": str(e)
        }

async def run_all_tests():
    """Run all test scenarios"""
    print("="*80)
    print("BRS-SASA COMPREHENSIVE USER SCENARIO TESTS")
    print("="*80)
    print(f"Total Scenarios: {sum(len(scenarios) for scenarios in TEST_SCENARIOS.values())}")
    print("="*80)
    
    all_results = []
    
    # Run RAG agent tests
    print("\n" + "="*80)
    print("RAG AGENT TESTS")
    print("="*80)
    for scenario in TEST_SCENARIOS["rag_agent"]:
        result = await run_test_scenario("rag_agent", scenario)
        all_results.append(result)
        print(f"  {'✅ PASS' if result['passed'] else '❌ FAIL'}: {result['scenario']}")
        if not result['passed']:
            print(f"     Missing keywords: {result['missing_keywords']}")
    
    # Run Conversation agent tests
    print("\n" + "="*80)
    print("CONVERSATION AGENT TESTS")
    print("="*80)
    for scenario in TEST_SCENARIOS["conversation_agent"]:
        result = await run_test_scenario("conversation_agent", scenario)
        all_results.append(result)
        print(f"  {'✅ PASS' if result['passed'] else '❌ FAIL'}: {result['scenario']}")
        if not result['passed']:
            print(f"     Missing keywords: {result['missing_keywords']}")
    
    # Run Public Participation agent tests
    print("\n" + "="*80)
    print("PUBLIC PARTICIPATION AGENT TESTS")
    print("="*80)
    for scenario in TEST_SCENARIOS["public_participation_agent"]:
        result = await run_test_scenario("public_participation_agent", scenario)
        all_results.append(result)
        print(f"  {'✅ PASS' if result['passed'] else '❌ FAIL'}: {result['scenario']}")
        if not result['passed']:
            print(f"     Missing keywords: {result['missing_keywords']}")
    
    # Run edge case tests
    print("\n" + "="*80)
    print("EDGE CASE TESTS")
    print("="*80)
    for scenario in TEST_SCENARIOS["edge_cases"]:
        result = await run_test_scenario("edge_cases", scenario)
        all_results.append(result)
        print(f"  {'✅ PASS' if result['passed'] else '❌ FAIL'}: {result['scenario']}")
        if not result['passed']:
            print(f"     Missing keywords: {result['missing_keywords']}")
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total = len(all_results)
    passed = sum(1 for r in all_results if r['passed'])
    failed = total - passed
    error_count = sum(1 for r in all_results if r['error'])
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    print(f"Errors: {error_count}")
    
    # Breakdown by agent
    print("\nBreakdown by Agent:")
    for agent_type in ["rag_agent", "conversation_agent", "public_participation_agent", "edge_cases"]:
        agent_results = [r for r in all_results if r['agent_type'] == agent_type]
        agent_passed = sum(1 for r in agent_results if r['passed'])
        print(f"  {agent_type}: {agent_passed}/{len(agent_results)} passed")
    
    # Show failed scenarios
    failed_scenarios = [r for r in all_results if not r['passed'] and not r['error']]
    if failed_scenarios:
        print(f"\n{'='*80}")
        print("FAILED SCENARIOS")
        print(f"{'='*80}")
        for scenario in failed_scenarios:
            print(f"\n{scenario['agent_type'].upper()}: {scenario['scenario']}")
            print(f"Query: {scenario['query'][:100]}...")
            print(f"Response: {scenario['response'][:200]}...")
            print(f"Missing keywords: {scenario['missing_keywords']}")
    
    # Show errors
    error_scenarios = [r for r in all_results if r['error']]
    if error_scenarios:
        print(f"\n{'='*80}")
        print("ERROR SCENARIOS")
        print(f"{'='*80}")
        for scenario in error_scenarios:
            print(f"\n{scenario['agent_type'].upper()}: {scenario['scenario']}")
            print(f"Error: {scenario['error']}")
    
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}\n")
    
    return all_results

if __name__ == "__main__":
    asyncio.run(run_all_tests())
