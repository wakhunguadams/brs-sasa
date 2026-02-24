"""
Direct test of web search for ICT director information
"""
import asyncio
from tools.web_search_tool import search_web_duckduckgo
from tools.brs_website_scraper import scrape_brs_website

async def test_ict_director_search():
    """Test searching for ICT director information"""
    
    print("=" * 80)
    print("DIRECT WEB SEARCH TEST - ICT DIRECTOR AT BRS KENYA")
    print("=" * 80)
    
    # Test 1: Web search
    print("\n[TEST 1: Web Search]")
    print("-" * 80)
    query1 = "BRS Kenya ICT director"
    print(f"Query: {query1}\n")
    
    result1 = await search_web_duckduckgo.ainvoke({"query": query1, "max_results": 5})
    print(result1)
    
    # Test 2: Alternative web search
    print("\n\n[TEST 2: Alternative Web Search]")
    print("-" * 80)
    query2 = "Business Registration Service Kenya ICT manager director"
    print(f"Query: {query2}\n")
    
    result2 = await search_web_duckduckgo.ainvoke({"query": query2, "max_results": 5})
    print(result2)
    
    # Test 3: Website scraping
    print("\n\n[TEST 3: Website Scraping]")
    print("-" * 80)
    query3 = "ICT director manager"
    print(f"Query: {query3}\n")
    
    result3 = await scrape_brs_website.ainvoke({"query": query3, "section": "general"})
    print(result3)
    
    # Test 4: Senior management search
    print("\n\n[TEST 4: Senior Management Search]")
    print("-" * 80)
    query4 = "senior management team"
    print(f"Query: {query4}\n")
    
    result4 = await scrape_brs_website.ainvoke({"query": query4, "section": "general"})
    print(result4)
    
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    # Check if any result has ICT director information
    all_results = result1 + result2 + result3 + result4
    
    has_ict = "ict" in all_results.lower() or "i.c.t" in all_results.lower()
    has_director = "director" in all_results.lower()
    has_name = any(word[0].isupper() and len(word) > 3 for word in all_results.split())
    
    print(f"\n✓ ICT mentioned: {has_ict}")
    print(f"✓ Director mentioned: {has_director}")
    print(f"✓ Names found: {has_name}")
    
    if has_ict and has_director and has_name:
        print("\n✅ Information likely available - check results above")
    elif has_ict or has_director:
        print("\n⚠️  Partial information found - may need more specific search")
    else:
        print("\n❌ No specific ICT director information found")
        print("   This position may not be publicly listed on the website")
    
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_ict_director_search())
