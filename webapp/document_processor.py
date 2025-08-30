"""
Document Processing Module for PIKE-RAG Web App
Handles document upload, processing, and indexing
"""

import os
import io
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

# Document processing imports
from docx import Document as DocxDocument
import PyPDF2
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

class DocumentProcessor:
    def __init__(self, upload_dir: str, knowledge_base_dir: str):
        self.upload_dir = upload_dir
        self.knowledge_base_dir = knowledge_base_dir
        self.chroma_client = None
        self.embedding_model = None
        
        # Ensure directories exist
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(knowledge_base_dir, exist_ok=True)
        
        self.initialize_chroma()
        self.initialize_embeddings()
    
    def initialize_chroma(self):
        """Initialize ChromaDB client"""
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=os.path.join(self.knowledge_base_dir, "chroma_db"),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            print("✅ ChromaDB initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize ChromaDB: {e}")
    
    def initialize_embeddings(self):
        """Initialize sentence transformer model"""
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Embedding model initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize embedding model: {e}")
    
    def process_uploaded_file(self, file_storage, collection_name: str = "documents") -> Dict[str, Any]:
        """Process uploaded file and add to knowledge base"""
        try:
            # Save file to disk
            file_id = str(uuid.uuid4())
            filename = file_storage.filename
            file_path = os.path.join(self.upload_dir, f"{file_id}_{filename}")
            file_storage.save(file_path)
            
            # Extract text based on file type
            file_extension = filename.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                text_content = self._extract_pdf_text(file_path)
            elif file_extension in ['doc', 'docx']:
                text_content = self._extract_docx_text(file_path)
            elif file_extension == 'txt':
                text_content = self._extract_txt_text(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Split text into chunks
            chunks = self._split_text_into_chunks(text_content)
            
            # Add to knowledge base
            result = self._add_to_knowledge_base(
                chunks=chunks,
                collection_name=collection_name,
                metadata={
                    'filename': filename,
                    'file_id': file_id,
                    'upload_time': datetime.now().isoformat(),
                    'file_type': file_extension,
                    'file_size': os.path.getsize(file_path)
                }
            )
            
            return {
                'success': True,
                'file_id': file_id,
                'filename': filename,
                'chunks_count': len(chunks),
                'collection_name': collection_name,
                'message': f'Successfully processed {filename} into {len(chunks)} chunks'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to process file: {str(e)}'
            }
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
    
    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        doc = DocxDocument(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def _extract_txt_text(self, file_path: str) -> str:
        """Extract text from TXT file"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def _split_text_into_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            
            # Try to break at sentence boundaries
            if end < text_length:
                # Look for sentence endings near the chunk boundary
                for i in range(end, max(start + chunk_size - 200, start), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap if end < text_length else text_length
        
        return chunks
    
    def _add_to_knowledge_base(self, chunks: List[str], collection_name: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Add text chunks to ChromaDB knowledge base"""
        try:
            # Get or create collection
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"description": f"Knowledge base collection: {collection_name}"}
            )
            
            # Prepare documents for insertion
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                doc_id = f"{metadata['file_id']}_chunk_{i}"
                chunk_metadata = {
                    **metadata,
                    'chunk_index': i,
                    'chunk_id': doc_id,
                    'chunk_length': len(chunk)
                }
                
                documents.append(chunk)
                metadatas.append(chunk_metadata)
                ids.append(doc_id)
            
            # Add to collection
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            return {
                'success': True,
                'collection_name': collection_name,
                'chunks_added': len(chunks),
                'collection_count': collection.count()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_knowledge_base(self, query: str, collection_name: str = "documents", n_results: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge base for relevant documents"""
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                    'chunk_id': results['metadatas'][0][i].get('chunk_id', f'chunk_{i}')
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get_collections(self) -> List[Dict[str, Any]]:
        """Get all available collections"""
        try:
            collections = self.chroma_client.list_collections()
            collection_info = []
            
            for collection in collections:
                collection_obj = self.chroma_client.get_collection(collection.name)
                collection_info.append({
                    'name': collection.name,
                    'count': collection_obj.count(),
                    'metadata': collection.metadata
                })
            
            return collection_info
            
        except Exception as e:
            print(f"Error getting collections: {e}")
            return []
    
    def delete_collection(self, collection_name: str) -> Dict[str, Any]:
        """Delete a collection"""
        try:
            self.chroma_client.delete_collection(name=collection_name)
            return {
                'success': True,
                'message': f'Collection {collection_name} deleted successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_file_info(self, collection_name: str = "documents") -> List[Dict[str, Any]]:
        """Get information about uploaded files"""
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            
            # Get all documents with metadata
            results = collection.get(include=['metadatas'])
            
            # Group by file_id to get unique files
            files_info = {}
            for metadata in results['metadatas']:
                file_id = metadata.get('file_id')
                if file_id and file_id not in files_info:
                    files_info[file_id] = {
                        'file_id': file_id,
                        'filename': metadata.get('filename', 'Unknown'),
                        'upload_time': metadata.get('upload_time', ''),
                        'file_type': metadata.get('file_type', 'unknown'),
                        'file_size': metadata.get('file_size', 0),
                        'chunks_count': 0
                    }
                
                if file_id:
                    files_info[file_id]['chunks_count'] += 1
            
            return list(files_info.values())
            
        except Exception as e:
            print(f"Error getting file info: {e}")
            return []