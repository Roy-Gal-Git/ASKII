# ASKII - Code Repository Analyst

ASKII is a CLI tool that answers natural-language questions about codebases using a RAG (Retrieval-Augmented Generation) pipeline with an agentic architecture. It ingests local git repositories into ChromaDB and uses semantic search to retrieve relevant code chunks, then synthesizes answers using Google's Gemini LLM.

## Prerequisites

Before installing ASKII, ensure you have the following installed on your system:

- **Python 3.8+** - Required Python version
- **Git** - Required by GitPython for repository operations
- **ripgrep** (`rg` command) - Required by the Explorer agent for file searching
  - macOS: `brew install ripgrep`
  - Linux: `apt-get install ripgrep` or `yum install ripgrep`
  - Windows: Download from [ripgrep releases](https://github.com/BurntSushi/ripgrep/releases)
- **Google Gemini API Key** - Required for embeddings and LLM inference
  - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd ASKII
```

2. Install the package in editable mode:
```bash
pip install -e .
```

This will install all Python dependencies from `requirements.txt` and set up the `askii` command-line tool.

## Configuration

ASKII requires a Google Gemini API key to function. Set it as an environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Alternatively, you can use `GOOGLE_API_KEY` (both are supported).

For convenience, you can create a `.env` file in the project root:
```
GEMINI_API_KEY=your-api-key-here
```

The `.env` file is automatically loaded by the application.

## Quick Start

### Complete Setup and One-Command Start

```bash
# 1. Install ASKII
pip install -e .

# 2. Set your API key
export GEMINI_API_KEY="your-api-key-here"

# 3. Navigate to your repository (e.g., httpx)
cd /path/to/httpx

# 4. Ask a question about the codebase
askii "How does httpx handle request timeouts?"
```

Or using Python directly (without installation):
```bash
# Set API key
export GEMINI_API_KEY="your-api-key-here"

# Run directly
python app.py "How does httpx handle request timeouts?" --repository-path /path/to/httpx
```

**Note**: The first query may take longer as ASKII indexes relevant files on-demand. Subsequent queries are faster as the index is reused.

### Basic Usage

```bash
# Query the current directory (must be a git repository)
askii "How does the code validate SSL certificates?"

# Query a specific repository
askii "Where is proxy support implemented?" --repository-path /path/to/repo

# Reset the index and re-index before querying
askii "Explain the authentication flow" --repository-path /path/to/repo --reset-index
```

## Example Queries

Here are some example queries you can ask about the httpx library:

- "How does httpx validate SSL certificates?"
- "Where in the code is proxy support implemented?"
- "What happens if a request exceeds the configured timeout?"
- "How does httpx handle connection pooling?"
- "Where is the HTTP/2 implementation?"

See [examples/httpx_queries.md](examples/httpx_queries.md) for detailed examples with expected answer formats and citations.

## How It Works

ASKII uses a RAG (Retrieval-Augmented Generation) loop with targeted indexing:

1. **Retrieval**: Queries ChromaDB for semantically similar code chunks
2. **Gating**: If evidence is strong enough (similarity ≥ 0.7), proceeds to synthesis
3. **Exploration**: If evidence is weak, uses an Explorer agent to find relevant files
4. **Indexing**: Indexes Explorer-selected files into ChromaDB
5. **Synthesis**: Formats evidence and generates a cited answer using Gemini

The system automatically loops between retrieval and indexing until sufficient evidence is found or a maximum attempt limit is reached.

## Assumptions

- **Git-only repositories**: ASKII only supports git repositories. Non-git directories are not supported.
- **Read-only operations**: ASKII never modifies source repositories. It only reads files for indexing and querying.
- **Local storage**: ChromaDB data is stored locally in `.data/chroma/` (relative to current working directory).
- **System dependencies**: Requires `git` and `ripgrep` (`rg`) to be installed and available in PATH.

## Limitations

- **Chunking strategy**: AST-based chunking is only used for Python files (`.py`). All other text files use sliding window chunking with 20% overlap.
- **Token limits**: Maximum 300 tokens per chunk (enforced during chunking).
- **Similarity threshold**: Strong evidence threshold is 0.7 (cosine similarity). Lower similarity scores may result in additional indexing attempts.
- **Retrieval attempts**: Maximum 3 retrieval attempts before synthesizing an answer (even with weak evidence).
- **File types**: Best results with text-based source code. Binary files are skipped during indexing.

## Output Format

All answers include:
- Plain text format (no markdown in output)
- Inline citations: `[file_path:line_range]` (e.g., `[src/client.py:45-67]`)
- Grounded in retrieved code snippets
- Concise and focused responses

When evidence is weak or insufficient, ASKII will:
- Explicitly state uncertainties
- Show what was found vs. what's unclear
- Refuse to answer if no relevant code is found

## Project Structure

```
ASKII/
├── app.py                      # Entry point
├── src/
│   ├── agents/                 # Strands graph orchestration
│   │   ├── graphs/            # Graph builders
│   │   ├── nodes/             # Deterministic graph nodes
│   │   └── factories/         # Agent factories
│   ├── chunking/              # File chunking strategies
│   ├── cli/                   # Command-line interface
│   ├── db/                    # ChromaDB integration
│   └── utils/                 # Shared utilities
├── examples/                  # Example queries
├── tests/                     # Test suite
└── requirements.txt          # Python dependencies
```

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Troubleshooting

### "Error: Failed to extract repository information"
- Ensure you're in a git repository or provide `--repository-path` pointing to a git repo
- Verify git is installed: `git --version`

### "Error: Failed to access collection"
- Check that ChromaDB can write to `.data/chroma/` directory
- Ensure you have write permissions in the current directory

### "No relevant code found"
- The repository may not contain code related to your question
- Try rephrasing your question or using more specific terms
- Use `--reset-index` to force re-indexing

### Explorer agent fails to find files
- Verify `ripgrep` is installed: `rg --version`
- Ensure `rg` is in your PATH

## License

MIT License

## Contributing

Contributions are welcome! Please ensure all tests pass before submitting a pull request.

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src
```

