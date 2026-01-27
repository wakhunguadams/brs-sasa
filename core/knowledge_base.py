"""
Knowledge Base - ChromaDB wrapper for vector storage and retrieval
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os
import uuid
from core.logger import setup_logger

logger = setup_logger(__name__)


class KnowledgeBase:
    """
    Knowledge base using ChromaDB for vector storage
    Singleton pattern for global access
    """
    
    def __init__(self, persist_dir: str = "./chroma_data", collection_name: str = "brs_documents"):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.initialized = False
        
        # Ensure persist directory exists
        os.makedirs(persist_dir, exist_ok=True)
    
    async def initialize(self):
        """Initialize ChromaDB client and collection"""
        if self.initialized:
            logger.info("Knowledge base already initialized")
            return
        
        try:
            # Create persistent client
            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            self.initialized = True
            
            # Log collection stats
            count = self.collection.count()
            logger.info(f"Knowledge base initialized: {count} documents in collection '{self.collection_name}'")
            
        except Exception as e:
            logger.error(f"Failed to initialize knowledge base: {str(e)}")
            raise
    
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the knowledge base
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of chunk dictionaries with content, source, and distance
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            chunks = []
            
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    chunk = {
                        'content': doc,
                        'source': results['metadatas'][0][i].get('source', 'Unknown'),
                        'distance': results['distances'][0][i] if results['distances'] else 0.0
                    }
                    
                    # Add section if available
                    if 'section' in results['metadatas'][0][i]:
                        chunk['section'] = results['metadatas'][0][i]['section']
                    
                    chunks.append(chunk)
            
            logger.debug(f"Search for '{query}' returned {len(chunks)} results")
            return chunks
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []
    
    async def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ):
        """
        Add documents to the knowledge base
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries
            ids: Optional list of document IDs (generated if not provided)
        """
        if not self.initialized:
            await self.initialize()
        
        if not documents:
            logger.warning("No documents to add")
            return
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to knowledge base")
            
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise
    
    async def add_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Add pre-chunked documents to the knowledge base
        
        Args:
            chunks: List of chunk dictionaries with 'content' and 'metadata'
        """
        if not chunks:
            logger.warning("No chunks to add")
            return
        
        documents = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            content = chunk.get('content', '')
            metadata = chunk.get('metadata', {})
            
            if content:
                documents.append(content)
                metadatas.append(metadata)
                ids.append(str(uuid.uuid4()))
        
        await self.add_documents(documents, metadatas, ids)
    
    async def clear(self):
        """Clear all documents from the knowledge base"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Delete and recreate collection
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Knowledge base cleared")
            
        except Exception as e:
            logger.error(f"Error clearing knowledge base: {str(e)}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        if not self.initialized:
            return {"initialized": False}
        
        try:
            count = self.collection.count()
            return {
                "initialized": True,
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_dir": self.persist_dir
            }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {"initialized": True, "error": str(e)}

    def is_empty(self) -> bool:
        """Check if the knowledge base is empty"""
        if not self.initialized:
            # We can't know for sure without initializing, but we'll return True to trigger initialization
            return True
        return self.collection.count() == 0
    
    async def ingest_single_document(self, file_path: str) -> Optional[str]:
        """
        Ingest a single document file
        
        Args:
            file_path: Path to document
        
        Returns:
            Document ID or None if failed
        """
        from utils.document_loader import load_document, chunk_documents
        
        try:
            # Load document
            doc = load_document(file_path)
            
            if not doc.get('content'):
                logger.error(f"No content loaded from {file_path}")
                return None
            
            # Chunk document
            chunks = chunk_documents([doc])
            
            # Add to knowledge base
            await self.add_chunks(chunks)
            
            logger.info(f"Ingested document: {file_path} ({len(chunks)} chunks)")
            return str(uuid.uuid4())
            
        except Exception as e:
            logger.error(f"Error ingesting document {file_path}: {str(e)}")
            return None
    
    async def ingest_documents_from_directory(self, directory: str, extensions: List[str] = None) -> List[str]:
        """
        Ingest all documents from a directory
        
        Args:
            directory: Directory path
            extensions: File extensions to process
        
        Returns:
            List of document IDs
        """
        from utils.document_loader import load_documents_from_directory, chunk_documents
        
        try:
            # Load documents
            documents = load_documents_from_directory(directory, extensions)
            
            if not documents:
                logger.warning(f"No documents found in {directory}")
                return []
            
            # Chunk documents
            chunks = chunk_documents(documents)
            
            # Add to knowledge base
            await self.add_chunks(chunks)
            
            logger.info(f"Ingested {len(documents)} documents from {directory} ({len(chunks)} chunks)")
            return [str(uuid.uuid4()) for _ in documents]
            
        except Exception as e:
            logger.error(f"Error ingesting documents from {directory}: {str(e)}")
            return []


# Global singleton instance
knowledge_base = KnowledgeBase()
