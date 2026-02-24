"""Centralized tools export for BRS-SASA agents"""
from tools.knowledge_base_tool import search_brs_knowledge
from tools.web_search_tool import search_web_duckduckgo, search_brs_news
from tools.brs_website_scraper import scrape_brs_website, get_brs_contact_info, get_brs_leadership
from tools.brs_status_checker import check_business_registration_status, get_registration_number_format
from tools.statistics_tool import (
    get_registration_statistics,
    get_sector_statistics,
    get_regional_statistics,
    get_trend_analysis,
    get_process_metrics
)

# All available tools for agent binding
BRS_TOOLS = [
    search_brs_knowledge,
    search_web_duckduckgo,
    search_brs_news,
    scrape_brs_website,
    get_brs_contact_info,
    get_brs_leadership,
    check_business_registration_status,
    get_registration_number_format,
    get_registration_statistics,
    get_sector_statistics,
    get_regional_statistics,
    get_trend_analysis,
    get_process_metrics
]

__all__ = [
    'BRS_TOOLS',
    'search_brs_knowledge',
    'search_web_duckduckgo',
    'search_brs_news',
    'scrape_brs_website',
    'get_brs_contact_info',
    'get_brs_leadership',
    'check_business_registration_status',
    'get_registration_number_format',
    'get_registration_statistics',
    'get_sector_statistics',
    'get_regional_statistics',
    'get_trend_analysis',
    'get_process_metrics'
]
