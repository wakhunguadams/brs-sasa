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
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure knowledge base is initialized before use"""
        if not self._initialized and not self.knowledge_base.initialized:
            await self.knowledge_base.initialize()
            self._initialized = True

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
            # Ensure knowledge base is initialized
            await self._ensure_initialized()
            
            # Expand query for better retrieval (especially for fee-related queries)
            expanded_queries = self._expand_query(query)
            
            # Retrieve relevant documents/chunks from knowledge base
            all_chunks = []
            seen_content = set()
            
            for q in expanded_queries:
                chunks = await self.knowledge_base.search(q, top_k)
                for chunk in chunks:
                    # Deduplicate by content hash
                    content_hash = hash(chunk.get('content', '')[:100])
                    if content_hash not in seen_content:
                        seen_content.add(content_hash)
                        all_chunks.append(chunk)
            
            # Limit to top_k * 2 to get diverse results
            retrieved_chunks = all_chunks[:top_k * 2]

            # Build context from retrieved chunks
            context_str = self._build_context_from_chunks(retrieved_chunks)

            # Build the final prompt with retrieved context
            prompt = self._build_rag_prompt(query, context_str)

            # Generate response from LLM
            response_text = await self.llm.generate_response(prompt)

            # Extract sources from retrieved chunks (clean up paths to show only filenames)
            sources = []
            for chunk in retrieved_chunks:
                source = chunk.get('source', 'Unknown')
                # Extract just the filename from the full path
                if '/' in source:
                    source = source.split('/')[-1]
                if source not in sources:  # Avoid duplicates
                    sources.append(source)

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
    
    def _expand_query(self, query: str) -> List[str]:
        """
        Expand query with synonyms and related terms for better retrieval.
        Especially important for fee/cost queries.
        """
        queries = [query]
        query_lower = query.lower()
        
        # Fee-related query expansion
        fee_keywords = ['fee', 'fees', 'cost', 'costs', 'price', 'prices', 'charge', 'charges', 
                       'how much', 'payment', 'pay', 'amount']
        
        if any(kw in query_lower for kw in fee_keywords):
            # Add query with KES (Kenyan Shillings) for better matching
            queries.append(f"{query} KES amount")
            
            # Add specific fee search based on entity type mentioned
            if 'company' in query_lower or 'private' in query_lower:
                queries.append("Company Registration Fees KES 10,650 private company")
            if 'business name' in query_lower or 'sole' in query_lower:
                queries.append("Business Name Registration Fees KES 950")
            if 'llp' in query_lower or 'limited liability partnership' in query_lower:
                queries.append("LLP Registration Fees KES 10,650")
                queries.append("LLP Agreement filing KES 2,000")
                queries.append("LIMITED LIABILITY PARTNERSHIP requirements partners")
            if 'foreign' in query_lower:
                queries.append("Foreign Company Registration Fees KES 25,000")
                queries.append("FOREIGN COMPANY REGISTRATION branch subsidiary")
                queries.append("foreign company local representative Kenya")
                queries.append("Registration KES 25,000 foreign")
        
        # Registration process query expansion
        if 'register' in query_lower or 'registration' in query_lower:
            if 'company' in query_lower:
                queries.append("company registration process requirements steps")
            if 'business name' in query_lower:
                queries.append("business name registration process requirements")
            if 'llp' in query_lower or 'limited liability partnership' in query_lower:
                queries.append("LLP Agreement filing KES 2,000")
                queries.append("LIMITED LIABILITY PARTNERSHIP requirements partners")
        
        # LLP-specific expansion (even without fee keywords)
        if 'llp' in query_lower or 'limited liability partnership' in query_lower:
            queries.append("LIMITED LIABILITY PARTNERSHIP LLP partners Kenya")
            queries.append("LLP Agreement filing requirements")
        
        # Contact info expansion
        contact_keywords = ['contact', 'phone', 'email', 'address', 'reach', 'call']
        if any(kw in query_lower for kw in contact_keywords):
            queries.append("BRS contact phone email address operating hours")
        
        # Timeline/duration expansion
        time_keywords = ['how long', 'time', 'duration', 'days', 'processing']
        if any(kw in query_lower for kw in time_keywords):
            queries.append("processing timeline 24-48 hours registration")
        
        return queries

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
            # Clean up source path to show only filename
            if '/' in source:
                source = source.split('/')[-1]
            distance = chunk.get('distance', 'N/A')
            context_parts.append(f"Source: {source}\nContent: {content}\n")

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