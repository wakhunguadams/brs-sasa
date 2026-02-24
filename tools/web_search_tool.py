"""Web search tool using DuckDuckGo for real-time information"""
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
import logging
import asyncio
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

@tool
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((Exception,)),
    reraise=False
)
async def search_web_duckduckgo(query: str, max_results: int = 5) -> str:
    """
    Search the web using DuckDuckGo for current information about BRS, 
    government services, news, statistics, and other real-time data not in the knowledge base.
    
    Use this tool when users ask about:
    - Current BRS leadership, management, or staff
    - Recent financial reports or revenue
    - Latest news about BRS or business registration
    - Current statistics or performance metrics
    - Recent policy changes or announcements
    - Contact information or office locations
    - Any information that requires up-to-date data
    - Any media publications made by BRS
    - Comparing with other countries' laws
    
    Args:
        query: The search query (e.g., "BRS Kenya director 2024", "Uganda trust laws")
        max_results: Maximum number of search results to return (default: 5)
        
    Returns:
        A string containing search results with titles, snippets, and URLs.
    """
    try:
        # Import ddgs
        try:
            from ddgs import DDGS
        except ImportError:
            logger.error("ddgs library not installed")
            return (
                "Web search is not available. The ddgs library is not installed. "
                "Please install it with: pip install ddgs"
            )
        
        # Validate inputs
        if not query or not query.strip():
            return "Error: Search query cannot be empty."
        
        if max_results < 1 or max_results > 20:
            max_results = 5  # Default to safe value
        
        # Perform search with timeout
        logger.info(f"Searching web for: {query}")
        
        try:
            # Use DDGS for search with timeout
            results = []
            with DDGS() as ddgs:
                search_results = ddgs.text(
                    query,
                    max_results=max_results,
                    region='wt-wt',  # Worldwide
                    safesearch='moderate'
                )
                # Convert generator to list with timeout
                results = list(search_results)
        except Exception as search_error:
            logger.error(f"DuckDuckGo search failed: {str(search_error)}")
            return (
                f"Web search encountered an issue: {str(search_error)}\n\n"
                f"This could be due to:\n"
                f"- Network connectivity issues\n"
                f"- Rate limiting from the search service\n"
                f"- Temporary service unavailability\n\n"
                f"Please try again in a moment or rephrase your query."
            )
        
        if not results:
            logger.warning(f"No results found for query: {query}")
            return (
                f"No web results found for: '{query}'\n\n"
                f"Suggestions:\n"
                f"- Try rephrasing your query\n"
                f"- Use more specific keywords\n"
                f"- Check spelling of names or terms\n"
                f"- Try a broader search term"
            )
        
        # Format results
        formatted_results = []
        formatted_results.append(f"Web Search Results for: '{query}'")
        formatted_results.append(f"Search Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        formatted_results.append(f"Found {len(results)} result(s)")
        formatted_results.append("=" * 60)
        
        for idx, result in enumerate(results, 1):
            try:
                title = result.get('title', 'No title')
                snippet = result.get('body', 'No description')
                url = result.get('href', 'No URL')
                
                # Truncate very long snippets
                if len(snippet) > 300:
                    snippet = snippet[:297] + "..."
                
                formatted_results.append(f"\n{idx}. {title}")
                formatted_results.append(f"   URL: {url}")
                formatted_results.append(f"   {snippet}")
            except Exception as format_error:
                logger.warning(f"Error formatting result {idx}: {str(format_error)}")
                continue
        
        formatted_results.append("\n" + "=" * 60)
        formatted_results.append(
            "Note: These are web search results. Please verify information from official sources."
        )
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"Error in web search tool: {str(e)}", exc_info=True)
        return (
            f"Web search encountered an unexpected error.\n\n"
            f"Please try:\n"
            f"- Rephrasing your question\n"
            f"- Using more specific search terms\n"
            f"- Asking about a different aspect\n\n"
            f"If the issue persists, the search service may be temporarily unavailable."
        )


@tool
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((Exception,)),
    reraise=False
)
async def search_brs_news(query: str = "Business Registration Service Kenya", max_results: int = 5) -> str:
    """
    Search for recent news and updates about the Business Registration Service (BRS) of Kenya.
    
    Use this tool when users ask about:
    - Latest news about BRS
    - Recent announcements or press releases
    - New services or features
    - System updates or changes
    - Government initiatives related to business registration
    
    Args:
        query: The news search query (default: "Business Registration Service Kenya")
        max_results: Maximum number of news results (default: 5)
        
    Returns:
        A string containing recent news articles with titles, snippets, and URLs.
    """
    try:
        from ddgs import DDGS
    except ImportError:
        logger.error("ddgs library not installed")
        return (
            "News search is not available. The ddgs library is not installed. "
            "Please install it with: pip install ddgs"
        )
    
    try:
        # Validate inputs
        if not query or not query.strip():
            query = "Business Registration Service Kenya"
        
        if max_results < 1 or max_results > 20:
            max_results = 5
        
        logger.info(f"Searching news for: {query}")
        
        # Use DDGS for news search
        results = []
        try:
            with DDGS() as ddgs:
                news_results = ddgs.news(
                    query,
                    max_results=max_results,
                    region='wt-wt',
                    safesearch='moderate'
                )
                results = list(news_results)
        except Exception as search_error:
            logger.error(f"News search failed: {str(search_error)}")
            return (
                f"News search encountered an issue: {str(search_error)}\n\n"
                f"This could be due to:\n"
                f"- Network connectivity issues\n"
                f"- Rate limiting from the news service\n"
                f"- Temporary service unavailability\n\n"
                f"Please try again in a moment."
            )
        
        if not results:
            logger.warning(f"No news found for query: {query}")
            return (
                f"No recent news found for: '{query}'\n\n"
                f"This could mean:\n"
                f"- No recent news articles match your query\n"
                f"- Try a broader search term\n"
                f"- Check the official BRS website for announcements: https://brs.go.ke/"
            )
        
        # Format results
        formatted_results = []
        formatted_results.append(f"Recent News: '{query}'")
        formatted_results.append(f"Search Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        formatted_results.append(f"Found {len(results)} article(s)")
        formatted_results.append("=" * 60)
        
        for idx, result in enumerate(results, 1):
            try:
                title = result.get('title', 'No title')
                snippet = result.get('body', 'No description')
                url = result.get('url', 'No URL')
                date = result.get('date', 'Unknown date')
                source = result.get('source', 'Unknown source')
                
                # Truncate long snippets
                if len(snippet) > 300:
                    snippet = snippet[:297] + "..."
                
                formatted_results.append(f"\n{idx}. {title}")
                formatted_results.append(f"   Source: {source} | Date: {date}")
                formatted_results.append(f"   URL: {url}")
                formatted_results.append(f"   {snippet}")
            except Exception as format_error:
                logger.warning(f"Error formatting news result {idx}: {str(format_error)}")
                continue
        
        formatted_results.append("\n" + "=" * 60)
        formatted_results.append(
            "Note: These are news search results. Please verify from official sources."
        )
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"Error in news search tool: {str(e)}", exc_info=True)
        return (
            f"News search encountered an unexpected error.\n\n"
            f"Please try:\n"
            f"- Visiting https://brs.go.ke/ for official announcements\n"
            f"- Checking BRS social media channels\n"
            f"- Trying again in a moment\n\n"
            f"If the issue persists, the news service may be temporarily unavailable."
        )
