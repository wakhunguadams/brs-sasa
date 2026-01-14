import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import numpy as np

from core.config import settings
from core.logger import setup_logger

logger = setup_logger(__name__)

class VectorDB(ABC):
    """
    Abstract base class for vector databases
    """
    
    @abstractmethod
    async def initialize(self):
        """
        Initialize the vector database
        """
        pass
    
    @abstractmethod
    async def add_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None, ids: Optional[List[str]] = None):
        """
        Add texts to the vector database
        """
        pass
    
    @abstractmethod
    async def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform similarity search in the vector database
        """
        pass
    
    @abstractmethod
    async def delete(self, ids: List[str]):
        """
        Delete entries from the vector database
        """
        pass

class ChromaDB(VectorDB):
    """
    ChromaDB implementation for vector storage
    """
    
    def __init__(self, collection_name: str = "brs_documents"):
        self.collection_name = collection_name
        self.client = None
        self.collection = None
    
    async def initialize(self):
        """
        Initialize the ChromaDB client and collection
        """
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Initialize client with persistence
            self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine distance
            )
            
            logger.info(f"ChromaDB initialized with collection: {self.collection_name}")
        except ImportError:
            raise ImportError("Please install chromadb: pip install chromadb")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {str(e)}")
            raise
    
    async def add_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None, ids: Optional[List[str]] = None):
        """
        Add texts to the ChromaDB collection
        """
        if not self.collection:
            await self.initialize()
        
        try:
            # Generate IDs if not provided
            if not ids:
                import uuid
                ids = [str(uuid.uuid4()) for _ in texts]
            
            # Add documents to collection
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(texts)} documents to ChromaDB")
            return ids
        except Exception as e:
            logger.error(f"Error adding texts to ChromaDB: {str(e)}")
            raise
    
    async def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform similarity search in ChromaDB
        """
        if not self.collection:
            await self.initialize()
        
        try:
            # Perform query
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'content': results['documents'][0][i],
                    'source': results['metadatas'][0][i]['source'] if results['metadatas'][0][i] else 'Unknown',
                    'distance': results['distances'][0][i] if results['distances'][0] else 0.0,
                    'id': results['ids'][0][i] if results['ids'][0] else None
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error performing similarity search in ChromaDB: {str(e)}")
            raise
    
    async def delete(self, ids: List[str]):
        """
        Delete entries from ChromaDB
        """
        if not self.collection:
            await self.initialize()
        
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from ChromaDB")
        except Exception as e:
            logger.error(f"Error deleting from ChromaDB: {str(e)}")
            raise

class VectorDBManager:
    """
    Manager class to handle vector database operations
    """
    
    def __init__(self, db_type: str = "chroma"):
        self.db_type = db_type
        self.db: Optional[VectorDB] = None
    
    async def initialize_db(self):
        """
        Initialize the appropriate vector database based on configuration
        """
        if self.db_type.lower() == "chroma":
            self.db = ChromaDB()
        else:
            raise ValueError(f"Unsupported vector database type: {self.db_type}")
        
        await self.db.initialize()
        return self.db
    
    async def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add processed documents to the vector database
        """
        if not self.db:
            await self.initialize_db()
        
        texts = [doc['content'] for doc in documents]
        metadatas = [{'source': doc['source'], **doc.get('metadata', {})} for doc in documents]
        
        return await self.db.add_texts(texts, metadatas)
    
    async def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant documents in the vector database
        """
        if not self.db:
            await self.initialize_db()
        
        return await self.db.similarity_search(query, k)