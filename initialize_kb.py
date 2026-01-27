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

from core.knowledge_base import knowledge_base
from core.logger import setup_logger

logger = setup_logger(__name__)

async def initialize_knowledge_base():
    """
    Initialize the knowledge base with documents from the acts and regulations directories
    """
    print("=" * 60)
    print("BRS-SASA Knowledge Base Initialization")
    print("=" * 60)
    
    # Initialize the knowledge base
    print("\n[1/4] Initializing knowledge base...")
    await knowledge_base.initialize()
    print("      Knowledge base initialized successfully!")
    
    # Define document directories
    acts_dir = project_root / "acts"
    regulations_dir = project_root / "regulations"
    knowledge_docs_dir = project_root / "knowledge_docs"
    faqs_file = project_root / "FAQs.pdf"
    brs_spec_file = project_root / "BRS-sasa.txt"
    
    total_docs = 0
    
    # Add documents from acts directory
    print("\n[2/4] Processing acts directory...")
    if acts_dir.exists():
        try:
            doc_ids = await knowledge_base.ingest_documents_from_directory(str(acts_dir))
            print(f"      Added {len(doc_ids)} document chunks from acts directory")
            total_docs += len(doc_ids)
        except Exception as e:
            print(f"      Error processing acts: {str(e)}")
    else:
        print(f"      Acts directory not found: {acts_dir}")
    
    # Add documents from regulations directory
    print("\n[3/4] Processing regulations directory...")
    if regulations_dir.exists():
        try:
            doc_ids = await knowledge_base.ingest_documents_from_directory(str(regulations_dir))
            print(f"      Added {len(doc_ids)} document chunks from regulations directory")
            total_docs += len(doc_ids)
        except Exception as e:
            print(f"      Error processing regulations: {str(e)}")
    else:
        print(f"      Regulations directory not found: {regulations_dir}")
    
    # Add extended knowledge documents
    print("\n[4/5] Processing knowledge_docs directory...")
    if knowledge_docs_dir.exists():
        try:
            doc_ids = await knowledge_base.ingest_documents_from_directory(str(knowledge_docs_dir))
            print(f"      Added {len(doc_ids)} document chunks from knowledge_docs directory")
            total_docs += len(doc_ids)
        except Exception as e:
            print(f"      Error processing knowledge_docs: {str(e)}")
    else:
        print(f"      knowledge_docs directory not found: {knowledge_docs_dir}")
    
    # Add FAQs and other documents
    print("\n[5/5] Processing additional documents...")
    
    # Add FAQs document if it exists
    if faqs_file.exists():
        try:
            doc_id = await knowledge_base.ingest_single_document(str(faqs_file))
            if doc_id:
                print(f"      Added FAQs document")
                total_docs += 1
        except Exception as e:
            print(f"      Error processing FAQs: {str(e)}")
    
    # Add BRS specification document if it exists
    if brs_spec_file.exists():
        try:
            doc_id = await knowledge_base.ingest_single_document(str(brs_spec_file))
            if doc_id:
                print(f"      Added BRS specification document")
                total_docs += 1
        except Exception as e:
            print(f"      Error processing BRS spec: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"Knowledge base initialization completed!")
    print(f"Total document chunks added: {total_docs}")
    print("=" * 60)
    
    return total_docs

async def test_search():
    """
    Test the knowledge base with a sample query
    """
    print("\n" + "-" * 60)
    print("Testing knowledge base search...")
    print("-" * 60)
    
    test_query = "How do I register a company in Kenya?"
    print(f"\nTest query: '{test_query}'")
    
    results = await knowledge_base.search(test_query, top_k=3)
    
    if results:
        print(f"\nFound {len(results)} relevant documents:")
        for i, result in enumerate(results, 1):
            source = result.get('source', 'Unknown')
            content_preview = result.get('content', '')[:200] + "..."
            print(f"\n{i}. Source: {source}")
            print(f"   Preview: {content_preview}")
    else:
        print("\nNo results found. Knowledge base may be empty.")
    
    return len(results)

if __name__ == "__main__":
    print("\nStarting BRS-SASA Knowledge Base Setup...\n")
    
    # Run initialization
    total = asyncio.run(initialize_knowledge_base())
    
    if total > 0:
        # Run test search
        asyncio.run(test_search())
    
    print("\nSetup complete! You can now run the server with: python start_server.py")