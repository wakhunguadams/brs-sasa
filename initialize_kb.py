#!/usr/bin/env python3
"""
Initialization script for BRS-SASA
This script sets up the knowledge base with the provided documents
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.rag_agent import RAGAgent
from llm_factory.factory import LLMFactory
from core.knowledge_base import knowledge_base

async def initialize_knowledge_base():
    """
    Initialize the knowledge base with documents from the acts and regulations directories
    """
    print("Initializing BRS-SASA Knowledge Base...")
    
    # Initialize LLM
    llm_factory = LLMFactory()
    llm = llm_factory.get_llm("gemini")  # Will use default or configured provider
    
    # Initialize RAG agent which will initialize the knowledge base
    rag_agent = RAGAgent(llm=llm)
    
    # Define document directories
    acts_dir = project_root / "acts"
    regulations_dir = project_root / "regulations"
    faqs_file = project_root / "FAQs.pdf"
    
    # Add documents from acts directory
    if acts_dir.exists():
        print(f"Ingesting documents from {acts_dir}...")
        doc_ids = await rag_agent.add_documents_from_directory(str(acts_dir))
        print(f"Added {len(doc_ids)} documents from acts directory")
    else:
        print(f"Acts directory not found: {acts_dir}")
    
    # Add documents from regulations directory
    if regulations_dir.exists():
        print(f"Ingesting documents from {regulations_dir}...")
        doc_ids = await rag_agent.add_documents_from_directory(str(regulations_dir))
        print(f"Added {len(doc_ids)} documents from regulations directory")
    else:
        print(f"Regulations directory not found: {regulations_dir}")
    
    # Add FAQs document if it exists
    if faqs_file.exists():
        print(f"Ingesting FAQs document: {faqs_file}...")
        doc_id = await rag_agent.add_document(str(faqs_file))
        if doc_id:
            print(f"Added FAQs document with ID: {doc_id}")
        else:
            print("Failed to add FAQs document")
    else:
        print(f"FAQs document not found: {faqs_file}")
    
    print("Knowledge base initialization completed!")

if __name__ == "__main__":
    asyncio.run(initialize_knowledge_base())