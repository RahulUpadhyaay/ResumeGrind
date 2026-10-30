import math
import asyncio
from typing import List, Dict, Any, Optional
from google import genai
from pydantic import BaseModel
from app.config import settings
from app.schemas.models import CodeFile

class CodeChunk(BaseModel):
    chunk_id: str
    repo_name: str
    file_path: str
    content: str
    language: str
    embedding: Optional[List[float]] = None

class RAGSearchResult(BaseModel):
    chunk: CodeChunk
    similarity_score: float

class RAGService:
    """
    Semantic Code Vector RAG Engine.
    Chunks source code files, generates 768-dim dense vector embeddings via Gemini text-embedding-004,
    and performs cosine similarity matrix searches across candidate GitHub repos.
    """

    def __init__(self):
        api_key = settings.GEMINI_API_KEY or "dummy_key_for_dev_init"
        self.client = genai.Client(api_key=api_key)
        self.embedding_model = "text-embedding-004"
        self.vector_store: List[CodeChunk] = []


    def chunk_code_file(self, repo_name: str, code_file: CodeFile) -> List[CodeChunk]:
        """Splits source code file into logical function/class/block chunks."""
        lines = code_file.content.split('\n')
        chunks = []
        chunk_lines = []
        chunk_counter = 1

        for line in lines:
            chunk_lines.append(line)
            # Break chunk at logical boundaries (functions/classes or every 30 lines)
            if len(chunk_lines) >= 25 or line.strip().startswith(('def ', 'class ', 'function ', 'export ', 'async def ')):
                content_text = "\n".join(chunk_lines).strip()
                if len(content_text) >= 15:
                    chunks.append(CodeChunk(
                        chunk_id=f"{repo_name}_{code_file.file_path}_{chunk_counter}",
                        repo_name=repo_name,
                        file_path=code_file.file_path,
                        content=content_text,
                        language=code_file.language
                    ))
                    chunk_counter += 1
                chunk_lines = []

        if chunk_lines:
            content_text = "\n".join(chunk_lines).strip()
            if len(content_text) >= 15:
                chunks.append(CodeChunk(
                    chunk_id=f"{repo_name}_{code_file.file_path}_{chunk_counter}",
                    repo_name=repo_name,
                    file_path=code_file.file_path,
                    content=content_text,
                    language=code_file.language
                ))


        return chunks

    async def generate_embedding(self, text: str) -> List[float]:
        """Generates dense vector embedding using Gemini text-embedding-004."""
        try:
            res = await self.client.aio.models.embed_content(
                model=self.embedding_model,
                contents=text[:2000]
            )
            if res.embedding and res.embedding.values:
                return list(res.embedding.values)
        except Exception as e:
            print(f"[RAG SERVICE] Embedding generation error: {e}")
        return []

    def cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Computes cosine similarity between two dense vectors."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    async def index_repository_code(self, repo_name: str, key_files: List[CodeFile]):
        """Chunks and vector-indexes all repository files into vector_store."""
        all_chunks = []
        for f in key_files:
            chunks = self.chunk_code_file(repo_name, f)
            all_chunks.extend(chunks)

        for chunk in all_chunks[:15]: # Limit index size for speed
            embedding = await self.generate_embedding(f"File: {chunk.file_path}\n{chunk.content}")
            if embedding:
                chunk.embedding = embedding
                self.vector_store.append(chunk)

        print(f"[RAG SERVICE] Successfully indexed {len(self.vector_store)} vector chunks for {repo_name}.")

    async def query_code_vector_db(self, query_text: str, top_k: int = 2) -> List[RAGSearchResult]:
        """Performs semantic vector search against candidate codebase."""
        if not self.vector_store or not query_text.strip():
            return []

        query_vector = await self.generate_embedding(query_text)
        if not query_vector:
            return []

        results = []
        for chunk in self.vector_store:
            if chunk.embedding:
                score = self.cosine_similarity(query_vector, chunk.embedding)
                results.append(RAGSearchResult(chunk=chunk, similarity_score=score))

        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:top_k]

rag_service = RAGService()
