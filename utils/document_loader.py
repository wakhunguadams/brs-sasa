import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import re

from core.logger import setup_logger

logger = setup_logger(__name__)


class TextChunker:
    """
    Utility class for splitting text into chunks with overlap
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks
        """
        if not text or len(text) <= self.chunk_size:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to find a natural break point (paragraph, sentence, or word boundary)
            if end < len(text):
                # Look for paragraph break
                para_break = text.rfind('\n\n', start, end)
                if para_break > start + self.chunk_size // 2:
                    end = para_break + 2
                else:
                    # Look for sentence break
                    sentence_break = max(
                        text.rfind('. ', start, end),
                        text.rfind('? ', start, end),
                        text.rfind('! ', start, end)
                    )
                    if sentence_break > start + self.chunk_size // 2:
                        end = sentence_break + 2
                    else:
                        # Look for word boundary
                        word_break = text.rfind(' ', start, end)
                        if word_break > start + self.chunk_size // 2:
                            end = word_break + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap if end < len(text) else len(text)
        
        return chunks
    
    def split_by_sections(self, text: str, section_delimiter: str = r'\n-{3,}\n|\n={3,}\n') -> List[str]:
        """
        Split text by section headers (lines of dashes or equals signs).
        Each section is kept as a separate chunk for better context.
        Large sections are further chunked.
        """
        import re
        
        # Split by section delimiters (lines with 3+ dashes or equals)
        # Pattern matches header underlines like "----" or "===="
        lines = text.split('\n')
        sections = []
        current_section = []
        current_header = ""
        
        for i, line in enumerate(lines):
            # Check if this line is a section delimiter (underline)
            if re.match(r'^[-=]{3,}$', line.strip()):
                # The previous line was the header
                if current_section:
                    # Save the previous section
                    section_text = '\n'.join(current_section).strip()
                    if section_text:
                        sections.append({
                            'header': current_header,
                            'content': section_text
                        })
                    current_section = []
                # Get the header from the line before the delimiter
                if i > 0:
                    current_header = lines[i-1].strip()
                    # Remove the header from current_section as it will be re-added
                    if current_section and current_section[-1].strip() == current_header:
                        current_section.pop()
            else:
                current_section.append(line)
        
        # Don't forget the last section
        if current_section:
            section_text = '\n'.join(current_section).strip()
            if section_text:
                sections.append({
                    'header': current_header,
                    'content': section_text
                })
        
        # Process sections - keep small sections together, chunk large ones
        chunks = []
        max_section_size = self.chunk_size * 2  # Allow sections up to 2x chunk size
        
        for section in sections:
            header = section['header']
            content = section['content']
            
            if len(content) <= max_section_size:
                # Small section - keep as one chunk with header prefix
                if header:
                    chunk_text = f"[{header}]\n\n{content}"
                else:
                    chunk_text = content
                chunks.append(chunk_text)
            else:
                # Large section - chunk it but prefix each chunk with header
                sub_chunks = self.split_text(content)
                for i, sub_chunk in enumerate(sub_chunks):
                    if header:
                        chunk_text = f"[{header} - Part {i+1}/{len(sub_chunks)}]\n\n{sub_chunk}"
                    else:
                        chunk_text = sub_chunk
                    chunks.append(chunk_text)
        
        return chunks

class DocumentLoader(ABC):
    """
    Abstract base class for document loaders
    """
    
    @abstractmethod
    def load_document(self, file_path: str) -> str:
        """
        Load a document and return its content as text
        """
        pass
    
    @abstractmethod
    def load_documents(self, directory_path: str) -> List[Dict[str, Any]]:
        """
        Load all documents from a directory
        """
        pass

class PDFLoader(DocumentLoader):
    """
    Loader for PDF documents
    """
    
    def load_document(self, file_path: str) -> str:
        """
        Load a PDF document and return its content as text
        """
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            raise ImportError("Please install PyPDF2: pip install PyPDF2")
        except Exception as e:
            logger.error(f"Error loading PDF document {file_path}: {str(e)}")
            raise
    
    def load_documents(self, directory_path: str) -> List[Dict[str, Any]]:
        """
        Load all PDF documents from a directory
        """
        pdf_files = Path(directory_path).glob("*.pdf")
        documents = []
        
        for pdf_file in pdf_files:
            try:
                content = self.load_document(str(pdf_file))
                documents.append({
                    "source": str(pdf_file),
                    "content": content,
                    "metadata": {
                        "filename": pdf_file.name,
                        "size": pdf_file.stat().st_size,
                        "extension": pdf_file.suffix
                    }
                })
            except Exception as e:
                logger.error(f"Error loading document {pdf_file}: {str(e)}")
        
        return documents

