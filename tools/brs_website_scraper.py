"""BRS Website Scraper Tool - Fetch current information from official BRS website
Uses dynamic sitemap discovery to cover ALL pages on brs.go.ke"""
from typing import Optional, List, Dict
from langchain_core.tools import tool
import logging
import asyncio
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Cached sitemap URLs and timestamp
_sitemap_cache: List[str] = []
_sitemap_cache_time: Optional[datetime] = None
_SITEMAP_CACHE_TTL = timedelta(hours=1)

# Smart URL groupings by topic - prioritized subsets for faster lookups
_URL_GROUPS: Dict[str, List[str]] = {
    "leadership": [
        "/senior-management/",
        "/board-of-directors/",
        "/who-we-are/",
        "/what-we-do/",
    ],
    "contact": [
        "/contact/",
        "/contact-us/",
    ],
    "statistics": [
        "/statistics/",
        "/companies-registry-statistics/",
        "/mpsr/",
        "/office-of-the-official-receiver/",
    ],
    "fees": [
        "/fees/",
        "/fee-schedule-companies-registry/",
        "/fee-schedule-official-receiver/",
        "/fee-schedule-collateral-registry/",
        "/official-receiver-fees/",
        "/miscellaneous-fees/",
        "/fees-payable-to-the-high-court-ag/",
        "/fees-chargeable-by-companies-for-services-provided-under-the-act/",
    ],
    "services": [
        "/services/",
        "/companies-registry/",
        "/the-collateral-registry/",
        "/entities-registered/",
        "/official-receiver-in-insolvency/",
        "/about-hire-purchase-registry/",
        "/model-articles/",
        "/manuals/",
        "/practice-notes/",
        "/forms/",
        "/boi-notice1/",
    ],
    "legislation": [
        "/legislations/",
        "/acts/",
        "/regulations/",
    ],
    "insolvency": [
        "/bankruptcy/",
        "/liquidation-by-court/",
        "/no-asset-procedure/",
        "/summary-installment-order/",
        "/individual-voluntary-arrangement/",
        "/company-voluntary-arrangement/",
        "/administration/",
        "/company-voluntary-liquidation/",
        "/document-inspection-obtaining-copies-of-documents/",
        "/insolvency/",
        "/bankruptcy-2/",
    ],
    "publications": [
        "/annual-report/",
        "/strategic-plan/",
        "/guides-and-handbooks/",
        "/branding-guidelines/",
        "/research-publications/",
        "/doing-business-reports/",
    ],
    "news": [
        "/press-room/",
        "/notices/",
        "/newsletter/",
        "/podcasts/",
    ],
    "opportunities": [
        "/careers/",
        "/tender-opportunities/",
    ],
    "about": [
        "/who-we-are/",
        "/what-we-do/",
        "/achievements/",
        "/development-partners/",
        "/about-us/",
    ],
}

# Keywords that map to URL groups
_TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "leadership": [
        "director", "manager", "management", "leader", "ceo", "dg",
        "director general", "registrar", "staff", "team", "head",
        "ict", "finance", "hr", "human resource", "cpa", "who is",
        "official receiver", "board", "chairman", "chairperson",
    ],
    "contact": [
        "contact", "phone", "email", "address", "location", "office",
        "reach", "call", "tel", "fax", "nairobi",
    ],
    "statistics": [
        "statistics", "data", "numbers", "registered", "how many",
        "total", "count", "annual", "report", "metric", "performance",
    ],
    "fees": [
        "fee", "fees", "cost", "price", "charge", "payment", "pay",
        "how much", "schedule", "tariff",
    ],
    "services": [
        "service", "register", "registration", "company", "business name",
        "llp", "partnership", "foreign company", "collateral", "mpsr",
        "hire purchase", "compliance", "ecitizen",
    ],
    "legislation": [
        "law", "act", "legislation", "regulation", "bill", "legal",
        "companies act", "partnership act", "insolvency act",
    ],
    "insolvency": [
        "insolvency", "bankrupt", "bankruptcy", "liquidation", "winding up",
        "receivership", "administration", "voluntary arrangement",
    ],
    "publications": [
        "publication", "report", "strategic plan", "handbook", "guide",
        "branding", "research", "doing business",
    ],
    "news": [
        "news", "press", "notice", "newsletter", "podcast", "announcement",
        "update", "latest",
    ],
    "opportunities": [
        "career", "job", "tender", "vacancy", "employment", "work",
        "opportunity", "recruitment",
    ],
    "about": [
        "about", "who we are", "what we do", "achievement", "partner",
        "history", "mandate", "mission", "vision",
    ],
}


