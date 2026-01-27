"""Centralized tools export for BRS-SASA agents"""
from tools.knowledge_base_tool import search_brs_knowledge

# All available tools for agent binding
BRS_TOOLS = [search_brs_knowledge]

__all__ = ['BRS_TOOLS', 'search_brs_knowledge']
