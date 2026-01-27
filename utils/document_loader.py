"""
Document Loader - Load and chunk documents for RAG
Supports: PDF, TXT with section-aware chunking
"""
from typing import List, Dict, Any
import os
from pathlib import Path
import re
from core.logger import setup_logger

logger = setup_logger(__name__)


class TextChunker:
    """Intelligent text chunking with section awareness"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str, source: str) -> List[Dict[str, Any]]:
        """
        Chunk text with overlap, preserving natural boundaries
        
        Args:
            text: Text to chunk
            source: Source filename
        
        Returns:
            List of chunk dictionaries with content and metadata
        """
        chunks = []
        
        # Try section-aware chunking first
        sections = self._split_by_sections(text)
        
        if len(sections) > 1:
            # Document has clear sections
            for section_title, section_content in sections:
                section_chunks = self._chunk_section(section_content, section_title, source)
                chunks.extend(section_chunks)
        else:
            # No clear sections, use simple chunking
            chunks = self._simple_chunk(text, source)
        
        return chunks
    
    def _split_by_sections(self, text: str) -> List[tuple]:
        """
        Split text by section headers
        Returns list of (section_title, section_content) tuples
        """
        # Pattern for section headers (all caps, numbers, or specific keywords)
        section_pattern = r'^([A-Z][A-Z\s]{3,}|PART \d+|CHAPTER \d+|SECTION \d+|SCHEDULE \d+|\d+\.\s+[A-Z][A-Z\s]+)$'
        
        lines = text.split('\n')
        sections = []
        current_section = "INTRODUCTION"
        current_content = []
        
        for line in lines:
            line_stripped = line.strip()
            if re.match(section_pattern, line_stripped) and len(line_stripped) > 5:
                # Save previous section
                if current_content:
                    sections.append((current_section, '\n'.join(current_content)))
                # Start new section
                current_section = line_stripped
                current_content = []
            else:
                current_content.append(line)
        
        # Add last section
        if current_content:
            sections.append((current_section, '\n'.join(current_content)))
        
        return sections if len(sections) > 1 else [("DOCUMENT", text)]
    
    def _chunk_section(self, content: str, section_title: str, source: str) -> List[Dict[str, Any]]:
        """Chunk a section, keeping section title with each chunk"""
        chunks = []
        
        # If section is small enough, keep it whole
        if len(content) <= self.chunk_size:
            chunks.append({
                'content': f"[{section_title}]\n{content}",
                'metadata': {
                    'source': source,
                    'section': section_title,
                    'chunk_id': 0
                }
            })
            return chunks
        
        # Otherwise, chunk it
        start = 0
        chunk_id = 0
        
        while start < len(content):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(content):
                # Look for sentence end
                sentence_end = content.rfind('. ', start, end)
                if sentence_end > start + self.chunk_size // 2:
                    end = sentence_end + 1
            
            chunk_text = content[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    'content': f"[{section_title}]\n{chunk_text}",
                    'metadata': {
                        'source': source,
                        'section': section_title,
                        'chunk_id': chunk_id
                    }
                })
            
            start = end - self.chunk_overlap
            chunk_id += 1
        
        return chunks
    
    def _simple_chunk(self, text: str, source: str) -> List[Dict[str, Any]]:
        """Simple overlapping chunks without section awareness"""
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at paragraph or sentence
            if end < len(text):
                para_break = text.rfind('\n\n', start, end)
                if para_break > start + self.chunk_size // 2:
                    end = para_break
                else:
                    sentence_end = text.rfind('. ', start, end)
                    if sentence_end > start + self.chunk_size // 2:
                        end = sentence_end + 1
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    'content': chunk_text,
                    'metadata': {
                        'source': source,
                        'chunk_id': chunk_id
                    }
                })
            
            start = end - self.chunk_overlap
            chunk_id += 1
        
        return chunks


def load_text_file(file_path: str) -> str:
    """Load a text file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading text file {file_path}: {str(e)}")
        return ""


def load_pdf_file(file_path: str) -> str:
    """Load a PDF file (basic implementation)"""
    try:
        # Try PyPDF2 first
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            logger.warning("PyPDF2 not installed, trying pdfplumber")
            
        # Try pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            logger.error("No PDF library available. Install PyPDF2 or pdfplumber")
            return ""
            
    except Exception as e:
        logger.error(f"Error loading PDF file {file_path}: {str(e)}")
        return ""


def load_document(file_path: str) -> Dict[str, Any]:
    """
    Load a document and return its content
    
    Args:
        file_path: Path to document
    
    Returns:
        Dictionary with content and metadata
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return {'content': '', 'source': str(file_path.name), 'error': 'File not found'}
    
    ext = file_path.suffix.lower()
    
    if ext == '.txt':
        content = load_text_file(str(file_path))
    elif ext == '.pdf':
        content = load_pdf_file(str(file_path))
    else:
        logger.warning(f"Unsupported file type: {ext}")
        content = ""
    
    return {
        'content': content,
        'source': file_path.name,
        'path': str(file_path),
        'type': ext[1:]  # Remove the dot
    }


def load_documents_from_directory(directory: str, extensions: List[str] = None) -> List[Dict[str, Any]]:
    """
    Load all documents from a directory
    
    Args:
        directory: Directory path
        extensions: List of extensions to load (e.g., ['.txt', '.pdf'])
    
    Returns:
        List of document dictionaries
    """
    if extensions is None:
        extensions = ['.txt', '.pdf']
    
    directory = Path(directory)
    
    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return []
    
    documents = []
    
    for ext in extensions:
        for file_path in directory.rglob(f'*{ext}'):
            logger.info(f"Loading: {file_path.name}")
            doc = load_document(str(file_path))
            if doc['content']:
                documents.append(doc)
    
    logger.info(f"Loaded {len(documents)} documents from {directory}")
    return documents


def chunk_documents(documents: List[Dict[str, Any]], chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Dict[str, Any]]:
    """
    Chunk a list of documents
    
    Args:
        documents: List of document dictionaries
        chunk_size: Size of each chunk
        chunk_overlap: Overlap between chunks
    
    Returns:
        List of chunk dictionaries
    """
    chunker = TextChunker(chunk_size, chunk_overlap)
    all_chunks = []
    
    for doc in documents:
        content = doc.get('content', '')
        source = doc.get('source', 'Unknown')
        
        if content:
            chunks = chunker.chunk_text(content, source)
            all_chunks.extend(chunks)
    
    logger.info(f"Created {len(all_chunks)} chunks from {len(documents)} documents")
    return all_chunks
