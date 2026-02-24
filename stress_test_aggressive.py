"""
Aggressive Stress Test for BRS-SASA API
Tests rate limiting, concurrent load, and system limits
"""
import asyncio
import aiohttp
import time
from datetime import datetime
import statistics

API_BASE = "http://localhost:8000"

async def make_request(session, url, method="GET", json_data=None):
    """Make a single HTTP request"""
    start = time.time()
    try:
        if method == "GET":
            async with session.get(url) as response:
                await response.text()
                return response.status, time.time() - start, None
        else:
            async with session.post(url, json=json_data) as response:
                await response.text()
                return response.status, time.time() - start, None
    except Exception as e:
        return 0, time.time() - start, str(e)


async def burst_test(name, endpoint, method="GET", json_data=None, count=50):
    """Send burst of requests to test rate limiting"""
    print(f"\n{'='*80}")
    print(f"BURST TEST: {name}")
    print(f"{'='*80}")
    print(f"Sending {count} concurrent requests to {endpoint}...")
    
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(count):
            tasks.append(make_request(session, f"{API_BASE}{endpoint}", method, json_data))
        
        results = await asyncio.gather(*tasks)
    
    duration = time.time() - start_time
    
    # Analyze results
    status_codes = {}
    response_times = []
    errors = []
    
    for status, resp_time, error in results:
        status_codes[status] = status_codes.get(status, 0) + 1
        if status in [200, 201]:
            response_times.append(resp_time)
        if error:
            errors.append(error)
    
    # Print results
    print(f"\nResults:")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Throughput: {count/duration:.2f} req/s")
    print(f"\nStatus Codes:")
    for status, count_val in sorted(status_codes.items()):
        status_name = {
            200: "OK",
            201: "Created",
            400: "Bad Request",
            429: "Rate Limited",
            500: "Server Error",
            0: "Connection Error"
        }.get(status, "Unknown")
        print(f"    {status} ({status_name}): {count_val} ({count_val/count*100:.1f}%)")
    
    if response_times:
        print(f"\nResponse Times (successful requests):")
        print(f"    Min: {min(response_times):.3f}s")
        print(f"    Max: {max(response_times):.3f}s")
        print(f"    Mean: {statistics.mean(response_times):.3f}s")
        print(f"    Median: {statistics.median(response_times):.3f}s")
    
    if errors:
        print(f"\nErrors: {len(errors)}")
        for error in errors[:3]:
            print(f"    - {error}")
    
    rate_limited = status_codes.get(429, 0)
    if rate_limited > 0:
        print(f"\n✅ Rate Limiting Working: {rate_limited} requests blocked")
    else:
        print(f"\n⚠️  Rate Limiting Not Triggered")
    
    return status_codes, response_times


async def sustained_load_test():
    """Test sustained load over time"""
    print(f"\n{'='*80}")
    print(f"SUSTAINED LOAD TEST")
    print(f"{'='*80}")
    print(f"Sending requests continuously for 30 seconds...")
    
    start_time = time.time()
    request_count = 0
    success_count = 0
    rate_limited_count = 0
    
    async with aiohttp.ClientSession() as session:
        query = {"messages": [{"role": "user", "content": "Hello"}]}
        
        while time.time() - start_time < 30:
            status, _, _ = await make_request(
                session, 
                f"{API_BASE}/api/v1/chat/completions", 
                "POST", 
                query
            )
            request_count += 1
            if status == 200:
                success_count += 1
            elif status == 429:
                rate_limited_count += 1
            
            await asyncio.sleep(0.5)  # 2 requests per second
    
    duration = time.time() - start_time
    
    print(f"\nResults:")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Total Requests: {request_count}")
    print(f"  Successful: {success_count} ({success_count/request_count*100:.1f}%)")
    print(f"  Rate Limited: {rate_limited_count} ({rate_limited_count/request_count*100:.1f}%)")
    print(f"  Throughput: {request_count/duration:.2f} req/s")


async def run_aggressive_tests():
    """Run all aggressive tests"""
    print("\n" + "="*80)
    print("BRS-SASA AGGRESSIVE STRESS TEST")
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: {API_BASE}")
    print("="*80)
    
    # Test 1: Burst on health endpoint (should handle easily)
    await burst_test(
        "Health Endpoint Burst",
        "/health/live",
        count=100
    )
    
    await asyncio.sleep(2)
    
    # Test 2: Burst on chat completions (should trigger rate limiting)
    await burst_test(
        "Chat Completions Burst (Should Trigger Rate Limit)",
        "/api/v1/chat/completions",
        method="POST",
        json_data={"messages": [{"role": "user", "content": "Hi"}]},
        count=50
    )
    
    await asyncio.sleep(5)  # Wait for rate limit to reset
    
    # Test 3: Burst on conversation creation (should trigger rate limiting)
    await burst_test(
        "Conversation Creation Burst (Should Trigger Rate Limit)",
        "/api/v1/conversations",
        method="POST",
        json_data={"title": "Test"},
        count=50
    )
    
    await asyncio.sleep(5)
    
    # Test 4: Sustained load test
    await sustained_load_test()
    
    print("\n" + "="*80)
    print("AGGRESSIVE STRESS TEST COMPLETED")
    print("="*80)
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)


if __name__ == "__main__":
    print("\n⚠️  Make sure the server is running: python start_server.py")
    print("⚠️  This test will make ~250+ requests to test rate limiting")
    input("\nPress Enter to start aggressive stress test...")
    
    asyncio.run(run_aggressive_tests())
