"""
Comprehensive test for web search and scraping tools
Tests if tools can find information that users would search for on the internet
"""
import asyncio
import sys
from tools.web_search_tool import search_web_duckduckgo, search_brs_news
from tools.brs_website_scraper import scrape_brs_website, get_brs_contact_info

# Test scenarios based on what users would search for
TEST_SCENARIOS = [
    {
        "category": "Leadership & Management",
        "queries": [
            "Who is the Director General of BRS Kenya?",
            "BRS Kenya leadership team",
            "BRS Kenya Registrar General",
        ],
        "tools": ["web_search", "scrape_website"]
    },
    {
        "category": "Contact Information",
        "queries": [
            "BRS Kenya phone number",
            "BRS Kenya email address",
            "BRS Kenya office location",
        ],
        "tools": ["scrape_website", "contact_info"]
    },
    {
        "category": "Current News & Updates",
        "queries": [
            "BRS Kenya latest news",
            "Business Registration Service Kenya updates",
            "BRS Kenya new services",
        ],
        "tools": ["news_search", "web_search"]
    },
    {
        "category": "Financial & Statistics",
        "queries": [
            "BRS Kenya revenue 2024",
            "BRS Kenya registration statistics",
            "How many companies registered in Kenya",
        ],
        "tools": ["web_search", "news_search"]
    },
    {
        "category": "Services & Features",
        "queries": [
            "BRS Kenya online services",
            "How to register business online Kenya",
            "BRS eCitizen services",
        ],
        "tools": ["web_search", "scrape_website"]
    },
    {
        "category": "Social Media & Online Presence",
        "queries": [
            "BRS Kenya LinkedIn",
            "BRS Kenya social media",
            "Business Registration Service Kenya LinkedIn profile",
        ],
        "tools": ["web_search"]
    }
]

async def test_web_search(query: str) -> dict:
    """Test web search tool"""
    try:
        result = await search_web_duckduckgo.ainvoke({"query": query, "max_results": 3})
        
        # Check if result contains useful information
        has_urls = "http" in result or "https" in result
        has_content = len(result) > 100
        not_error = "Error" not in result and "not available" not in result
        
        return {
            "success": has_urls and has_content and not_error,
            "result": result[:500] + "..." if len(result) > 500 else result,
            "full_length": len(result)
        }
    except Exception as e:
        return {
            "success": False,
            "result": f"Error: {str(e)}",
            "full_length": 0
        }

async def test_news_search(query: str) -> dict:
    """Test news search tool"""
    try:
        result = await search_brs_news.ainvoke({"query": query, "max_results": 3})
        
        has_urls = "http" in result or "https" in result
        has_content = len(result) > 100
        not_error = "Error" not in result and "not available" not in result
        
        return {
            "success": has_urls and has_content and not_error,
            "result": result[:500] + "..." if len(result) > 500 else result,
            "full_length": len(result)
        }
    except Exception as e:
        return {
            "success": False,
            "result": f"Error: {str(e)}",
            "full_length": 0
        }

async def test_scrape_website(query: str) -> dict:
    """Test website scraping tool"""
    try:
        result = await scrape_brs_website.ainvoke({"query": query, "section": "general"})
        
        has_content = len(result) > 100
        has_source = "brs.go.ke" in result.lower()
        not_error = "Error" not in result or "couldn't find" in result  # couldn't find is OK
        
        return {
            "success": has_content and has_source and not_error,
            "result": result[:500] + "..." if len(result) > 500 else result,
            "full_length": len(result)
        }
    except Exception as e:
        return {
            "success": False,
            "result": f"Error: {str(e)}",
            "full_length": 0
        }

async def test_contact_info() -> dict:
    """Test contact info tool"""
    try:
        result = await get_brs_contact_info.ainvoke({})
        
        # Check for essential contact information
        has_phone = "+254" in result or "011" in result or "020" in result
        has_email = "@" in result and "brs" in result.lower()
        has_address = "nairobi" in result.lower() or "address" in result.lower()
        has_website = "brs.go.ke" in result.lower()
        
        return {
            "success": has_phone and has_email and has_address and has_website,
            "result": result[:500] + "..." if len(result) > 500 else result,
            "full_length": len(result),
            "details": {
                "has_phone": has_phone,
                "has_email": has_email,
                "has_address": has_address,
                "has_website": has_website
            }
        }
    except Exception as e:
        return {
            "success": False,
            "result": f"Error: {str(e)}",
            "full_length": 0
        }

