"""
RAG (Retrieval-Augmented Generation) Service for NCERT curriculum.
Handles document loading, chunking, embedding, and retrieval from vector database.
"""

import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.models.schemas import ClassLevel, Subject


class DocumentChunk:
    """Represents a chunk of a document with metadata."""
    
    def __init__(
        self,
        content: str,
        metadata: Dict[str, Any],
        chunk_id: Optional[str] = None
    ):
        self.content = content
        self.metadata = metadata
        self.chunk_id = chunk_id or str(uuid.uuid5(uuid.NAMESPACE_URL, content))
        self.embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "metadata": self.metadata,
            "embedding": self.embedding
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentChunk":
        chunk = cls(data["content"], data["metadata"], data["chunk_id"])
        chunk.embedding = data.get("embedding")
        return chunk


class VectorStore(ABC):
    """Abstract vector store interface."""
    
    @abstractmethod
    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        pass
    
    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[DocumentChunk, float]]:
        pass
    
    @abstractmethod
    async def delete_collection(self) -> None:
        pass


class QdrantVectorStore(VectorStore):
    """Qdrant vector store implementation."""
    
    def __init__(self, url: str, api_key: str = "", collection_name: str = "ncert_curriculum"):
        self.url = url
        self.api_key = api_key
        self.collection_name = collection_name
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
                self._client = QdrantClient(url=self.url, api_key=self.api_key if self.api_key else None)
            except ImportError:
                raise RuntimeError("qdrant-client not installed. Run: pip install qdrant-client")
        return self._client
    
    async def initialize(self, vector_size: int = 768) -> None:
        """Create collection if not exists."""
        client = self._get_client()
        from qdrant_client.models import Distance, VectorParams
        
        try:
            client.get_collection(self.collection_name)
        except Exception:
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
    
    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        client = self._get_client()
        from qdrant_client.models import PointStruct
        
        points = []
        for chunk in chunks:
            if chunk.embedding is None:
                raise ValueError(f"Chunk {chunk.chunk_id} has no embedding")
            points.append(PointStruct(
                id=chunk.chunk_id,
                vector=chunk.embedding,
                payload={"content": chunk.content, **chunk.metadata}
            ))
        
        await asyncio.to_thread(client.upsert, collection_name=self.collection_name, points=points)
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[DocumentChunk, float]]:
        client = self._get_client()
        from qdrant_client.models import FieldCondition, Filter, MatchValue
        
        query_filter = None
        if filter_metadata:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filter_metadata.items()
            ]
            query_filter = Filter(must=conditions)
        
        results = await asyncio.to_thread(
            client.search,
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True
        )
        
        chunks_with_scores = []
        for hit in results:
            chunk = DocumentChunk(
                content=hit.payload.pop("content", ""),
                metadata=hit.payload,
                chunk_id=str(hit.id)
            )
            chunks_with_scores.append((chunk, hit.score))
        
        return chunks_with_scores
    
    async def delete_collection(self) -> None:
        client = self._get_client()
        await asyncio.to_thread(client.delete_collection, collection_name=self.collection_name)


