"""
Test query: Who is the ICT director at BRS Kenya?
This tests if the system can find current leadership information
"""
import asyncio
from core.workflow import brs_workflow

async def test_ict_director_query():
    """Test asking about ICT director at BRS"""
    
    query = "Who is the ICT director at BRS Kenya?"
    
    print("=" * 80)
    print("TESTING REAL USER QUERY")
    print("=" * 80)
    print(f"\nQuery: {query}")
    print("\nProcessing...\n")
    print("-" * 80)
    
    # Create workflow
    from core.workflow import brs_workflow
    
    # Run query
    config = {"configurable": {"thread_id": "test_ict_director"}}
    
    result = await brs_workflow.invoke(
        {"user_input": query, "messages": []},
        config=config
    )
    
    # Extract response
    response = result.get("response", "No response generated")
    query_type = result.get("query_type", "unknown")
    agent = result.get("current_agent", "unknown")
    
    print(f"\nQuery Type: {query_type}")
    print(f"Agent Used: {agent}")
    print("\n" + "=" * 80)
    print("RESPONSE")
    print("=" * 80)
    print(response)
    print("=" * 80)
    
    # Analyze response quality
    print("\n" + "=" * 80)
    print("RESPONSE ANALYSIS")
    print("=" * 80)
    
    response_lower = response.lower()
    
    checks = {
        "Has ICT/IT mention": any(x in response_lower for x in ["ict", "i.c.t", "information technology", "it director"]),
        "Has name": any(len(word) > 3 and word[0].isupper() for word in response.split()),
        "Has BRS mention": "brs" in response_lower,
        "Has source/URL": any(x in response_lower for x in ["http", "source:", "from:", "brs.go.ke"]),
        "Not error message": "error" not in response_lower and "couldn't find" not in response_lower,
        "Reasonable length": len(response) > 100
    }
    
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
    
    all_passed = all(checks.values())
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ EXCELLENT - Query handled perfectly!")
    elif sum(checks.values()) >= 4:
        print("✅ GOOD - Query handled well with minor gaps")
    elif sum(checks.values()) >= 2:
        print("⚠️  PARTIAL - Some information found but incomplete")
    else:
        print("❌ POOR - Unable to find relevant information")
    print("=" * 80)
    
    return all_passed or sum(checks.values()) >= 4

if __name__ == "__main__":
    success = asyncio.run(test_ict_director_query())
    exit(0 if success else 1)
