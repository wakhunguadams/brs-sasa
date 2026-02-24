"""Quick test script for web search functionality"""
import asyncio
from tools.web_search_tool import search_web_duckduckgo, search_brs_news

async def test_web_search():
    print("=" * 70)
    print("Testing Web Search Tool")
    print("=" * 70)
    
    # Test 1: Search for BRS Kenya director
    print("\n1. Searching for: 'BRS Kenya director 2024'")
    print("-" * 70)
    result = await search_web_duckduckgo.ainvoke({"query": "BRS Kenya director 2024", "max_results": 3})
    print(result)
    
    # Test 2: Search for BRS revenue
    print("\n\n2. Searching for: 'Business Registration Service Kenya revenue 2023'")
    print("-" * 70)
    result = await search_web_duckduckgo.ainvoke({"query": "Business Registration Service Kenya revenue 2023", "max_results": 3})
    print(result)
    
    # Test 3: Search for BRS news
    print("\n\n3. Searching for recent BRS news")
    print("-" * 70)
    result = await search_brs_news.ainvoke({"query": "Business Registration Service Kenya", "max_results": 3})
    print(result)
    
    print("\n" + "=" * 70)
    print("Web search tests completed!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_web_search())
