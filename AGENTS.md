# AGENTS.md - AI Coding Assistant Guide

## Purpose

This document provides comprehensive context for AI coding assistants working with the ASKII codebase. It focuses on development patterns, file organization, coding standards, and assistant-specific guidance that complements the user-facing README.md and ARCHITECTURE.md.

## Project Overview

**ASKII** is a CLI tool that answers natural-language questions about codebases using a RAG (Retrieval-Augmented Generation) pipeline with an agentic architecture. It ingests local git repositories into ChromaDB and uses semantic search to retrieve relevant code chunks, then synthesizes answers using Google's Gemini LLM.

### Key Characteristics

- **Language**: Python 3.8+
- **Architecture**: Strands graph RAG loop (Retriever → SynthInput → Synthesizer, else Explorer → Indexer → Retriever)
- **Storage**: ChromaDB (local, persistent)
- **LLM/Embeddings**: Google Gemini API
- **Chunking**: AST-based for Python, sliding window for other files
- **Read-Only**: Never modifies source repositories
- **Git-Only**: Only supports git repositories (non-git repos not supported)

## Directory Structure

```
ASKII/
├── app.py                      # Entry point (delegates to src/cli/main.py)
├── src/
│   ├── chunking/              # File chunking strategies
│   │   ├── chunker.py         # Main chunking interface (routes to strategy)
│   │   ├── ast_chunker.py     # AST-based chunking for Python files
│   │   ├── sliding_window.py  # Sliding window chunking for other files
│   │   ├── token_counter.py   # Token counting utilities (tiktoken)
│   │   └── models.py          # Chunk and RetrievalResult data models
│   ├── db/                    # Database integration
│   │   └── chroma.py         # ChromaDB client wrapper
│   ├── agents/                 # Strands graph orchestration
│   │   ├── graphs/            # Graph builders
│   │   │   └── rag_loop.py    # Primary RAG loop graph
│   │   ├── nodes/             # Deterministic graph nodes
│   │   │   ├── retriever.py   # Retrieval + gating node
│   │   │   ├── explorer_select.py  # Explorer agent bridge node
│   │   │   ├── indexer.py    # Indexing node
│   │   │   └── synth_input.py # Synthesizer input formatting node
│   │   └── factories/         # Strands Agent factories (Explorer/Synthesizer)
│   │       ├── base.py        # Base factory class
│   │       ├── explorer.py    # Explorer agent factory
│   │       └── synthesizer.py # Synthesizer agent factory
│   ├── cli/                   # Command-line interface
│   │   ├── main.py           # CLI entry point (argparse, ingestion, query execution)
│   │   └── progress.py       # Progress indicator utilities
│   └── utils/                 # Shared utilities
│       └── git_utils.py     # Git operations (repo info, collection naming)
├── tests/                     # Integration and unit tests
│   ├── __init__.py
│   └── test_error_handling.py # Error handling tests
│   └── test_graphs.py         # Graph smoke tests
├── .data/                     # Data storage (gitignored)
│   ├── chroma/               # ChromaDB collections
├── .sop/                      # Planning and design documents
│   └── summary/              # Generated documentation (this file's source)
├── examples/                  # Example queries and usage
├── requirements.txt          # Python dependencies
├── README.md                 # User-facing documentation
└── ARCHITECTURE.md           # Architecture documentation
```

## Coding Style Patterns

### Type Hints

- **Always use type hints** for function parameters and return types
- Use `Optional[T]` for nullable values
- Use `List[T]`, `Dict[K, V]` for collections
- Example:
```python
def some_function(
    collection: Collection,
    question: str,
    top_k: int = 10
) -> RetrievalResult:
    ...
```

### Pydantic Models

- **All data models use Pydantic** (`BaseModel`)
- Use `Field()` for descriptions and defaults
- Factory methods for creation (e.g., `create_now()`)
- Example:
```python
class Chunk(BaseModel):
    text: str = Field(..., description="The actual code/text content")
    file_path: str = Field(..., description="Relative path from repo root")
    line_range: str = Field(..., description="start_line-end_line (e.g., '45-67')")
    symbol_name: Optional[str] = Field(None, description="Function or class name")
    token_count: int = Field(0, description="Number of tokens in chunk")
    chunk_id: str = Field("", description="Unique identifier for ChromaDB")
```

### Error Handling

- **Prefer raw upstream exceptions** for core dependencies (Gemini/ChromaDB) so debugging details are preserved.
- **Graceful degradation**: Skip bad files during ingestion, continue processing
- **User messaging**: CLI prints errors and exits non-zero

Example:
```python
try:
    result = api_call()
except Exception as e:
    raise
```

