import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from utils.document_loader import DocumentProcessor
from utils.vector_db import VectorDBManager
from core.config import settings
from core.logger import setup_logger

logger = setup_logger(__name__)

class KnowledgeBaseManager:
    """
    Manager class for the knowledge base that handles document ingestion,
    storage in vector database, and retrieval for RAG operations
    """
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.vector_db_manager = VectorDBManager(db_type=settings.VECTOR_DB_TYPE)
        self.initialized = False
    
    async def initialize(self):
        """
        Initialize the knowledge base components
        """
        if not self.initialized:
            await self.vector_db_manager.initialize_db()
            self.initialized = True
            logger.info("Knowledge base initialized successfully")
    
    async def ingest_documents_from_directory(self, directory_path: str):
        """
        Ingest all documents from a directory into the knowledge base
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Load documents from directory
            logger.info(f"Loading documents from {directory_path}")
            documents = self.document_processor.load_documents_from_directory(directory_path)
            
            if not documents:
                logger.warning(f"No documents found in {directory_path}")
                return []
            
            # Add documents to vector database
            logger.info(f"Adding {len(documents)} documents to vector database")
            doc_ids = await self.vector_db_manager.add_documents(documents)
            
            logger.info(f"Successfully ingested {len(documents)} documents into knowledge base")
            return doc_ids
        except Exception as e:
            logger.error(f"Error ingesting documents from {directory_path}: {str(e)}")
            raise
    
    async def ingest_single_document(self, file_path: str):
        """
        Ingest a single document into the knowledge base
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Load the document
            logger.info(f"Loading document: {file_path}")
            document = self.document_processor.load_document(file_path)
            
            # Add to vector database
            logger.info(f"Adding document to vector database: {file_path}")
            doc_ids = await self.vector_db_manager.add_documents([document])
            
            logger.info(f"Successfully ingested document: {file_path}")
            return doc_ids[0] if doc_ids else None
        except Exception as e:
            logger.error(f"Error ingesting document {file_path}: {str(e)}")
            raise
    
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the knowledge base for relevant information
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            results = await self.vector_db_manager.search(query, top_k)
            logger.debug(f"Found {len(results)} results for query: {query[:50]}...")
            return results
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            raise
    
    async def get_document_count(self) -> int:
        """
        Get the total count of documents in the knowledge base
        This is a simplified implementation - in a real system, 
        this would query the vector database for actual count
        """
        # For now, return a placeholder implementation
        # In a real system, this would connect to the vector DB to get actual count
        return 0  # Placeholder - would need to implement actual count from vector DB

# Global knowledge base instance
knowledge_base = KnowledgeBaseManager()