async def _fetch_sitemap_urls() -> List[str]:
    """Fetch all page URLs from the BRS website sitemap, with caching."""
    global _sitemap_cache, _sitemap_cache_time

    # Return cached if fresh
    if _sitemap_cache and _sitemap_cache_time and (datetime.now() - _sitemap_cache_time) < _SITEMAP_CACHE_TTL:
        logger.info(f"Using cached sitemap ({len(_sitemap_cache)} URLs)")
        return _sitemap_cache

    try:
        import httpx
        logger.info("Fetching BRS sitemap from brs.go.ke/page-sitemap.xml")

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get("https://brs.go.ke/page-sitemap.xml")
            if response.status_code == 200:
                # Parse URLs from XML sitemap
                urls = re.findall(r'<loc>(https://brs\.go\.ke/[^<]+)</loc>', response.text)
                if urls:
                    _sitemap_cache = urls
                    _sitemap_cache_time = datetime.now()
                    logger.info(f"Fetched {len(urls)} URLs from sitemap")
                    return urls

    except Exception as e:
        logger.warning(f"Failed to fetch sitemap: {str(e)}")

    # Fallback: comprehensive hardcoded list
    logger.info("Using fallback URL list")
    fallback = [
        "https://brs.go.ke/",
        "https://brs.go.ke/who-we-are/",
        "https://brs.go.ke/what-we-do/",
        "https://brs.go.ke/senior-management/",
        "https://brs.go.ke/board-of-directors/",
        "https://brs.go.ke/achievements/",
        "https://brs.go.ke/development-partners/",
        "https://brs.go.ke/about-us/",
        "https://brs.go.ke/services/",
        "https://brs.go.ke/companies-registry/",
        "https://brs.go.ke/entities-registered/",
        "https://brs.go.ke/the-collateral-registry/",
        "https://brs.go.ke/official-receiver-in-insolvency/",
        "https://brs.go.ke/about-hire-purchase-registry/",
        "https://brs.go.ke/contact/",
        "https://brs.go.ke/contact-us/",
        "https://brs.go.ke/statistics/",
        "https://brs.go.ke/companies-registry-statistics/",
        "https://brs.go.ke/mpsr/",
        "https://brs.go.ke/office-of-the-official-receiver/",
        "https://brs.go.ke/fees/",
        "https://brs.go.ke/fee-schedule-companies-registry/",
        "https://brs.go.ke/fee-schedule-official-receiver/",
        "https://brs.go.ke/fee-schedule-collateral-registry/",
        "https://brs.go.ke/official-receiver-fees/",
        "https://brs.go.ke/miscellaneous-fees/",
        "https://brs.go.ke/fees-payable-to-the-high-court-ag/",
        "https://brs.go.ke/fees-chargeable-by-companies-for-services-provided-under-the-act/",
        "https://brs.go.ke/legislations/",
        "https://brs.go.ke/acts/",
        "https://brs.go.ke/regulations/",
        "https://brs.go.ke/model-articles/",
        "https://brs.go.ke/manuals/",
        "https://brs.go.ke/practice-notes/",
        "https://brs.go.ke/forms/",
        "https://brs.go.ke/boi-notice1/",
        "https://brs.go.ke/bankruptcy/",
        "https://brs.go.ke/liquidation-by-court/",
        "https://brs.go.ke/no-asset-procedure/",
        "https://brs.go.ke/summary-installment-order/",
        "https://brs.go.ke/individual-voluntary-arrangement/",
        "https://brs.go.ke/company-voluntary-arrangement/",
        "https://brs.go.ke/administration/",
        "https://brs.go.ke/company-voluntary-liquidation/",
        "https://brs.go.ke/document-inspection-obtaining-copies-of-documents/",
        "https://brs.go.ke/insolvency/",
        "https://brs.go.ke/bankruptcy-2/",
        "https://brs.go.ke/annual-report/",
        "https://brs.go.ke/strategic-plan/",
        "https://brs.go.ke/guides-and-handbooks/",
        "https://brs.go.ke/branding-guidelines/",
        "https://brs.go.ke/research-publications/",
        "https://brs.go.ke/doing-business-reports/",
        "https://brs.go.ke/press-room/",
        "https://brs.go.ke/notices/",
        "https://brs.go.ke/newsletter/",
        "https://brs.go.ke/podcasts/",
        "https://brs.go.ke/careers/",
        "https://brs.go.ke/tender-opportunities/",
        "https://brs.go.ke/gallery/",
        "https://brs.go.ke/photos/",
        "https://brs.go.ke/videos/",
        "https://brs.go.ke/whistle-blowing/",
        "https://brs.go.ke/brs-feedback/",
        "https://brs.go.ke/frequently-asked-questions/",
        "https://brs.go.ke/boi-notice/",
    ]
    _sitemap_cache = fallback
    _sitemap_cache_time = datetime.now()
    return fallback