### Docstrings

- **All public functions have docstrings**
- Format: Description, Args, Returns, Raises
- Example:
```python
def some_function(
    collection: Collection, question: str, top_k: int = 10
) -> RetrievalResult:
    """
    Do some work.

    Args:
        collection: ChromaDB collection to query
        question: Question/query text to search for
        top_k: Number of top results to retrieve (default: 10)

    Returns:
        RetrievalResult: Retrieval result with chunks, similarity scores, and metrics

    Raises:
        ValueError: If collection is empty or query fails
    """
```

### Module Organization

- **One class/function per logical unit**
- **Clear separation of concerns**: Each module has a single responsibility
- **Import organization**: Standard library → Third-party → Local
- **Circular dependency avoidance**: Utils don't import from agents/retrieval/synthesizer

### Configuration Management

- **Environment variables** loaded via `python-dotenv` in `app.py`
- Support both `.env` file and system environment variables
- Configuration accessed directly via `os.getenv()` throughout codebase
- **No hardcoded values**: All configurable via environment variables
- **API Key**: `GEMINI_API_KEY` or `GOOGLE_API_KEY` required
- **Optional**: `AGENT_MAX_TOKENS`, `SYNTHESIZER_MAX_OUTPUT_TOKENS`, etc.

### Progress Indicators

- **Use `yaspin`** for progress indication during graph execution
- Spinner shows current node action (e.g., "Retrieving relevant snippets", "Searching the repository")
- Spinner stops when Synthesizer begins streaming output
- Implementation: `src/cli/progress.py` (SpinnerUI class)
- Example:
```python
from src.cli.progress import SpinnerUI

ui = SpinnerUI.start(node_actions=node_actions, text="Thinking")
ui.set_node(node_id="retriever")  # Updates spinner text
ui.stop()  # Stops spinner
```

## File Organization Patterns

### Module Structure

Each module follows this pattern:
1. **Imports** (standard → third-party → local)
2. **Constants** (if any)
3. **Helper functions** (private, `_prefix`)
4. **Public functions/classes**
5. **Main entry point** (if applicable)

### Data Models Location

- **Chunking models**: `src/chunking/models.py` (Chunk, RetrievalResult)
- **Repo metadata model**: `src/utils/git_utils.py` (RepoInfo)

### Error Handling Location

- **Error handling**: In each module (appropriate for context)
- **User messages**: CLI/graph surfaces user-friendly error messages
- **Pattern**: Prefer raw upstream exceptions for core dependencies (Gemini/ChromaDB) so debugging details are preserved
- **Graceful degradation**: Skip bad files during indexing, continue processing
- **CLI errors**: Print user-friendly messages and exit non-zero

### Configuration Location

- **Environment loading**: `app.py` (loads `.env` file via `python-dotenv`)
- **Configuration access**: Direct `os.getenv()` calls throughout codebase
- **No config module**: Configuration is accessed directly where needed

## Development Patterns

### Adding a New Component

1. **Create module** in appropriate directory (`src/chunking/`, `src/db/`, etc.)
2. **Add type hints** to all functions
3. **Add docstrings** to public functions
4. **Use Pydantic models** for data structures
5. **Handle errors** with user-friendly messages
6. **Add tests** in `tests/` directory
7. **Update documentation** in `.sop/summary/`

### Modifying a Workflow

1. **Understand current flow** (see `workflows.md`)
2. **Identify components** involved (see `components.md`)
3. **Update components** as needed
4. **Maintain error handling** patterns
5. **Update tests** to cover changes
6. **Update documentation** if workflow changes

### Adding a New Data Model

1. **Choose location**: `src/chunking/models.py` (chunking/retrieval models) or the owning module (e.g., `src/utils/git_utils.py`)
2. **Use Pydantic** `BaseModel`
3. **Add Field descriptions**
4. **Add factory methods** if needed (e.g., `create_now()`)
5. **Update serialization** if needed (JSON, ChromaDB)
6. **Update components** that use the model
7. **Add validation** rules

### Integrating a New Dependency

1. **Add to `requirements.txt`**
2. **Document in `.sop/summary/dependencies.md`**
3. **Add configuration** if needed (environment variables)
4. **Handle errors** appropriately
5. **Update tests** if needed

## Testing Patterns

### Test Structure

- **Integration tests**: `tests/test_integration.py` (end-to-end workflows)
- **Edge case tests**: `tests/test_edge_cases.py` (empty repos, syntax errors, etc.)
- **Error handling tests**: `tests/test_error_handling.py` (error message formats, error propagation)

### Test Patterns

