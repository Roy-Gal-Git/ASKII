"""Tests for synth input formatting."""

from src.agents.nodes.synth_input import SynthInputNode
from src.chunking.models import Chunk, RetrievalResult


def test_format_task_with_chunks():
    """Test _format_task formats question and chunks correctly."""
    chunks = [
        Chunk(
            text="def hello():\n    return 'world'",
            file_path="test.py",
            line_range="10-12",
            symbol_name="hello",
            symbol_type="function",
            chunk_id="id1",
        ),
        Chunk(
            text="class MyClass:\n    pass",
            file_path="test.py",
            line_range="15-17",
            symbol_name="MyClass",
            symbol_type="class",
            chunk_id="id2",
        ),
    ]
    retrieval_result = RetrievalResult(
        chunks=chunks,
        max_similarity=0.85,
        num_chunks_above_threshold=2,
        distances=[0.15, 0.20],
    )

    task = SynthInputNode._format_task(question="What does hello do?", retrieval_result=retrieval_result)

    assert "User question:" in task
    assert "What does hello do?" in task
    assert "Evidence: 2 snippet(s)" in task
    assert "max_similarity=0.8500" in task
    assert "[test.py:10-12]" in task
    assert "[test.py:15-17]" in task
    assert "function: hello" in task
    assert "class: MyClass" in task
    assert "def hello()" in task
    assert "class MyClass" in task


def test_format_task_without_symbols():
    """Test _format_task handles chunks without symbol names."""
    chunks = [
        Chunk(
            text="Some code here",
            file_path="test.txt",
            line_range="5-7",
            symbol_name=None,
            symbol_type=None,
            chunk_id="id1",
        ),
    ]
    retrieval_result = RetrievalResult(
        chunks=chunks,
        max_similarity=0.75,
        num_chunks_above_threshold=1,
        distances=[0.25],
    )

    task = SynthInputNode._format_task(question="What is this?", retrieval_result=retrieval_result)

    assert "[test.txt:5-7]" in task
    assert "Some code here" in task
    # Should not include symbol info
    assert "function:" not in task
    assert "class:" not in task


def test_format_task_empty_chunks():
    """Test _format_task handles empty chunks."""
    retrieval_result = RetrievalResult(
        chunks=[],
        max_similarity=0.0,
        num_chunks_above_threshold=0,
        distances=[],
    )

    task = SynthInputNode._format_task(question="Test question", retrieval_result=retrieval_result)

    assert "User question:" in task
    assert "Test question" in task
    assert "Evidence: 0 snippet(s)" in task
    assert "No snippets retrieved." in task


def test_format_task_citation_format():
    """Test _format_task includes correct citation format."""
    chunks = [
        Chunk(
            text="code",
            file_path="src/utils.py",
            line_range="42-45",
            chunk_id="id1",
        ),
    ]
    retrieval_result = RetrievalResult(
        chunks=chunks,
        max_similarity=0.8,
        num_chunks_above_threshold=1,
        distances=[0.2],
    )

    task = SynthInputNode._format_task(question="Q", retrieval_result=retrieval_result)

    # Check citation format: [file_path:line_range]
    assert "[src/utils.py:42-45]" in task


def test_format_task_snippet_numbering():
    """Test _format_task numbers snippets correctly."""
    chunks = [
        Chunk(text="code1", file_path="file1.py", line_range="1-2", chunk_id="id1"),
        Chunk(text="code2", file_path="file2.py", line_range="3-4", chunk_id="id2"),
        Chunk(text="code3", file_path="file3.py", line_range="5-6", chunk_id="id3"),
    ]
    retrieval_result = RetrievalResult(
        chunks=chunks,
        max_similarity=0.9,
        num_chunks_above_threshold=3,
        distances=[0.1, 0.15, 0.2],
    )

    task = SynthInputNode._format_task(question="Q", retrieval_result=retrieval_result)

    assert "Snippet 1:" in task
    assert "Snippet 2:" in task
    assert "Snippet 3:" in task


def test_format_task_code_block_formatting():
    """Test _format_task wraps code in code blocks."""
    chunks = [
        Chunk(
            text="def func():\n    return True",
            file_path="test.py",
            line_range="10-12",
            chunk_id="id1",
        ),
    ]
    retrieval_result = RetrievalResult(
        chunks=chunks,
        max_similarity=0.8,
        num_chunks_above_threshold=1,
        distances=[0.2],
    )

    task = SynthInputNode._format_task(question="Q", retrieval_result=retrieval_result)

    # Check code block markers
    assert "```" in task
    # Code should appear between markers
    assert "def func():" in task
    assert "return True" in task