class TextLoader(DocumentLoader):
    """
    Loader for text documents
    """
    
    def load_document(self, file_path: str) -> str:
        """
        Load a text document and return its content
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def load_documents(self, directory_path: str) -> List[Dict[str, Any]]:
        """
        Load all text documents from a directory
        """
        txt_files = Path(directory_path).glob("*.txt")
        documents = []
        
        for txt_file in txt_files:
            try:
                content = self.load_document(str(txt_file))
                documents.append({
                    "source": str(txt_file),
                    "content": content,
                    "metadata": {
                        "filename": txt_file.name,
                        "size": txt_file.stat().st_size,
                        "extension": txt_file.suffix
                    }
                })
            except Exception as e:
                logger.error(f"Error loading document {txt_file}: {str(e)}")
        
        return documents

class DocumentProcessor:
    """
    Processor to handle different types of documents using appropriate loaders
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.loaders = {
            '.pdf': PDFLoader(),
            '.txt': TextLoader(),
            '.doc': TextLoader(),  # Simplified for now
            '.docx': TextLoader()  # Simplified for now
        }
        self.chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    def load_document(self, file_path: str, chunk: bool = True) -> Dict[str, Any]:
        """
        Load a document using the appropriate loader based on file extension
        """
        ext = Path(file_path).suffix.lower()
        
        if ext not in self.loaders:
            raise ValueError(f"Unsupported file type: {ext}")
        
        loader = self.loaders[ext]
        content = loader.load_document(file_path)
        
        return {
            "source": file_path,
            "content": content,
            "metadata": {
                "filename": Path(file_path).name,
                "size": Path(file_path).stat().st_size,
                "extension": ext
            }
        }
    
    def load_and_chunk_document(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load a document and split it into chunks for better RAG performance.
        Uses section-based chunking for text files with clear section headers.
        """
        doc = self.load_document(file_path)
        ext = Path(file_path).suffix.lower()
        
        # Use section-based chunking for text files (knowledge docs)
        if ext == '.txt' and self._has_section_headers(doc["content"]):
            chunks = self.chunker.split_by_sections(doc["content"])
        else:
            chunks = self.chunker.split_text(doc["content"])
        
        chunked_docs = []
        for i, chunk in enumerate(chunks):
            chunked_docs.append({
                "source": doc["source"],
                "content": chunk,
                "metadata": {
                    **doc["metadata"],
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            })
        
        return chunked_docs
    
    def _has_section_headers(self, text: str) -> bool:
        """
        Check if text contains section headers (lines of dashes/equals signs).
        """
        import re
        # Look for lines that are just dashes or equals (section underlines)
        return bool(re.search(r'\n-{3,}\n|\n={3,}\n', text))
    
    def load_documents_from_directory(self, directory_path: str, chunk: bool = True) -> List[Dict[str, Any]]:
        """
        Load all supported documents from a directory
        """
        documents = []
        
        for ext, loader in self.loaders.items():
            try:
                docs = loader.load_documents(directory_path)
                if chunk:
                    # Chunk each document
                    for doc in docs:
                        doc_ext = Path(doc["source"]).suffix.lower()
                        
                        # Use section-based chunking for text files with headers
                        if doc_ext == '.txt' and self._has_section_headers(doc["content"]):
                            chunks = self.chunker.split_by_sections(doc["content"])
                        else:
                            chunks = self.chunker.split_text(doc["content"])
                        
                        for i, chunk_text in enumerate(chunks):
                            documents.append({
                                "source": doc["source"],
                                "content": chunk_text,
                                "metadata": {
                                    **doc.get("metadata", {}),
                                    "chunk_index": i,
                                    "total_chunks": len(chunks)
                                }
                            })
                else:
                    documents.extend(docs)
            except Exception as e:
                logger.error(f"Error loading {ext} documents from {directory_path}: {str(e)}")
        
        return documents