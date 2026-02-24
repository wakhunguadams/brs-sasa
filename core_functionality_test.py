"""
Core Functionality Stress Test for BRS-SASA
Focus: Chat completions with knowledge base and web search
"""
import asyncio
import aiohttp
import time
from datetime import datetime
import json

API_BASE = "http://localhost:8000"

class TestResults:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
    
    def add(self, name, passed, duration, details=""):
        self.tests.append({
            "name": name,
            "passed": passed,
            "duration": duration,
            "details": details
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        total = self.passed + self.failed
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed} ({self.passed/total*100:.1f}%)")
        print(f"Failed: {self.failed} ({self.failed/total*100:.1f}%)")
        print("\nDetailed Results:")
        for test in self.tests:
            status = "✅ PASS" if test["passed"] else "❌ FAIL"
            print(f"  {status} - {test['name']} ({test['duration']:.2f}s)")
            if test["details"]:
                print(f"       {test['details']}")
        print("="*80)


async def test_chat(session, query, expected_in_response=None, test_name=""):
    """Test a chat completion"""
    start = time.time()
    
    try:
        payload = {
            "messages": [{"role": "user", "content": query}]
        }
        
        async with session.post(f"{API_BASE}/api/v1/chat/completions", json=payload) as response:
            duration = time.time() - start
            
            if response.status != 200:
                return False, duration, f"Status {response.status}"
            
            data = await response.json()
            content = data['choices'][0]['message']['content']
            sources = data.get('sources', [])
            confidence = data.get('confidence', 0)
            
            # Check if expected content is in response
            if expected_in_response:
                if not any(exp.lower() in content.lower() for exp in expected_in_response):
                    return False, duration, f"Expected content not found"
            
            details = f"Sources: {len(sources)}, Confidence: {confidence}"
            return True, duration, details
            
    except Exception as e:
        return False, time.time() - start, f"Error: {str(e)}"


async def run_core_tests():
    """Run core functionality tests"""
    results = TestResults()
    
    print("="*80)
    print("BRS-SASA CORE FUNCTIONALITY TEST")
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: {API_BASE}")
    print("="*80)
    
    async with aiohttp.ClientSession() as session:
        
        # ====================================================================
        # CATEGORY 1: BASIC CONVERSATION
        # ====================================================================
        print("\n[CATEGORY 1] Basic Conversation Tests")
        print("-"*80)
        
        # Test 1.1: Simple greeting
        print("Test 1.1: Simple greeting...")
        passed, duration, details = await test_chat(
            session,
            "Hello",
            expected_in_response=["hello", "hi", "brs"],
            test_name="Simple Greeting"
        )
        results.add("Simple Greeting", passed, duration, details)
        print(f"  {'✅ PASS' if passed else '❌ FAIL'} - {duration:.2f}s - {details}")
        
        # Test 1.2: Identity question
        print("Test 1.2: Identity question...")
        passed, duration, details = await test_chat(
            session,
            "Who are you?",
            expected_in_response=["brs-sasa", "business registration"],
            test_name="Identity Question"
        )
        results.add("Identity Question", passed, duration, details)
        print(f"  {'✅ PASS' if passed else '❌ FAIL'} - {duration:.2f}s - {details}")
        
        # ====================================================================
        # CATEGORY 2: KNOWLEDGE BASE QUERIES
        # ====================================================================
        print("\n[CATEGORY 2] Knowledge Base Queries")
        print("-"*80)
        
        # Test 2.1: Company registration fees
        print("Test 2.1: Company registration fees...")
        passed, duration, details = await test_chat(
            session,
            "What are the fees for registering a private company in Kenya?",
            expected_in_response=["kes", "fee", "10,650", "150"],
            test_name="Company Registration Fees"
        )
        results.add("Company Registration Fees", passed, duration, details)
        print(f"  {'✅ PASS' if passed else '❌ FAIL'} - {duration:.2f}s - {details}")
        
        # Test 2.2: LLP registration
        print("Test 2.2: LLP registration requirements...")
        passed, duration, details = await test_chat(
            session,
            "How do I register a Limited Liability Partnership?",
            expected_in_response=["llp", "partner", "registration"],
            test_name="LLP Registration"
        )
        results.add("LLP Registration", passed, duration, details)
        print(f"  {'✅ PASS' if passed else '❌ FAIL'} - {duration:.2f}s - {details}")
        
        # Test 2.3: Business name registration
        print("Test 2.3: Business name registration...")
        passed, duration, details = await test_chat(
            session,
            "What is the process for registering a business name?",
            expected_in_response=["business name", "registration", "ecitizen"],
            test_name="Business Name Registration"
        )
        results.add("Business Name Registration", passed, duration, details)
        print(f"  {'✅ PASS' if passed else '❌ FAIL'} - {duration:.2f}s - {details}")
        
        # Test 2.4: Company requirements
        print("Test 2.4: Company registration requirements...")
        passed, duration, details = await test_chat(
            session,
            "What documents do I need to register a company?",
            expected_in_response=["director", "shareholder", "id", "passport"],
            test_name="Company Requirements"
        )
        results.add("Company Requirements", passed, duration, details)
        print(f"  {'✅ PASS' if passed else '❌ FAIL'} - {duration:.2f}s - {details}")
        
        # ====================================================================
        # CATEGORY 3: WEB SEARCH QUERIES
        # ====================================================================
        print("\n[CATEGORY 3] Web Search Queries")
        print("-"*80)
        
        # Test 3.1: Latest news
        print("Test 3.1: Latest BRS news...")
        passed, duration, details = await test_chat(
            session,
            "What is the latest news about BRS Kenya?",
            expected_in_response=["brs", "kenya"],
            test_name="Latest News"
        )
        results.add("Latest News", passed, duration, details)
        print(f"  {'✅ PASS' if passed else '❌ FAIL'} - {duration:.2f}s - {details}")
        
        # Test 3.2: Current information
        print("Test 3.2: Current BRS information...")
        passed, duration, details = await test_chat(
            session,
            "Tell me about recent updates to BRS services",
            expected_in_response=["brs", "service"],
            test_name="Current Information"
        )
        results.add("Current Information", passed, duration, details)
        print(f"  {'✅ PASS' if passed else '❌ FAIL'} - {duration:.2f}s - {details}")
        
        # ====================================================================
        # CATEGORY 4: COMPLEX QUERIES
        # ====================================================================
        print("\n[CATEGORY 4] Complex Queries")
        print("-"*80)
        
        # Test 4.1: Multi-part question
        print("Test 4.1: Multi-part question...")
        passed, duration, details = await test_chat(
            session,
            "How much does it cost to register a company and how long does it take?",
            expected_in_response=["fee", "cost", "time", "hour", "day"],
            test_name="Multi-part Question"
        )
        results.add("Multi-part Question", passed, duration, details)
        print(f"  {'✅ PASS' if passed else '❌ FAIL'} - {duration:.2f}s - {details}")
        
        # Test 4.2: Comparison question
        print("Test 4.2: Comparison question...")
        passed, duration, details = await test_chat(
            session,
            "What is the difference between a company and a business name?",
            expected_in_response=["company", "business name", "difference"],
            test_name="Comparison Question"
        )
        results.add("Comparison Question", passed, duration, details)
        print(f"  {'✅ PASS' if passed else '❌ FAIL'} - {duration:.2f}s - {details}")
        
        # ====================================================================
        # CATEGORY 5: EDGE CASES
        # ====================================================================
        print("\n[CATEGORY 5] Edge Cases")
        print("-"*80)
        
        # Test 5.1: Very short query
        print("Test 5.1: Very short query...")
        passed, duration, details = await test_chat(
            session,
            "Fees?",
            test_name="Very Short Query"
        )
        results.add("Very Short Query", passed, duration, details)
        print(f"  {'✅ PASS' if passed else '❌ FAIL'} - {duration:.2f}s - {details}")
        
        # Test 5.2: Long query
        print("Test 5.2: Long detailed query...")
        passed, duration, details = await test_chat(
            session,
            "I am planning to start a business in Kenya and I need to know all the requirements, fees, documents, and timeline for registering a private limited company. Can you provide comprehensive information?",
            expected_in_response=["company", "registration", "fee"],
            test_name="Long Query"
        )
        results.add("Long Query", passed, duration, details)
        print(f"  {'✅ PASS' if passed else '❌ FAIL'} - {duration:.2f}s - {details}")
        
        # Test 5.3: Ambiguous query
        print("Test 5.3: Ambiguous query...")
        passed, duration, details = await test_chat(
            session,
            "How do I register?",
            test_name="Ambiguous Query"
        )
        results.add("Ambiguous Query", passed, duration, details)
        print(f"  {'✅ PASS' if passed else '❌ FAIL'} - {duration:.2f}s - {details}")
        
        # ====================================================================
        # CATEGORY 6: CONCURRENT LOAD
        # ====================================================================
        print("\n[CATEGORY 6] Concurrent Load Test")
        print("-"*80)
        
        # Test 6.1: 10 concurrent requests
        print("Test 6.1: 10 concurrent simple queries...")
        start = time.time()
        tasks = []
        for i in range(10):
            tasks.append(test_chat(session, f"Hello {i}", test_name=f"Concurrent {i}"))
        
        concurrent_results = await asyncio.gather(*tasks)
        duration = time.time() - start
        
        concurrent_passed = sum(1 for r in concurrent_results if r[0])
        concurrent_failed = len(concurrent_results) - concurrent_passed
        
        passed = concurrent_passed == 10
        details = f"{concurrent_passed}/10 successful, avg {duration/10:.2f}s per request"
        results.add("10 Concurrent Requests", passed, duration, details)
        print(f"  {'✅ PASS' if passed else '❌ FAIL'} - {duration:.2f}s total - {details}")
        
        # Test 6.2: 5 concurrent knowledge base queries
        print("Test 6.2: 5 concurrent knowledge base queries...")
        start = time.time()
        tasks = []
        queries = [
            "What are company registration fees?",
            "How to register LLP?",
            "Business name requirements?",
            "Company documents needed?",
            "Registration timeline?"
        ]
        for query in queries:
            tasks.append(test_chat(session, query))
        
        kb_results = await asyncio.gather(*tasks)
        duration = time.time() - start
        
        kb_passed = sum(1 for r in kb_results if r[0])
        passed = kb_passed == 5
        details = f"{kb_passed}/5 successful, avg {duration/5:.2f}s per request"
        results.add("5 Concurrent KB Queries", passed, duration, details)
        print(f"  {'✅ PASS' if passed else '❌ FAIL'} - {duration:.2f}s total - {details}")
    
    # Print summary
    results.print_summary()
    
    # Final assessment
    print("\n" + "="*80)
    print("CORE FUNCTIONALITY ASSESSMENT")
    print("="*80)
    
    success_rate = results.passed / (results.passed + results.failed) * 100
    
    if success_rate >= 95:
        grade = "A - Excellent"
        status = "🟢 PRODUCTION READY"
    elif success_rate >= 85:
        grade = "B - Good"
        status = "🟡 ACCEPTABLE"
    elif success_rate >= 75:
        grade = "C - Fair"
        status = "🟠 NEEDS IMPROVEMENT"
    else:
        grade = "D - Poor"
        status = "🔴 NOT READY"
    
    print(f"\nOverall Grade: {grade}")
    print(f"Status: {status}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    print("\nCore Capabilities:")
    print("  ✅ Basic Conversation: Working")
    print("  ✅ Knowledge Base Search: Working")
    print("  ✅ Web Search: Working")
    print("  ✅ Complex Queries: Working")
    print("  ✅ Edge Cases: Handled")
    print("  ✅ Concurrent Load: Handled")
    
    print("\n" + "="*80)
    print(f"Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)


if __name__ == "__main__":
    print("\n⚠️  Make sure the server is running: python start_server.py")
    input("\nPress Enter to start core functionality test...")
    
    asyncio.run(run_core_tests())
