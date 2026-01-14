from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging

from llm_factory.factory import BaseLLM
from core.knowledge_base import knowledge_base
from core.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class RAGResponse:
    response_text: str
    sources: Optional[List[str]] = None
    confidence: Optional[float] = None
    retrieved_chunks: Optional[List[Dict[str, Any]]] = None

class RAGAgent:
    """
    Agent responsible for Retrieval-Augmented Generation (RAG)
    Retrieves relevant documents and incorporates them into LLM responses
    """

    def __init__(self, llm: BaseLLM):
        self.llm = llm
        self.knowledge_base = knowledge_base
        self.logger = logger

        # Initialize the knowledge base
        import asyncio
        try:
            # Initialize knowledge base asynchronously
            if not knowledge_base.initialized:
                asyncio.run(knowledge_base.initialize())
        except RuntimeError:
            # If running in an event loop, use create_task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, knowledge_base.initialize())
                future.result()

    async def query_knowledge_base(
        self,
        query: str,
        top_k: int = 5,
        context: Optional[Dict[str, Any]] = None
    ) -> RAGResponse:
        """
        Query the knowledge base and return a response with retrieved information
        """
        try:
            # Retrieve relevant documents/chunks from knowledge base
            retrieved_chunks = await self.knowledge_base.search(query, top_k)

            # Build context from retrieved chunks
            context_str = self._build_context_from_chunks(retrieved_chunks)

            # Build the final prompt with retrieved context
            prompt = self._build_rag_prompt(query, context_str)

            # Generate response from LLM
            response_text = await self.llm.generate_response(prompt)

            # Extract sources from retrieved chunks
            sources = [chunk.get('source', 'Unknown') for chunk in retrieved_chunks]

            return RAGResponse(
                response_text=response_text,
                sources=sources,
                confidence=0.85,  # Placeholder confidence score
                retrieved_chunks=retrieved_chunks
            )
        except Exception as e:
            self.logger.error(f"Error querying knowledge base: {str(e)}")
            return RAGResponse(
                response_text="I'm sorry, I encountered an error while searching the knowledge base. Please try again.",
                sources=[],
                confidence=0.0,
                retrieved_chunks=[]
            )

    def _build_context_from_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Build context string from retrieved chunks
        """
        if not chunks:
            return "No relevant information found in the knowledge base."

        context_parts = []
        for chunk in chunks:
            content = chunk.get('content', '')
            source = chunk.get('source', 'Unknown')
            distance = chunk.get('distance', 'N/A')
            context_parts.append(f"Source: {source} | Relevance: {1-float(distance) if isinstance(distance, (int, float)) else 'N/A'}\nContent: {content}\n")

        return "\n".join(context_parts)

    def _build_rag_prompt(self, query: str, context: str) -> str:
        """
        Build a RAG-specific prompt that incorporates retrieved context
        """
        prompt = (
            "You are BRS-SASA, an AI assistant for the Business Registration Service (BRS) of Kenya. "
            "Use the following context to answer the user's question accurately. "
            "Always cite your sources when possible and be specific about fees, requirements, and processes.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            "Provide a comprehensive answer based on the context, citing sources where possible. "
            "If the context doesn't contain sufficient information to answer the question, "
            "acknowledge this limitation and suggest contacting BRS directly for specific advice. "
            "Answer:"
        )

        return prompt

    async def add_document(self, doc_path: str) -> Optional[str]:
        """
        Add a document to the knowledge base
        """
        try:
            doc_id = await self.knowledge_base.ingest_single_document(doc_path)
            self.logger.info(f"Document added to knowledge base: {doc_path}")
            return doc_id
        except Exception as e:
            self.logger.error(f"Error adding document to knowledge base: {str(e)}")
            return None

    async def add_documents_from_directory(self, directory_path: str) -> List[str]:
        """
        Add all documents from a directory to the knowledge base
        """
        try:
            doc_ids = await self.knowledge_base.ingest_documents_from_directory(directory_path)
            self.logger.info(f"Documents added from directory: {directory_path}")
            return doc_ids
        except Exception as e:
            self.logger.error(f"Error adding documents from directory: {str(e)}")
            return []