def _detect_topics(query: str) -> List[str]:
    """Detect which topic groups a query belongs to."""
    query_lower = query.lower()
    matched_topics = []

    for topic, keywords in _TOPIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                if topic not in matched_topics:
                    matched_topics.append(topic)
                break

    return matched_topics if matched_topics else ["about"]


def _get_priority_urls(topics: List[str], all_urls: List[str]) -> List[str]:
    """Get prioritized URL list based on detected topics."""
    base_url = "https://brs.go.ke"
    priority_urls = []

    # First add topic-specific URLs
    for topic in topics:
        group_paths = _URL_GROUPS.get(topic, [])
        for path in group_paths:
            full_url = f"{base_url}{path}"
            if full_url in all_urls and full_url not in priority_urls:
                priority_urls.append(full_url)

    # Always include homepage as it may have relevant info
    homepage = f"{base_url}/"
    if homepage not in priority_urls:
        priority_urls.insert(0, homepage)

    # Cap at 15 URLs to avoid excessive scraping
    return priority_urls[:15]


async def _scrape_page(client, url: str, query: str, keywords: List[str]) -> Optional[Dict]:
    """Scrape a single page and extract relevant content."""
    try:
        from bs4 import BeautifulSoup

        response = await client.get(url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'lxml')

        # Remove script, style, nav, footer elements
        for element in soup(["script", "style", "nav", "footer"]):
            element.decompose()

        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        lines = text.split('\n')
        relevant_lines = []

        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            if not line_lower:
                continue

            # Check if line contains any of the query keywords
            if any(keyword in line_lower for keyword in keywords):
                # Include broader context (±5 lines)
                start = max(0, i - 5)
                end = min(len(lines), i + 6)
                context = lines[start:end]
                relevant_lines.extend(context)

        if relevant_lines:
            # Remove duplicates while preserving order
            seen = set()
            unique_lines = []
            for line in relevant_lines:
                stripped = line.strip()
                # Lower minimum length to 3 to catch short titles like "Director ICT"
                if stripped and stripped not in seen and len(stripped) > 3:
                    seen.add(stripped)
                    unique_lines.append(stripped)

            if unique_lines:
                return {
                    'url': url,
                    'content': '\n'.join(unique_lines[:30])  # Limit to 30 lines
                }

    except Exception as e:
        logger.warning(f"Error scraping {url}: {str(e)}")

    return None


