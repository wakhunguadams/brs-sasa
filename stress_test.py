"""
Stress Test for BRS-SASA API
Tests concurrent requests, rate limiting, and system stability
"""
import asyncio
import aiohttp
import time
from datetime import datetime
import statistics

API_BASE = "http://localhost:8000"

class StressTestResults:
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.rate_limited = 0
        self.response_times = []
        self.errors = []
        self.start_time = None
        self.end_time = None
    
    def add_result(self, success, response_time, status_code, error=None):
        self.total_requests += 1
        if success:
            self.successful_requests += 1
            self.response_times.append(response_time)
        else:
            self.failed_requests += 1
            if status_code == 429:
                self.rate_limited += 1
            if error:
                self.errors.append(error)
    
    def print_summary(self):
        duration = self.end_time - self.start_time
        print("\n" + "="*80)
        print("STRESS TEST RESULTS")
        print("="*80)
        print(f"Test Duration: {duration:.2f} seconds")
        print(f"Total Requests: {self.total_requests}")
        print(f"Successful: {self.successful_requests} ({self.successful_requests/self.total_requests*100:.1f}%)")
        print(f"Failed: {self.failed_requests} ({self.failed_requests/self.total_requests*100:.1f}%)")
        print(f"Rate Limited (429): {self.rate_limited}")
        
        if self.response_times:
            print(f"\nResponse Times:")
            print(f"  Min: {min(self.response_times):.3f}s")
            print(f"  Max: {max(self.response_times):.3f}s")
            print(f"  Mean: {statistics.mean(self.response_times):.3f}s")
            print(f"  Median: {statistics.median(self.response_times):.3f}s")
            if len(self.response_times) > 1:
                print(f"  Std Dev: {statistics.stdev(self.response_times):.3f}s")
        
        print(f"\nThroughput: {self.total_requests/duration:.2f} req/s")
        
        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(self.errors) > 5:
                print(f"  ... and {len(self.errors)-5} more")
        
        print("="*80)


async def make_request(session, url, method="GET", json_data=None):
    """Make a single HTTP request"""
    start = time.time()
    try:
        if method == "GET":
            async with session.get(url) as response:
                await response.text()
                return True, time.time() - start, response.status, None
        else:
            async with session.post(url, json=json_data) as response:
                await response.text()
                return True, time.time() - start, response.status, None
    except Exception as e:
        return False, time.time() - start, 0, str(e)


async def test_endpoint(session, results, endpoint, method="GET", json_data=None, count=10):
    """Test a single endpoint multiple times"""
    tasks = []
    for _ in range(count):
        tasks.append(make_request(session, f"{API_BASE}{endpoint}", method, json_data))
    
    responses = await asyncio.gather(*tasks)
    for success, response_time, status_code, error in responses:
        results.add_result(success, response_time, status_code, error)


