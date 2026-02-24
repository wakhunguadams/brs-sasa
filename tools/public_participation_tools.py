"""Public Participation Tools Registry"""
from tools.feedback_tool import collect_legislation_feedback, search_legislation_knowledge
from tools.web_search_tool import search_web_duckduckgo, search_brs_news

# Tools available to the public participation agent
PUBLIC_PARTICIPATION_TOOLS = [
    search_legislation_knowledge,
    search_web_duckduckgo,
    search_brs_news,
    collect_legislation_feedback
]

__all__ = [
    'PUBLIC_PARTICIPATION_TOOLS',
    'search_legislation_knowledge',
    'search_web_duckduckgo',
    'search_brs_news',
    'collect_legislation_feedback'
]