- **Use pytest** for all tests
- **Mock external dependencies** (API calls, ChromaDB)
- **Test error paths** as well as success paths
- **Test user-friendly messages** (error formatting)

Example:
```python
import pytest
from unittest.mock import Mock, patch

def test_retrieve_chunks_empty_collection():
    collection = Mock()
    collection.query.return_value = {"ids": [], "documents": []}

    # Example placeholder assertion: your retrieval logic lives in the RetrieverNode.
    # If unit testing retrieval behavior, test `src/agents/nodes/retriever.py` helpers directly.
    result = {"chunks": [], "max_similarity": 0.0}

    assert result["chunks"] == []
    assert result["max_similarity"] == 0.0
```

## Key Design Patterns

### Strategy Pattern

- **Chunking strategies**: AST for Python, sliding window for others
- **Location**: `src/chunking/chunker.py` routes to appropriate strategy
- **Pattern**: Single interface, multiple implementations

### Repository Pattern

- **ChromaDB client**: Abstraction over ChromaDB operations
- **Location**: `src/db/chroma.py`
- **Pattern**: Encapsulate data access logic

### Factory Pattern

- **Agent creation**: Factories build configured Strands Agents (Explorer/Synthesizer)
- **Location**: `src/agents/factories/`
- **Pattern**: Encapsulate configuration (model, system prompt, tools) behind a small wrapper API

## Important Constants and Thresholds

### Chunking

- **Max tokens per chunk**: 300
- **Sliding window overlap**: 20% (60 tokens)
- **Token counting**: `tiktoken` with `cl100k_base` encoding

### Retrieval

- **Default top-k**: 10 chunks
- **Similarity threshold**: 0.7 (for evidence strength)
- **Deduplication**: Overlapping chunks (same file, overlapping line ranges)

### Synthesizer

- **Strong evidence threshold**: 0.7 similarity
- **Weak evidence threshold**: 0.5 similarity
- **Min chunks for strong**: 3 chunks
- **Temperature**: 0.7
- **Max output tokens**: 8192 (configurable via `SYNTHESIZER_MAX_OUTPUT_TOKENS`)

### Embeddings

- **Model**: `gemini-embedding-001`
- **Batch size**: 100 items per batch
- **Dimension**: 768 (handled by ChromaDB)

### LLM

- **Model**: `gemini-2.5-flash`
- **Streaming**: Yes (streams directly to stdout)
- **Temperature**: 0.7

## Common Tasks

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_integration.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src
```

### Adding a New Chunking Strategy

1. Create new file in `src/chunking/` (e.g., `custom_chunker.py`)
2. Implement chunking function: `chunk_custom_file(file_path: str, source: str, repo_path: str) -> List[Chunk]`
3. Update `src/chunking/chunker.py` to route to new strategy
4. Add tests in `tests/`
5. Update documentation

### Adding a New Agent

1. Create agent file in `src/agents/` (e.g., `new_agent.py`)
2. Implement agent function with type hints and docstrings
3. Update `src/agents/graphs/rag_loop.py` (or another graph builder) to integrate the new agent/node
4. Add error handling
5. Add tests
6. Update documentation

### Modifying Error Messages

1. Keep messages:
   - Plain English (no technical jargon)
   - Actionable (suggests specific steps)
   - Specific (different messages for different scenarios)
   - Contextual (includes relevant details)

## Code Examples

### Creating a Chunk

```python
from src.chunking.models import Chunk

chunk = Chunk(
    text="def calculate_average(numbers: list[float]) -> float:\n    return sum(numbers) / len(numbers)",
    file_path="src/utils/math.py",
    line_range="45-47",
    symbol_name="calculate_average",
    symbol_type="function",
    token_count=15,
    chunk_id="src/utils/math.py:45-47"
)
```

### Querying ChromaDB

```python
from src.db.chroma import client
from src.db.embedding import GeminiEmbeddingFunction

embedding_function = GeminiEmbeddingFunction(api_key="YOUR_API_KEY")

try:
    collection = client.get_collection(name="my-repo", embedding_function=embedding_function)
except Exception:
    collection = client.create_collection(
        name="my-repo",
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )

results = collection.query(query_texts=["How does authentication work?"], n_results=10)
```

### Retrieving Chunks

Retrieval + gating is handled inside `src/agents/nodes/retriever.py` (the `RetrieverNode`).

### Generating Embeddings

```python
from src.db.embedding import GeminiEmbeddingFunction

embedding_function = GeminiEmbeddingFunction(api_key="YOUR_API_KEY")
embeddings = embedding_function(["text1", "text2", "text3"])  # Returns list of lists
```

### Handling Errors

```python
try:
    result = api_call()
