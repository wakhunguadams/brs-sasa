"""
Final Comprehensive Endpoint Test
Tests all core functionality through the API endpoints
"""
import requests
import json
import time

API_BASE = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def test_query(query, category="General"):
    """Test a single query and analyze the response"""
    print(f"\n[{category}] Query: {query}")
    print("-"*80)
    
    start = time.time()
    response = requests.post(
        f"{API_BASE}/api/v1/chat/completions",
        json={"messages": [{"role": "user", "content": query}]},
        headers={"Content-Type": "application/json"}
    )
    duration = time.time() - start
    
    if response.status_code == 200:
        data = response.json()
        content = data['choices'][0]['message']['content']
        sources = data.get('sources', [])
        confidence = data.get('confidence', 0)
        
        # Count apologies
        apology_count = content.lower().count('apolog') + content.lower().count('sorry')
        
        # Print response summary
        print(f"✅ Status: {response.status_code}")
        print(f"⏱️  Duration: {duration:.2f}s")
        print(f"📊 Confidence: {confidence}")
        print(f"📚 Sources: {len(sources)} - {sources[:3] if sources else 'None'}")
        print(f"🚫 Apologies: {apology_count}")
        
        # Print response preview
        preview = content[:400] + "..." if len(content) > 400 else content
        print(f"\n💬 Response Preview:\n{preview}")
        
        return {
            "success": True,
            "duration": duration,
            "apologies": apology_count,
            "sources": len(sources),
            "confidence": confidence
        }
    else:
        print(f"❌ Status: {response.status_code}")
        print(f"Error: {response.text[:200]}")
        return {"success": False, "duration": duration}

def main():
    print_section("BRS-SASA FINAL ENDPOINT TEST")
    print(f"Target: {API_BASE}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # ========================================================================
    # CATEGORY 1: Basic Conversation
    # ========================================================================
    print_section("CATEGORY 1: Basic Conversation")
    
    results.append(test_query("Hello, who are you?", "Greeting"))
    time.sleep(1)
    
    results.append(test_query("What can you help me with?", "Capabilities"))
    time.sleep(1)
    
    # ========================================================================
    # CATEGORY 2: Knowledge Base Queries (Laws, Fees, Processes)
    # ========================================================================
    print_section("CATEGORY 2: Knowledge Base Queries")
    
    results.append(test_query(
        "What are the fees for registering a private company in Kenya?",
        "Company Fees"
    ))
    time.sleep(1)
    
    results.append(test_query(
        "What documents do I need to register a company?",
        "Company Requirements"
    ))
    time.sleep(1)
    
    results.append(test_query(
        "How do I register a Limited Liability Partnership?",
        "LLP Registration"
    ))
    time.sleep(1)
    
    # ========================================================================
    # CATEGORY 3: Current Information (Leadership, Contact)
    # ========================================================================
    print_section("CATEGORY 3: Current Information Queries")
    
    results.append(test_query(
        "Who is the Director General of BRS?",
        "Leadership - DG"
    ))
    time.sleep(1)
    
    results.append(test_query(
        "Who is the Registrar of Companies in Kenya?",
        "Leadership - Registrar"
    ))
    time.sleep(1)
    
    results.append(test_query(
        "How do I contact BRS?",
        "Contact Information"
    ))
    time.sleep(1)
    
    # ========================================================================
    # CATEGORY 4: Web Search Queries (News, Updates)
    # ========================================================================
    print_section("CATEGORY 4: Web Search Queries")
    
    results.append(test_query(
        "What is the latest news about BRS Kenya?",
        "Recent News"
    ))
    time.sleep(1)
    
    results.append(test_query(
        "Tell me about recent updates to BRS services",
        "Service Updates"
    ))
    time.sleep(1)
    
    # ========================================================================
    # CATEGORY 5: Complex Queries
    # ========================================================================
    print_section("CATEGORY 5: Complex Queries")
    
    results.append(test_query(
        "What is the difference between a company and a business name?",
        "Comparison"
    ))
    time.sleep(1)
    
    results.append(test_query(
        "How much does it cost to register a company and how long does it take?",
        "Multi-part"
    ))
    time.sleep(1)
    
    # ========================================================================
    # CATEGORY 6: Edge Cases
    # ========================================================================
    print_section("CATEGORY 6: Edge Cases")
    
    results.append(test_query("Fees?", "Very Short"))
    time.sleep(1)
    
    results.append(test_query(
        "I want to start a business in Kenya and need to know everything about registration including fees, requirements, documents, timeline, and who to contact",
        "Very Long"
    ))
    time.sleep(1)
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print_section("TEST SUMMARY")
    
    successful = sum(1 for r in results if r.get("success", False))
    total = len(results)
    
    total_apologies = sum(r.get("apologies", 0) for r in results if r.get("success", False))
    avg_duration = sum(r.get("duration", 0) for r in results if r.get("success", False)) / successful if successful > 0 else 0
    queries_with_sources = sum(1 for r in results if r.get("sources", 0) > 0)
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Total Queries: {total}")
    print(f"   Successful: {successful} ({successful/total*100:.1f}%)")
    print(f"   Failed: {total - successful}")
    print(f"   Average Duration: {avg_duration:.2f}s")
    print(f"   Queries with Sources: {queries_with_sources}")
    print(f"   Total Apologies: {total_apologies} 🎯")
    
    print(f"\n🎯 Key Metrics:")
    if total_apologies == 0:
        print(f"   ✅ ZERO APOLOGIES - Excellent!")
    elif total_apologies <= 2:
        print(f"   ✅ Very Few Apologies - Good!")
    else:
        print(f"   ⚠️  {total_apologies} Apologies - Could be improved")
    
    if avg_duration < 10:
        print(f"   ✅ Fast Response Time - Excellent!")
    elif avg_duration < 15:
        print(f"   ✅ Good Response Time")
    else:
        print(f"   ⚠️  Slow Response Time")
    
    if successful == total:
        print(f"   ✅ 100% Success Rate - Perfect!")
    elif successful >= total * 0.9:
        print(f"   ✅ High Success Rate - Good!")
    else:
        print(f"   ⚠️  Low Success Rate")
    
    print(f"\n🏆 Overall Assessment:")
    if total_apologies == 0 and successful == total and avg_duration < 15:
        print(f"   Grade: A+ - EXCELLENT")
        print(f"   Status: 🟢 PRODUCTION READY")
    elif total_apologies <= 2 and successful >= total * 0.9:
        print(f"   Grade: A - VERY GOOD")
        print(f"   Status: 🟢 PRODUCTION READY")
    else:
        print(f"   Grade: B - GOOD")
        print(f"   Status: 🟡 NEEDS MINOR IMPROVEMENTS")
    
    print("\n" + "="*80)
    print(f"Test Completed: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

if __name__ == "__main__":
    print("\n⚠️  Make sure the server is running: python start_server.py")
    print("\nStarting comprehensive endpoint test...")
    time.sleep(2)  # Give server time if just started
    main()
