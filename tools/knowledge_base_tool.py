from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from core.knowledge_base import knowledge_base
import logging

logger = logging.getLogger(__name__)

@tool
async def search_brs_knowledge(query: str, top_k: int = 5) -> str:
    """
    Search the Business Registration Service (BRS) knowledge base for information 
    about business registration processes, fees, requirements, and laws in Kenya.
    
    Args:
        query: The search query (e.g., "What are the fees for a private company?")
        top_k: Number of relevant results to return (default: 5)
        
    Returns:
        A string containing the retrieved information with source citations.
    """
    try:
        if not knowledge_base.initialized:
            await knowledge_base.initialize()
            
        chunks = await knowledge_base.search(query, top_k=top_k)
        
        if not chunks:
            return "No relevant information found in the BRS knowledge base."
            
        results = []
        for chunk in chunks:
            content = chunk.get('content', '')
            source = chunk.get('source', 'Unknown')
            if '/' in source:
                source = source.split('/')[-1]
            results.append(f"Source: {source}\nContent: {content}\n")
            
        return "\n---\n".join(results)
    except Exception as e:
        logger.error(f"Error in search_brs_knowledge tool: {str(e)}")
        return f"Error searching knowledge base: {str(e)}"
