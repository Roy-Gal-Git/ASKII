# Codebase Information

## Overview

**ASKII** is a CLI tool that answers natural-language questions about codebases using a RAG (Retrieval-Augmented Generation) pipeline with an agentic architecture. It ingests local git repositories into ChromaDB and uses semantic search to retrieve relevant code chunks, then synthesizes answers using Google's Gemini LLM.

## Technology Stack

### Programming Languages
- **Primary**: Python 3.8+
- **Configuration**: Environment variables, `.env` files

### Core Dependencies
- **strands-agents[gemini]**: Agent framework with Gemini provider support
- **strands-agents-tools**: Tool integrations for agents
- **chromadb**: Vector database for storing embeddings
- **google-genai**: Google Generative AI SDK
- **tiktoken**: Token counting utilities
- **gitpython**: Git repository operations
- **yaspin**: Spinner animations for CLI
- **python-dotenv**: Environment variable management
- **pydantic**: Data validation and models
- **pathspec**: `.gitignore` pattern matching
- **google-generativeai**: Google Generative AI client

### Development Dependencies
- **pytest>=7.0.0**: Testing framework
- **pytest-mock>=3.10.0**: Mocking utilities for tests

## Project Structure

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
│   ├── retrieval/             # ChromaDB integration and retrieval
│   │   ├── db/chroma.py       # ChromaDB client wrapper
│   │   ├── embedding_function.py  # Custom Gemini embedding function
│   │   └── retriever.py      # Retrieval logic (semantic search, post-processing)
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
│   ├── db/                    # Database integration
│   │   └── chroma.py         # ChromaDB client singleton
│   └── utils/                 # Shared utilities
│       ├── git_utils.py      # Git operations (repo info, collection naming)
│       └── errors.py         # Error formatting utilities (user-friendly messages)
├── tests/                     # Integration and unit tests
│   ├── __init__.py
│   ├── test_error_handling.py # Error handling tests
│   └── test_graphs.py        # Graph smoke tests
├── examples/                  # Example queries and usage
├── requirements.txt          # Python dependencies
├── README.md                 # User-facing documentation
└── ARCHITECTURE.md           # Architecture documentation
```

## Key Characteristics

- **Language**: Python 3.8+
- **Architecture**: Strands graph RAG loop (Retriever → SynthInput → Synthesizer, else Explorer → Indexer → Retriever)
- **Storage**: ChromaDB (local, persistent)
- **LLM/Embeddings**: Google Gemini API
- **Chunking**: AST-based for Python, sliding window for other files
- **Read-Only**: Never modifies source repositories
- **Git-Only**: Only supports git repositories (non-git repos not supported)

## File Counts

- **Total Python files**: 21 source files
- **Test files**: 2 test files
- **Documentation files**: README.md, ARCHITECTURE.md, AGENTS.md

## Entry Points

- **CLI**: `app.py` → `src/cli/main.py`
- **Graph**: `src/agents/graphs/rag_loop.py` → `build_rag_loop_graph()`

## Configuration

Configuration is managed via environment variables:
- `GEMINI_API_KEY` or `GOOGLE_API_KEY`: Required for Gemini API access
- `AGENT_MAX_TOKENS`: Maximum total tokens for agent loop execution
- `SYNTHESIZER_MAX_OUTPUT_TOKENS`: Maximum output tokens for synthesizer (default: 8192)
- `RETRIEVER_MAX_OUTPUT_TOKENS`: Maximum output tokens for retriever (default: 2048)
- `ROUTER_MAX_OUTPUT_TOKENS`: Maximum output tokens for router (default: 2048)

## Data Storage

- **ChromaDB collections**: Stored in `.data/chroma/` (relative to current working directory)
- **Collection naming**: Based on normalized absolute repository path
- **Metadata**: Includes file_path, line_range, symbol_name, symbol_type, token_count

