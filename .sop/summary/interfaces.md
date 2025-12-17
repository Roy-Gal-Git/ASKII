# Interfaces and APIs

## Overview

This document describes the key interfaces, APIs, and integration points in the ASKII system.

## Public APIs

### CLI Interface

**Location**: `src/cli/main.py`

**Entry Point**: `main()`

**Command-Line Arguments**:
- `question` (optional): Natural language question about the codebase
- `--repository-path PATH`: Path to repository (defaults to current directory)
- `--reset-index`: Delete the existing index for this repository before querying

**Example Usage**:
```bash
python app.py "How does the code handle timeouts?"
python app.py "What is the main entry point?" --repository-path /path/to/repo
python app.py "Explain the authentication flow" --reset-index
```

### Graph Interface

**Location**: `src/agents/graphs/rag_loop.py`

**Function**: `build_rag_loop_graph(repo_path: str) -> Any`

**Parameters**:
- `repo_path`: Absolute path to the repository root (used to configure Explorer)

**Returns**: Built Strands graph instance

**Usage**:
```python
from src.agents.graphs import build_rag_loop_graph

graph = build_rag_loop_graph(repo_path="/path/to/repo")
```

**Node Actions**: `get_node_actions() -> dict[str, str]`

Returns a mapping of node IDs to human-friendly action labels for UI display.

### Chunking Interface

**Location**: `src/chunking/chunker.py`

**Function**: `chunk_file_from_path(file_path: str, repo_path: str) -> List[Chunk]`

**Parameters**:
- `file_path`: Absolute path to the file
- `repo_path`: Path to repository root (for relative paths)

**Returns**: List of Chunk objects

**Raises**: `IOError` if file cannot be read

**Example**:
```python
from src.chunking.chunker import chunk_file_from_path

chunks = chunk_file_from_path(
    file_path="/path/to/file.py",
    repo_path="/path/to/repo"
)
```

### ChromaDB Interface

**Location**: `src/db/chroma.py`

**Client**: `client` (singleton ChromaDB PersistentClient)

**Usage**:
```python
from src.db.chroma import client

collection = client.get_or_create_collection(
    name="my-repo",
    embedding_function=embedding_function,
    metadata={"hnsw:space": "cosine"},
)
```

### Git Utilities Interface

**Location**: `src/utils/git_utils.py`

**Function**: `get_repo_info(path: str) -> RepoInfo`

**Parameters**:
- `path`: Path to git repository

**Returns**: `RepoInfo` object with:
- `path`: Repository path
- `name`: Repository name
- `collection_name`: Normalized collection name

**Raises**: `ValueError` if path is not a valid git repository

**Example**:
```python
from src.utils.git_utils import get_repo_info

repo_info = get_repo_info("/path/to/repo")
print(repo_info.collection_name)
```

## Data Models

### Chunk

**Location**: `src/chunking/models.py`

**Class**: `Chunk(BaseModel)`

**Fields**:
- `text: str`: The actual code/text content
- `file_path: str`: Relative path from repo root
- `line_range: str`: start_line-end_line (e.g., '45-67')
- `symbol_name: Optional[str]`: Function or class name (for AST chunks)
- `symbol_type: Optional[str]`: 'function' | 'class' | None
- `token_count: int`: Number of tokens in chunk
- `chunk_id: str`: Unique identifier for ChromaDB

**Example**:
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

### RetrievalResult

**Location**: `src/chunking/models.py`

**Class**: `RetrievalResult(BaseModel)`

**Fields**:
- `chunks: List[Chunk]`: List of retrieved chunks
- `max_similarity: float`: Maximum similarity score (1 - distance)
- `num_chunks_above_threshold: int`: Number of chunks above similarity threshold
- `distances: List[float]`: Distance scores for each chunk (lower is more similar)

**Example**:
```python
from src.chunking.models import RetrievalResult

result = RetrievalResult(
    chunks=[chunk1, chunk2],
    max_similarity=0.85,
    num_chunks_above_threshold=2,
    distances=[0.15, 0.20]
)
```

### RepoInfo

**Location**: `src/utils/git_utils.py`

**Class**: `RepoInfo(BaseModel)`

**Fields**:
- `path: str`: Repository path
- `name: str`: Repository name
- `collection_name: str`: Normalized collection name

**Example**:
```python
from src.utils.git_utils import RepoInfo

repo_info = RepoInfo(
    path="/path/to/repo",
    name="my-repo",
    collection_name="path_to_repo"
)
```

## Node Interfaces

### RetrieverNode

**Location**: `src/agents/nodes/retriever.py`

**Class**: `RetrieverNode(MultiAgentBase)`

**Invocation State Requirements**:
- `question: str`: User question
- `collection: Collection`: ChromaDB collection
- `repo_path: str`: Repository path
- `attempts: int`: Current attempt count

**Output State**:
- `retrieval_result: RetrievalResult`: Retrieval results
- `should_synthesize: bool`: Whether to synthesize or continue loop
- `attempts: int`: Updated attempt count

**Node ID**: `"retriever"`

**Action**: `"Retrieving relevant snippets"`

### IndexerNode

**Location**: `src/agents/nodes/indexer.py`

**Class**: `IndexerNode(MultiAgentBase)`

