"""Test BRS website scraping functionality"""
import asyncio
from tools.brs_website_scraper import scrape_brs_website, get_brs_contact_info

async def test_scraper():
    print("="*80)
    print("BRS WEBSITE SCRAPER TEST")
    print("="*80)
    
    # Test 1: Scrape for Director General
    print("\n[TEST 1] Scraping for Director General...")
    print("-"*80)
    result = await scrape_brs_website.ainvoke({
        "query": "Director General",
        "section": "leadership"
    })
    print(result)
    
    # Test 2: Scrape for Registrar
    print("\n\n[TEST 2] Scraping for Registrar of Companies...")
    print("-"*80)
    result = await scrape_brs_website.ainvoke({
        "query": "Registrar of Companies",
        "section": "leadership"
    })
    print(result)
    
    # Test 3: Get contact information
    print("\n\n[TEST 3] Getting BRS contact information...")
    print("-"*80)
    result = await get_brs_contact_info.ainvoke({})
    print(result)
    
    # Test 4: Scrape for Director ICT
    print("\n\n[TEST 4] Scraping for Director ICT...")
    print("-"*80)
    result = await scrape_brs_website.ainvoke({
        "query": "Director ICT",
        "section": "leadership"
    })
    print(result)
    
    print("\n" + "="*80)
    print("SCRAPER TESTS COMPLETED")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_scraper())
