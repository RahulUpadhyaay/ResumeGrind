import pytest
from app.services.rag_service import rag_service
from app.schemas.models import CodeFile

def test_code_chunker():
    code_content = """def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
    code_file = CodeFile(file_path="math_utils.py", content=code_content, language="python")
    chunks = rag_service.chunk_code_file("repo_test", code_file)
    assert len(chunks) >= 1
    assert chunks[0].repo_name == "repo_test"
    assert chunks[0].file_path == "math_utils.py"

def test_cosine_similarity():
    vec_a = [1.0, 0.0, 0.0]
    vec_b = [1.0, 0.0, 0.0]
    vec_c = [0.0, 1.0, 0.0]

    sim_identical = rag_service.cosine_similarity(vec_a, vec_b)
    sim_orthogonal = rag_service.cosine_similarity(vec_a, vec_c)

    assert round(sim_identical, 2) == 1.0
    assert round(sim_orthogonal, 2) == 0.0
