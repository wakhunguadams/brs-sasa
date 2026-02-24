"""
Detailed test of BRS website scraping
Verify what information can be extracted from brs.go.ke
"""
import asyncio
from tools.brs_website_scraper import scrape_brs_website, get_brs_contact_info

async def test_specific_information():
    """Test scraping specific information from BRS website"""
    
    print("=" * 80)
    print("DETAILED BRS WEBSITE SCRAPING TEST")
    print("=" * 80)
    print("\nTesting what information can be extracted from https://brs.go.ke/")
    print()
    
    test_queries = [
        {
            "query": "Director General",
            "expected": ["director", "general", "leadership"],
            "description": "Leadership - Director General"
        },
        {
            "query": "Board of Directors",
            "expected": ["board", "director", "chairman"],
            "description": "Leadership - Board Members"
        },
        {
            "query": "Registrar General",
            "expected": ["registrar", "general"],
            "description": "Leadership - Registrar General"
        },
        {
            "query": "contact information",
            "expected": ["phone", "email", "address", "contact"],
            "description": "Contact Information"
        },
        {
            "query": "services",
            "expected": ["service", "registration", "business"],
            "description": "Services Offered"
        },
        {
            "query": "about BRS",
            "expected": ["business", "registration", "service"],
            "description": "About BRS"
        },
        {
            "query": "mission vision",
            "expected": ["mission", "vision", "mandate"],
            "description": "Mission and Vision"
        },
        {
            "query": "office location",
            "expected": ["office", "location", "address", "nairobi"],
            "description": "Office Location"
        }
    ]
    
    results = []
    
    for test in test_queries:
        print(f"\n{'=' * 80}")
        print(f"TEST: {test['description']}")
        print(f"Query: {test['query']}")
        print(f"{'=' * 80}")
        
        result = await scrape_brs_website.ainvoke({
            "query": test['query'],
            "section": "general"
        })
        
        # Check if expected keywords are in result
        found_keywords = []
        missing_keywords = []
        
        result_lower = result.lower()
        for keyword in test['expected']:
            if keyword in result_lower:
                found_keywords.append(keyword)
            else:
                missing_keywords.append(keyword)
        
        # Determine success
        success = len(found_keywords) > 0 and "couldn't find" not in result
        
        # Check for actual content (not just error message)
        has_content = len(result) > 300 and "brs.go.ke" in result.lower()
        
        results.append({
            "description": test['description'],
            "query": test['query'],
            "success": success and has_content,
            "found_keywords": found_keywords,
            "missing_keywords": missing_keywords,
            "content_length": len(result),
            "has_urls": "https://brs.go.ke" in result
        })
        
        if success and has_content:
            print(f"✅ PASS - Found relevant information")
            print(f"   Keywords found: {', '.join(found_keywords)}")
            print(f"   Content length: {len(result)} chars")
            print(f"   Has source URLs: {'Yes' if 'https://brs.go.ke' in result else 'No'}")
        else:
            print(f"❌ FAIL - Limited or no information found")
            print(f"   Keywords found: {', '.join(found_keywords) if found_keywords else 'None'}")
            print(f"   Keywords missing: {', '.join(missing_keywords)}")
            print(f"   Content length: {len(result)} chars")
        
        # Show sample of content
        print(f"\nSample content:")
        print("-" * 80)
        lines = result.split('\n')[:10]
        for line in lines:
            if line.strip():
                print(f"   {line[:75]}...")
        print("-" * 80)
    
    # Test contact info specifically
    print(f"\n{'=' * 80}")
    print("TEST: Contact Information Tool")
    print(f"{'=' * 80}")
    
    contact_result = await get_brs_contact_info.ainvoke({})
    
    # Check for essential contact details
    contact_checks = {
        "Phone": any(x in contact_result for x in ["+254", "011", "020"]),
        "Email": "@" in contact_result and "brs" in contact_result.lower(),
        "Address": "nairobi" in contact_result.lower(),
        "Website": "brs.go.ke" in contact_result.lower(),
        "Office Hours": "office" in contact_result.lower() or "hours" in contact_result.lower()
    }
    
    all_present = all(contact_checks.values())
    
    if all_present:
        print("✅ PASS - All contact information present")
    else:
        print("⚠️  PARTIAL - Some contact information missing")
    
    for item, present in contact_checks.items():
        status = "✓" if present else "✗"
        print(f"   {status} {item}")
    
    print(f"\nContact info length: {len(contact_result)} chars")
    print("\nSample contact info:")
    print("-" * 80)
    lines = contact_result.split('\n')[:15]
    for line in lines:
        if line.strip():
            print(f"   {line}")
    print("-" * 80)
    
    results.append({
        "description": "Contact Information Tool",
        "query": "get_brs_contact_info()",
        "success": all_present,
        "found_keywords": [k for k, v in contact_checks.items() if v],
        "missing_keywords": [k for k, v in contact_checks.items() if not v],
        "content_length": len(contact_result),
        "has_urls": "brs.go.ke" in contact_result.lower()
    })
    
    # Summary
    print(f"\n\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    
    total = len(results)
    passed = sum(1 for r in results if r['success'])
    failed = total - passed
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    
    print(f"\n{'=' * 80}")
    print("DETAILED RESULTS")
    print(f"{'=' * 80}")
    
    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"\n{status} {r['description']}")
        print(f"   Query: {r['query']}")
        print(f"   Content: {r['content_length']} chars")
        print(f"   Found: {', '.join(r['found_keywords']) if r['found_keywords'] else 'None'}")
        if r['missing_keywords']:
            print(f"   Missing: {', '.join(r['missing_keywords'])}")
    
    # Recommendations
    print(f"\n\n{'=' * 80}")
    print("RECOMMENDATIONS")
    print(f"{'=' * 80}")
    
    if passed == total:
        print("\n✅ All scraping tests passed!")
        print("   The BRS website scraper is working perfectly.")
        print("   It can extract all necessary information from brs.go.ke")
    elif passed / total >= 0.7:
        print("\n⚠️  Most scraping tests passed, but some improvements needed:")
        for r in results:
            if not r['success']:
                print(f"   - {r['description']}: {', '.join(r['missing_keywords'])}")
    else:
        print("\n❌ Multiple scraping tests failed:")
        print("   The website structure may have changed or scraping logic needs improvement")
        for r in results:
            if not r['success']:
                print(f"   - {r['description']}")
    
    print(f"\n{'=' * 80}\n")
    
    return passed, total

if __name__ == "__main__":
    passed, total = asyncio.run(test_specific_information())
    
    if passed == total:
        exit(0)
    else:
        exit(1)