async def run_comprehensive_test():
    """Run comprehensive test of all web tools"""
    print("=" * 80)
    print("COMPREHENSIVE WEB TOOLS TEST")
    print("=" * 80)
    print("\nTesting if our tools can find information users would search for online...")
    print()
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for scenario in TEST_SCENARIOS:
        print(f"\n{'=' * 80}")
        print(f"CATEGORY: {scenario['category']}")
        print(f"{'=' * 80}")
        
        for query in scenario['queries']:
            print(f"\nQuery: {query}")
            print("-" * 80)
            
            # Test each recommended tool
            if "web_search" in scenario['tools']:
                total_tests += 1
                print("\n[Testing: Web Search]")
                result = await test_web_search(query)
                
                if result['success']:
                    print(f"✅ PASS - Found {result['full_length']} chars of data")
                    passed_tests += 1
                else:
                    print(f"❌ FAIL - {result['result']}")
                    failed_tests.append({
                        "category": scenario['category'],
                        "query": query,
                        "tool": "web_search",
                        "reason": result['result']
                    })
                
                print(f"Sample: {result['result'][:200]}...")
            
            if "news_search" in scenario['tools']:
                total_tests += 1
                print("\n[Testing: News Search]")
                result = await test_news_search(query)
                
                if result['success']:
                    print(f"✅ PASS - Found {result['full_length']} chars of data")
                    passed_tests += 1
                else:
                    print(f"❌ FAIL - {result['result']}")
                    failed_tests.append({
                        "category": scenario['category'],
                        "query": query,
                        "tool": "news_search",
                        "reason": result['result']
                    })
                
                print(f"Sample: {result['result'][:200]}...")
            
            if "scrape_website" in scenario['tools']:
                total_tests += 1
                print("\n[Testing: Website Scraping]")
                result = await test_scrape_website(query)
                
                if result['success']:
                    print(f"✅ PASS - Found {result['full_length']} chars of data")
                    passed_tests += 1
                else:
                    print(f"❌ FAIL - {result['result']}")
                    failed_tests.append({
                        "category": scenario['category'],
                        "query": query,
                        "tool": "scrape_website",
                        "reason": result['result']
                    })
                
                print(f"Sample: {result['result'][:200]}...")
            
            if "contact_info" in scenario['tools']:
                total_tests += 1
                print("\n[Testing: Contact Info]")
                result = await test_contact_info()
                
                if result['success']:
                    print(f"✅ PASS - All contact info present")
                    if 'details' in result:
                        print(f"   Phone: {'✓' if result['details']['has_phone'] else '✗'}")
                        print(f"   Email: {'✓' if result['details']['has_email'] else '✗'}")
                        print(f"   Address: {'✓' if result['details']['has_address'] else '✗'}")
                        print(f"   Website: {'✓' if result['details']['has_website'] else '✗'}")
                    passed_tests += 1
                else:
                    print(f"❌ FAIL - {result['result']}")
                    failed_tests.append({
                        "category": scenario['category'],
                        "query": query,
                        "tool": "contact_info",
                        "reason": result['result']
                    })
                
                print(f"Sample: {result['result'][:200]}...")
    
    # Summary
    print(f"\n\n{'=' * 80}")
    print("TEST SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"Failed: {len(failed_tests)} ({len(failed_tests)/total_tests*100:.1f}%)")
    
    if failed_tests:
        print(f"\n{'=' * 80}")
        print("FAILED TESTS")
        print(f"{'=' * 80}")
        for failure in failed_tests:
            print(f"\nCategory: {failure['category']}")
            print(f"Query: {failure['query']}")
            print(f"Tool: {failure['tool']}")
            print(f"Reason: {failure['reason'][:200]}...")
    
    print(f"\n{'=' * 80}")
    if passed_tests == total_tests:
        print("✅ ALL TESTS PASSED - Web tools working perfectly!")
    elif passed_tests / total_tests >= 0.8:
        print("⚠️  MOSTLY WORKING - Some improvements needed")
    else:
        print("❌ NEEDS ATTENTION - Multiple tools failing")
    print(f"{'=' * 80}\n")
    
    return passed_tests, total_tests, failed_tests

if __name__ == "__main__":
    passed, total, failures = asyncio.run(run_comprehensive_test())
    
    # Exit with appropriate code
    if passed == total:
        sys.exit(0)
    else:
        sys.exit(1)