class RAGService:
    """Main RAG service for curriculum-aware retrieval."""
    
    def __init__(self):
        self.vector_store = QdrantVectorStore(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            collection_name=settings.collection_name
        )
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize vector store and embedding model."""
        if self._initialized:
            return
        
        await self.vector_store.initialize()
        self._initialized = True
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text using Google's embedding model."""
        """Generate an embedding with Google's embedding API.

        No random-vector fallback is used: retrieval over random vectors would
        look successful but return meaningless results.
        """
        if not settings.google_api_key:
            raise RuntimeError("GOOGLE_API_KEY is required for curriculum embeddings")
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise RuntimeError(
                "google-generativeai is required for embeddings; install backend requirements"
            ) from exc

        def _embed() -> List[float]:
            genai.configure(api_key=settings.google_api_key)
            result = genai.embed_content(
                model=settings.embedding_model,
                content=text,
                task_type="retrieval_document",
            )
            return result["embedding"]

        return await asyncio.to_thread(_embed)
    
    async def embed_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Generate embeddings for multiple chunks."""
        for chunk in chunks:
            chunk.embedding = await self.embed_text(chunk.content)
        return chunks
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        chunk_size: int = None,
        chunk_overlap: int = None
    ) -> int:
        """Add documents to vector store with chunking."""
        chunk_size = chunk_size or settings.max_chunk_size
        chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        all_chunks = []
        for doc in documents:
            chunks = self._chunk_document(doc["content"], doc["metadata"], chunk_size, chunk_overlap)
            all_chunks.extend(chunks)
        
        # Generate embeddings
        all_chunks = await self.embed_chunks(all_chunks)
        
        # Store in vector database
        await self.vector_store.add_chunks(all_chunks)
        
        return len(all_chunks)
    
    def _chunk_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        chunk_size: int,
        chunk_overlap: int
    ) -> List[DocumentChunk]:
        """Split document into overlapping chunks."""
        chunks = []
        start = 0
        chunk_num = 0
        
        while start < len(content):
            end = min(start + chunk_size, len(content))
            
            # Try to break at sentence boundary
            if end < len(content):
                last_period = content.rfind('. ', start, end)
                if last_period > start:
                    end = last_period + 1
            
            chunk_content = content[start:end].strip()
            if chunk_content:
                chunk_metadata = {
                    **metadata,
                    "chunk_index": chunk_num,
                    "chunk_start": start,
                    "chunk_end": end
                }
                chunks.append(DocumentChunk(chunk_content, chunk_metadata))
                chunk_num += 1
            
            start = max(0, end - chunk_overlap)
            if start >= len(content):
                break
        
        return chunks
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        subject: Optional[str] = None,
        class_level: Optional[int] = None,
        chapter: Optional[str] = None
    ) -> List[Tuple[DocumentChunk, float]]:
        """Retrieve relevant chunks for a query."""
        await self.initialize()
        
        # Generate query embedding
        query_embedding = await self.embed_text(query)
        
        # Build metadata filter
        filter_metadata = {}
        if subject:
            filter_metadata["subject"] = subject
        if class_level:
            filter_metadata["class_level"] = class_level
        if chapter:
            filter_metadata["chapter"] = chapter
        
        # Search
        results = await self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata if filter_metadata else None
        )
        
        return results
    
    async def retrieve_for_prompt(
        self,
        prompt_name: str,
        **kwargs
    ) -> str:
        """Retrieve context and format for prompt injection."""
        # Build query from prompt variables
        query_parts = []
        if "subject" in kwargs:
            query_parts.append(f"Subject: {kwargs['subject']}")
        if "class_level" in kwargs:
            query_parts.append(f"Class: {kwargs['class_level']}")
        if "chapter" in kwargs:
            query_parts.append(f"Chapter: {kwargs['chapter']}")
        
        query = " ".join(query_parts)
        
        # Retrieve relevant chunks
        results = await self.retrieve(query, top_k=5, **{k: v for k, v in kwargs.items() if k in ["subject", "class_level", "chapter"]})
        
        # Format as context
        context_parts = []
        for chunk, score in results:
            context_parts.append(f"[Source: {chunk.metadata.get('source', 'unknown')}, Relevance: {score:.2f}]\n{chunk.content}")
        
        return "\n\n---\n\n".join(context_parts) if context_parts else "No relevant curriculum content found."


# Global RAG service instance
rag_service = RAGService()


# =============================================================================
# NCERT Data Loader Utilities
# =============================================================================

class NCERTDataLoader:
    """Load and process NCERT curriculum data."""
    
    def __init__(self, data_dir: Optional[str] = None):
        # Resolve relative to repository root rather than process CWD, so the
        # API works whether launched from the root or backend/ directory.
        repo_root = Path(__file__).resolve().parents[3]
        self.data_dir = Path(data_dir) if data_dir else repo_root / "data"
        self.curriculum_dir = self.data_dir / "curriculum"
        self.prompts_dir = self.data_dir / "prompts"
        self.samples_dir = self.data_dir / "ncert_raw"
    
    def load_curriculum_map(self, subject: Subject, class_level: ClassLevel) -> Dict[str, Any]:
        """Load curriculum mapping for subject/class."""
        file_path = self.curriculum_dir / f"{subject.value}_class_{class_level.value}.json"
        if file_path.exists():
            with open(file_path) as f:
                return json.load(f)
        return self._get_default_curriculum(subject, class_level)
    
    def _get_default_curriculum(self, subject: Subject, class_level: ClassLevel) -> Dict[str, Any]:
        """Default curriculum structure."""
        return {
            "subject": subject.value,
            "class": class_level.value,
            "chapters": [],
            "learning_outcomes": {},
            "weightage": {}
        }
    
    def load_chapter_content(self, subject: Subject, class_level: ClassLevel, chapter: str) -> Optional[str]:
        """Load a downloaded chapter's extracted text, if present."""
        for file_path in self.samples_dir.glob(
            f"class_{class_level.value}/{subject.value}/*/{chapter}.txt"
        ):
            return file_path.read_text(encoding="utf-8")
        return None
    
    def load_all_chapters(self, subject: Subject, class_level: ClassLevel) -> Dict[str, str]:
        """Load chapter text extracted by scripts/scrape_ncert.py."""
        chapters: Dict[str, str] = {}
        subject_dir = self.samples_dir / f"class_{class_level.value}" / subject.value
        if subject_dir.exists():
            for file_path in subject_dir.glob("*/*.txt"):
                chapters[file_path.stem] = file_path.read_text(encoding="utf-8")
        return chapters
    
    def prepare_rag_documents(self, subject: Subject, class_level: ClassLevel) -> List[Dict[str, Any]]:
        """Prepare documents for RAG ingestion."""
        chapters = self.load_all_chapters(subject, class_level)
        curriculum = self.load_curriculum_map(subject, class_level)
        
        documents = []
        for chapter_name, content in chapters.items():
            # Find chapter metadata from curriculum
            chapter_meta = next(
                (c for c in curriculum.get("chapters", []) if c.get("name") == chapter_name),
                {}
            )
            
            documents.append({
                "content": content,
                "metadata": {
                    "subject": subject.value,
                    "class_level": class_level.value,
                    "chapter": chapter_name,
                    "source": "ncert_textbook",
                    "learning_outcomes": chapter_meta.get("learning_outcomes", []),
                    "weightage": chapter_meta.get("weightage", 0)
                }
            })
        
        return documents


# Global data loader
ncert_loader = NCERTDataLoader()