@tool
async def scrape_brs_website(query: str, section: str = "general") -> str:
    """
    Scrape the official BRS Kenya website (https://brs.go.ke/) for current information.
    Dynamically discovers ALL pages on the site via the sitemap.

    Use this tool when users ask about:
    - Current BRS leadership (Director General, Registrars, Directors)
    - BRS contact information (phone, email, office locations)
    - Current services and their status
    - Recent announcements on the BRS website
    - Office hours and locations
    - Statistics and performance data
    - Fee schedules and costs
    - Legislation, acts, and regulations
    - Careers and tender opportunities
    - Any information that should be on the official BRS website

    Args:
        query: What information to look for (e.g., "ICT director", "contact information", "statistics")
        section: Hint for focus area - "leadership", "contact", "services", "fees",
                 "statistics", "legislation", or "general"

    Returns:
        Information scraped from the BRS website with source URLs.
    """
    try:
        try:
            import httpx
            from bs4 import BeautifulSoup
        except ImportError:
            return (
                "Web scraping is not available. Required libraries not installed. "
                "Please install: pip install httpx beautifulsoup4 lxml"
            )

        logger.info(f"Scraping BRS website for: {query} (section: {section})")

        # Fetch all available URLs from sitemap
        all_urls = await _fetch_sitemap_urls()

        # Detect topics from query
        topics = _detect_topics(query)

        # If section hint is provided and valid, prioritize it
        if section != "general" and section in _URL_GROUPS:
            if section not in topics:
                topics.insert(0, section)

        logger.info(f"Detected topics: {topics}")

        # Get prioritized URLs
        urls_to_check = _get_priority_urls(topics, all_urls)
        logger.info(f"Will check {len(urls_to_check)} prioritized URLs")

        # Prepare search keywords
        query_lower = query.lower()
        keywords = [kw.strip() for kw in query_lower.split() if len(kw.strip()) > 1]
        # Also add the full query as a keyword for phrase matching
        if len(keywords) > 1:
            keywords.append(query_lower)

        results = []

        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            # Scrape pages concurrently in batches of 5
            for i in range(0, len(urls_to_check), 5):
                batch = urls_to_check[i:i + 5]
                tasks = [_scrape_page(client, url, query, keywords) for url in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in batch_results:
                    if isinstance(result, dict) and result:
                        results.append(result)

                # If we have enough results, stop early
                if len(results) >= 5:
                    break

        if not results:
            return (
                f"I searched the official BRS website (https://brs.go.ke/) across "
                f"{len(urls_to_check)} pages but couldn't find specific information "
                f"about '{query}'. This could mean:\n"
                f"1. The information is not publicly available on the website\n"
                f"2. The website structure has changed\n"
                f"3. The information may be in downloadable documents (PDFs)\n\n"
                f"I recommend:\n"
                f"- Visiting https://brs.go.ke/ directly\n"
                f"- Contacting BRS via their official contact channels\n"
                f"- Checking the specific section on their website"
            )

        # Format results
        formatted_results = []
        formatted_results.append(f"Information from BRS Official Website about '{query}':")
        formatted_results.append(f"Search Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        formatted_results.append("=" * 60)

        for idx, result in enumerate(results, 1):
            formatted_results.append(f"\nFrom: {result['url']}")
            formatted_results.append("-" * 60)
            formatted_results.append(result['content'])

        formatted_results.append("\n" + "=" * 60)
        formatted_results.append("Source: Official BRS Website (https://brs.go.ke/)")
        formatted_results.append("Note: Please verify this information by visiting the official website.")

        return "\n".join(formatted_results)

    except Exception as e:
        logger.error(f"Error in BRS website scraper: {str(e)}")
        return (
            f"I encountered an error while trying to access the BRS website: {str(e)}\n\n"
            f"Please try:\n"
            f"1. Visiting https://brs.go.ke/ directly\n"
            f"2. Contacting BRS through their official channels\n"
            f"3. Asking me a different question about BRS services"
        )


@tool
async def get_brs_leadership() -> str:
    """
    Get current BRS Kenya senior management and leadership information.

    Use this tool when users ask about:
    - Who is the Director General of BRS
    - Who is the ICT Director at BRS
    - BRS senior management team
    - BRS leadership and directors
    - Any specific director or head of department at BRS

    Returns:
        Current BRS leadership and senior management information from the official website.
    """
    try:
        import httpx
        from bs4 import BeautifulSoup
    except ImportError:
        return (
            "Leadership information retrieval is not available. Required libraries not installed. "
            "Please install: pip install httpx beautifulsoup4 lxml"
        )

    try:
        logger.info("Fetching BRS leadership information")

        urls = [
            "https://brs.go.ke/senior-management/",
            "https://brs.go.ke/board-of-directors/",
        ]

        all_content = []

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            for url in urls:
                try:
                    response = await client.get(url)
                    if response.status_code != 200:
                        continue

                    soup = BeautifulSoup(response.text, 'lxml')

                    # Remove unnecessary elements
                    for element in soup(["script", "style", "nav", "footer"]):
                        element.decompose()

                    # Get text content
                    text = soup.get_text(separator='\n', strip=True)
                    lines = text.split('\n')

                    # Extract leadership-related content
                    leadership_lines = []
                    leadership_keywords = [
                        'director', 'registrar', 'manager', 'head', 'chairman',
                        'chairperson', 'ceo', 'general', 'ict', 'finance',
                        'legal', 'human resource', 'hr', 'corporate', 'strategy',
                        'secretary', 'cpa', 'advocate', 'mr.', 'ms.', 'mrs.',
                        'dr.', 'prof.', 'mandate', 'oversee', 'hsc', 'ogw',
                    ]

                    for i, line in enumerate(lines):
                        line_lower = line.lower().strip()
                        if not line_lower:
                            continue

                        if any(kw in line_lower for kw in leadership_keywords):
                            # Include broader context (±5 lines)
                            start = max(0, i - 5)
                            end = min(len(lines), i + 6)
                            context = lines[start:end]
                            leadership_lines.extend(context)

                    if leadership_lines:
                        seen = set()
                        unique_lines = []
                        for line in leadership_lines:
                            stripped = line.strip()
                            if stripped and stripped not in seen and len(stripped) > 3:
                                seen.add(stripped)
                                unique_lines.append(stripped)

                        if unique_lines:
                            page_label = "Senior Management" if "senior" in url else "Board of Directors"
                            all_content.append(f"\n--- {page_label} ---")
                            all_content.append(f"Source: {url}")
                            all_content.extend(unique_lines[:40])

                except Exception as e:
                    logger.warning(f"Error fetching {url}: {str(e)}")
                    continue

        if all_content:
            result = "BRS Kenya Leadership & Senior Management:\n"
            result += "=" * 60 + "\n"
            result += '\n'.join(all_content)
            result += "\n\n" + "=" * 60 + "\n"
            result += "Source: Official BRS Website (https://brs.go.ke/)\n"
            result += "Note: Please verify by visiting the official website."
            return result

        # Fallback
        return (
            "BRS Kenya Leadership Information:\n"
            "=" * 60 + "\n\n"
            "I was unable to fetch the latest leadership information from the BRS website.\n\n"
            "Please visit these pages directly:\n"
            "- Senior Management: https://brs.go.ke/senior-management/\n"
            "- Board of Directors: https://brs.go.ke/board-of-directors/\n\n"
            "Or contact BRS:\n"
            "Phone: +254 11 112 7000\n"
            "Email: eo@brs.go.ke\n"
            "Website: https://brs.go.ke/"
        )

    except Exception as e:
        logger.error(f"Error fetching BRS leadership info: {str(e)}")
        return (
            "BRS Kenya Leadership Information:\n"
            "=" * 60 + "\n\n"
            "I encountered an error accessing the BRS website.\n\n"
            "Please visit:\n"
            "- Senior Management: https://brs.go.ke/senior-management/\n"
            "- Board of Directors: https://brs.go.ke/board-of-directors/\n\n"
            "Phone: +254 11 112 7000\n"
            "Email: eo@brs.go.ke"
        )


@tool
async def get_brs_contact_info() -> str:
    """
    Get current contact information for the Business Registration Service (BRS) of Kenya.

    Use this tool when users ask about:
    - BRS phone numbers
    - BRS email addresses
    - BRS office locations
    - BRS physical addresses
    - How to contact BRS

    Returns:
        Current BRS contact information from the official website.
    """
    try:
        import httpx
        from bs4 import BeautifulSoup
    except ImportError:
        return (
            "Contact information retrieval is not available. Required libraries not installed. "
            "Please install: pip install httpx beautifulsoup4 lxml"
        )

    try:
        logger.info("Fetching BRS contact information")

        contact_urls = [
            "https://brs.go.ke/contact/",
            "https://brs.go.ke/contact-us/",
        ]

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            for contact_url in contact_urls:
                try:
                    response = await client.get(contact_url)

                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'lxml')

                        # Remove unnecessary elements
                        for element in soup(["script", "style", "nav", "footer"]):
                            element.decompose()

                        # Get text content
                        text = soup.get_text(separator='\n', strip=True)

                        # Look for contact information patterns
                        lines = text.split('\n')
                        contact_lines = []

                        keywords = [
                            'phone', 'email', 'address', 'location', 'contact',
                            'tel', 'fax', 'p.o.', 'box', 'nairobi', 'office',
                            'call', 'reach', '+254', '011', '020', 'hours',
                            'monday', 'friday', 'weekend',
                        ]

                        for i, line in enumerate(lines):
                            line_lower = line.lower()
                            if any(keyword in line_lower for keyword in keywords):
                                start = max(0, i - 2)
                                end = min(len(lines), i + 3)
                                contact_lines.extend(lines[start:end])

                        if contact_lines:
                            seen = set()
                            unique_lines = []
                            for line in contact_lines:
                                stripped = line.strip()
                                if stripped and stripped not in seen and len(stripped) > 3:
                                    seen.add(stripped)
                                    unique_lines.append(stripped)

                            result = "BRS Kenya Contact Information:\n"
                            result += "=" * 60 + "\n\n"
                            result += '\n'.join(unique_lines[:30])
                            result += "\n\n" + "=" * 60 + "\n"
                            result += f"Source: {contact_url}\n"
                            result += "Note: Please verify by visiting the official website."
                            return result

                except Exception as e:
                    logger.warning(f"Error fetching {contact_url}: {str(e)}")
                    continue

        # Fallback if scraping doesn't work - use known contact info
        return (
            "BRS Kenya Contact Information:\n"
            "=" * 60 + "\n\n"
            "Official Website: https://brs.go.ke/\n"
            "eCitizen Portal: https://brs.ecitizen.go.ke/\n\n"
            "Phone: +254 11 112 7000\n"
            "Email: eo@brs.go.ke\n"
            "Physical Address: BRS Towers, Ngong Road, Nairobi, Kenya\n"
            "Postal Address: P.O. Box 30035-00100, Nairobi, Kenya\n\n"
            "Office Hours: Monday-Friday, 8:00 AM - 5:00 PM\n"
            "Weekend/Holiday: Closed\n\n"
            "For the most current contact information, please visit:\n"
            "https://brs.go.ke/contact/\n\n"
            "You can also find contact details on the eCitizen platform."
        )

    except Exception as e:
        logger.error(f"Error fetching BRS contact info: {str(e)}")
        return (
            "BRS Kenya Contact Information:\n"
            "=" * 60 + "\n\n"
            "Official Website: https://brs.go.ke/\n"
            "eCitizen Portal: https://brs.ecitizen.go.ke/\n\n"
            "Phone: +254 11 112 7000\n"
            "Email: eo@brs.go.ke\n"
            "Physical Address: BRS Towers, Ngong Road, Nairobi, Kenya\n"
            "Postal Address: P.O. Box 30035-00100, Nairobi, Kenya\n\n"
            "Office Hours: Monday-Friday, 8:00 AM - 5:00 PM\n"
            "Weekend/Holiday: Closed\n\n"
            "I encountered an error accessing the contact page.\n"
            "Please visit https://brs.go.ke/contact/ directly for current contact information."
        )