except Exception as e:
    raise
```

## Documentation Guidelines

### When to Update Documentation

- **New components**: Update `components.md`
- **New APIs**: Update `interfaces.md`
- **New data models**: Update `data_models.md`
- **Workflow changes**: Update `workflows.md`
- **New dependencies**: Update `dependencies.md`
- **Architecture changes**: Update `architecture.md`

### Documentation Location

- **User-facing**: `README.md`, `ARCHITECTURE.md`
- **AI assistant context**: This file (`AGENTS.md`)
- **Detailed documentation**: `.sop/summary/` directory
- **Planning documents**: `.sop/planning/` directory

## Package-Specific Guidance

### Chunking Package

- **Entry point**: `chunk_file_from_path()` in `chunker.py`
- **Strategies**: AST for `.py` files, sliding window for others
- **Token limit**: Enforced at 300 tokens
- **Line ranges**: Precise for AST chunks, estimated for sliding window

### Database Package

- **ChromaDB client**: `src/db/chroma.py` (singleton persistent client)
- **Embedding function**: `src/db/embedding.py` (`GeminiEmbeddingFunction` using `google-genai` package and `gemini-embedding-001` model)
- **Retriever**: `src/agents/nodes/retriever.py` (semantic search, post-processing, gating)

### Agents Package

- **Graphs**: `src/agents/graphs/` (top-level orchestration)
- **Nodes**: `src/agents/nodes/` (deterministic steps: retrieval gate, explorer selection bridge, indexing, synth input formatting)
- **Factories**: `src/agents/factories/` (configured Strands agents: Explorer/Synthesizer)

### Utils Package

- **Git utils**: `git_utils.py` (repo info, collection naming, GitRepo wrapper)
- **Models**: `RepoInfo` Pydantic model in `git_utils.py`

## Important Notes for AI Assistants

### Code Modification Guidelines

1. **Maintain type hints**: Always add/update type hints
2. **Update docstrings**: Keep docstrings current
3. **Follow error handling patterns**: Use error formatting utilities
4. **Test changes**: Run tests after modifications
5. **Update documentation**: Update relevant docs if behavior changes

### Common Pitfalls

1. **Hardcoded paths**: Keep ChromaDB data stored under `.data/chroma` (relative to current working directory) and avoid scattering path logic across modules
2. **Missing error handling**: Always handle errors with user-friendly messages
3. **Missing type hints**: Always add type hints to new functions
4. **Circular imports**: Utils shouldn't import from agents/retrieval/synthesizer
5. **Token limits**: Remember 300-token limit for chunks
6. **Git-only**: Only support git repositories (non-git repos not supported)

### When to Ask for Clarification

- **Architecture decisions**: If unsure about design pattern to use
- **Error handling**: If error scenario is unclear
- **Data models**: If data structure needs clarification
- **API changes**: If modifying public APIs

## Quick Reference

### Key Files

- **Entry point**: `app.py` → `src/cli/main.py`
- **Graph**: `src/agents/graphs/rag_loop.py`
- **Chunking**: `src/chunking/chunker.py`
- **Retrieval**: handled by `RetrieverNode` in `src/agents/nodes/retriever.py`
- **Agents (factories)**: `src/agents/factories/`
- **Graph nodes**: `src/agents/nodes/`
- **ChromaDB client**: `src/db/chroma.py`
- **Git utils**: `src/utils/git_utils.py`

### Key Functions

- **Graph build**: `build_rag_loop_graph()` in `src/agents/graphs/rag_loop.py`
- **Chunking**: `chunk_file_from_path()` in `chunker.py`
- **Retrieval**: handled by `RetrieverNode` in `src/agents/nodes/retriever.py`

### Key Models

- **Chunk**: `src/chunking/models.py` (Pydantic BaseModel)
- **RetrievalResult**: `src/chunking/models.py` (Pydantic BaseModel)
- **RepoInfo**: `src/utils/git_utils.py` (Pydantic BaseModel)
- **FilesResponse**: `src/agents/factories/explorer.py` (Pydantic BaseModel for Explorer structured output)

## Additional Resources

- **Architecture details**: See `ARCHITECTURE.md`
- **User documentation**: See `README.md`
- **Detailed documentation**: See `.sop/summary/index.md` for full documentation index
- **Planning documents**: See `.sop/planning/` for design and implementation details

---

**Last Updated**: Generated during codebase summary
**Documentation Version**: 1.0
**For detailed component documentation**: See `.sop/summary/components.md`
**For API documentation**: See `.sop/summary/interfaces.md`
**For workflow documentation**: See `.sop/summary/workflows.md`
