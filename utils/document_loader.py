import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

from core.logger import setup_logger

logger = setup_logger(__name__)

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
    
    def __init__(self):
        self.loaders = {
            '.pdf': PDFLoader(),
            '.txt': TextLoader(),
            '.doc': TextLoader(),  # Simplified for now
            '.docx': TextLoader()  # Simplified for now
        }
    
    def load_document(self, file_path: str) -> Dict[str, Any]:
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
    
    def load_documents_from_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        """
        Load all supported documents from a directory
        """
        documents = []
        
        for ext, loader in self.loaders.items():
            try:
                docs = loader.load_documents(directory_path)
                documents.extend(docs)
            except Exception as e:
                logger.error(f"Error loading {ext} documents from {directory_path}: {str(e)}")
        
        return documents