**Invocation State Requirements**:
- `repo_path: str`: Repository path
- `collection: Collection`: ChromaDB collection
- `already_indexed: set[str]`: Set of already-indexed relative paths
- `explorer_files_abs: list[str]`: Absolute file paths from Explorer (optional, can extract from task)

**Output State**:
- `already_indexed: set[str]`: Updated set of indexed files

**Node ID**: `"indexer"`

**Action**: `"Indexing relevant files"`

### ExplorerSelectNode

**Location**: `src/agents/nodes/explorer_select.py`

**Class**: `ExplorerSelectNode(MultiAgentBase)`

**Invocation State Requirements**:
- `question: str`: User question
- `already_indexed: set[str]`: Already-indexed files (optional, for context)

**Output State**:
- `explorer_files_abs: list[str]`: Absolute file paths selected by Explorer

**Node ID**: `"explorer"`

**Action**: `"Searching the repository"`

### SynthInputNode

**Location**: `src/agents/nodes/synth_input.py`

**Class**: `SynthInputNode(MultiAgentBase)`

**Invocation State Requirements**:
- `question: str`: User question
- `retrieval_result: RetrievalResult`: Retrieval results

**Output State**:
- `synth_task: str`: Formatted task string for Synthesizer

**Node ID**: `"synth_input"`

**Action**: `"Preparing evidence"`

## Agent Interfaces

### Explorer Agent

**Location**: `src/agents/factories/explorer.py`

**Class**: `Explorer(Base)`

**Input**: Question string (with optional already-indexed file list)

**Output**: `FilesResponse` (Pydantic model):
- `files: list[str]`: Absolute file paths

**Tools**: `shell` (for ripgrep access)

**Model**: `gemini-2.5-flash` (temperature: 0.1)

**Name**: `"explorer"`

### Synthesizer Agent

**Location**: `src/agents/factories/synthesizer.py`

**Class**: `Synthesizer(Base)`

**Input**: Formatted task string (question + snippets with citations)

**Output**: Plain text answer with inline citations

**Model**: `gemini-2.5-flash` (temperature: 0.7, max_output_tokens: 8192)

**Name**: `"synthesizer"`

**Action**: `"Thinking"`

## Integration Points

### ChromaDB Integration

**Embedding Function**: Uses `chromadb.utils.embedding_functions.GoogleGenerativeAiEmbeddingFunction`

**Collection Metadata**:
- `hnsw:space`: `"cosine"` (cosine similarity)

**Chunk Metadata**:
- `file_path`: Relative path from repo root
- `line_range`: Line range string
- `symbol_name`: Symbol name (if applicable)
- `symbol_type`: Symbol type (if applicable)
- `token_count`: Token count

**Operations**:
- `collection.add()`: Add chunks
- `collection.query()`: Query chunks
- `collection.delete()`: Delete chunks by ID
- `collection.get()`: Get all chunks

### Strands Graph Integration

**Graph State**: `invocation_state` dictionary passed through all nodes

**Node Execution**: Nodes implement `invoke_async()` method

**Conditional Edges**: Based on `RetrieverNode` approval decision

**Streaming**: Synthesizer output streams directly to stdout

### Environment Variables

**Required**:
- `GEMINI_API_KEY` or `GOOGLE_API_KEY`: Google API key for Gemini

**Optional**:
- `AGENT_MAX_TOKENS`: Maximum total tokens for agent loop
- `SYNTHESIZER_MAX_OUTPUT_TOKENS`: Maximum output tokens for synthesizer (default: 8192)
- `RETRIEVER_MAX_OUTPUT_TOKENS`: Maximum output tokens for retriever (default: 2048)
- `ROUTER_MAX_OUTPUT_TOKENS`: Maximum output tokens for router (default: 2048)

**Loading**: Environment variables loaded via `python-dotenv` in `app.py`

## Error Handling

### Exception Types

**ValueError**: Invalid input (repository path, file paths)

**IOError**: File read errors

**TypeError**: Invalid structured output from agents

**Exception**: General errors (propagated with context)

### Error Propagation

- **CLI Layer**: Catches exceptions, prints user-friendly messages, exits with non-zero code
- **Graph Layer**: Errors propagate through graph execution
- **Node Layer**: Nodes handle errors appropriately (best-effort indexing, graceful degradation)

## Extension Points

### Adding a New Chunking Strategy

1. Create chunking function: `chunk_custom_file(file_path: str, source: str, repo_path: str) -> List[Chunk]`
2. Update `src/chunking/chunker.py` to route to new strategy
3. Follow existing chunking interface (return `List[Chunk]`)

### Adding a New Node

1. Extend `MultiAgentBase` from Strands
2. Implement `invoke_async()` method
3. Define `id` and `ACTION` class attributes
4. Add to graph in `build_rag_loop_graph()`

### Adding a New Agent

1. Extend `Base` factory class
2. Implement required methods: `_system_prompt()`, `_model()`, `_name()`
3. Optionally implement: `_tools()`, `_structured_output_model()`
4. Create factory instance and add to graph

### Customizing Embeddings

1. Create custom embedding function (compatible with ChromaDB)
2. Pass to `client.get_or_create_collection()` with `embedding_function` parameter
3. Ensure consistent embedding function across collection lifecycle