async def run_stress_test():
    """Run comprehensive stress test"""
    results = StressTestResults()
    results.start_time = time.time()
    
    print("="*80)
    print("BRS-SASA STRESS TEST")
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: {API_BASE}")
    print("="*80)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Health Endpoints (Light)
        print("\n[1/7] Testing Health Endpoints (50 requests)...")
        await test_endpoint(session, results, "/health/live", count=25)
        await test_endpoint(session, results, "/health/ready", count=25)
        print(f"  ✓ Completed: {results.successful_requests}/{results.total_requests} successful")
        
        # Test 2: Info Endpoints (Light)
        print("\n[2/7] Testing Info Endpoints (50 requests)...")
        await test_endpoint(session, results, "/", count=25)
        await test_endpoint(session, results, "/info", count=25)
        print(f"  ✓ Completed: {results.successful_requests}/{results.total_requests} successful")
        
        # Test 3: Metrics Endpoint (Light)
        print("\n[3/7] Testing Metrics Endpoint (20 requests)...")
        await test_endpoint(session, results, "/metrics", count=20)
        print(f"  ✓ Completed: {results.successful_requests}/{results.total_requests} successful")
        
        # Test 4: Chat Completions - Simple (Medium)
        print("\n[4/7] Testing Chat Completions - Simple Queries (30 requests)...")
        simple_query = {
            "messages": [{"role": "user", "content": "Hello"}]
        }
        await test_endpoint(session, results, "/api/v1/chat/completions", "POST", simple_query, count=30)
        print(f"  ✓ Completed: {results.successful_requests}/{results.total_requests} successful")
        await asyncio.sleep(2)  # Brief pause
        
        # Test 5: Chat Completions - Knowledge Base (Heavy)
        print("\n[5/7] Testing Chat Completions - Knowledge Base Queries (20 requests)...")
        kb_query = {
            "messages": [{"role": "user", "content": "What are the fees for company registration?"}]
        }
        await test_endpoint(session, results, "/api/v1/chat/completions", "POST", kb_query, count=20)
        print(f"  ✓ Completed: {results.successful_requests}/{results.total_requests} successful")
        await asyncio.sleep(2)  # Brief pause
        
        # Test 6: Rate Limiting Test (Should trigger 429s)
        print("\n[6/7] Testing Rate Limiting (40 rapid requests)...")
        print("  (Expecting some 429 Rate Limit responses)")
        rapid_query = {
            "messages": [{"role": "user", "content": "Hi"}]
        }
        # Send all at once to trigger rate limiting
        tasks = []
        for _ in range(40):
            tasks.append(make_request(session, f"{API_BASE}/api/v1/chat/completions", "POST", rapid_query))
        responses = await asyncio.gather(*tasks)
        for success, response_time, status_code, error in responses:
            results.add_result(success, response_time, status_code, error)
        print(f"  ✓ Completed: {results.successful_requests}/{results.total_requests} successful")
        print(f"  ✓ Rate Limited: {results.rate_limited} requests")
        await asyncio.sleep(3)  # Wait for rate limit to reset
        
        # Test 7: Conversation Management (Light)
        print("\n[7/7] Testing Conversation Management (20 requests)...")
        conv_create = {
            "title": "Stress Test Conversation"
        }
        await test_endpoint(session, results, "/api/v1/conversations", "POST", conv_create, count=10)
        await test_endpoint(session, results, "/api/v1/conversations", "GET", count=10)
        print(f"  ✓ Completed: {results.successful_requests}/{results.total_requests} successful")
    
    results.end_time = time.time()
    results.print_summary()
    
    # Performance Assessment
    print("\n" + "="*80)
    print("PERFORMANCE ASSESSMENT")
    print("="*80)
    
    success_rate = results.successful_requests / results.total_requests * 100
    avg_response_time = statistics.mean(results.response_times) if results.response_times else 0
    
    if success_rate >= 95 and avg_response_time < 2.0:
        grade = "A - Excellent"
        status = "🟢 PRODUCTION READY"
    elif success_rate >= 90 and avg_response_time < 5.0:
        grade = "B - Good"
        status = "🟡 ACCEPTABLE"
    elif success_rate >= 80:
        grade = "C - Fair"
        status = "🟠 NEEDS IMPROVEMENT"
    else:
        grade = "D - Poor"
        status = "🔴 NOT READY"
    
    print(f"Overall Grade: {grade}")
    print(f"Status: {status}")
    print(f"\nKey Metrics:")
    print(f"  Success Rate: {success_rate:.1f}% (Target: >95%)")
    print(f"  Avg Response Time: {avg_response_time:.3f}s (Target: <2s)")
    print(f"  Rate Limiting: {'✓ Working' if results.rate_limited > 0 else '✗ Not Triggered'}")
    print(f"  Error Rate: {results.failed_requests/results.total_requests*100:.1f}% (Target: <5%)")
    
    print("\n" + "="*80)
    print(f"Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)


if __name__ == "__main__":
    print("\n⚠️  Make sure the server is running: python start_server.py")
    print("⚠️  This test will make ~250 requests to the API")
    input("\nPress Enter to start stress test...")
    
    asyncio.run(run_stress_test())
