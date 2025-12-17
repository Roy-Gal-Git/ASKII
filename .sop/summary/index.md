# Documentation Index

## Purpose

This index serves as a knowledge base for AI assistants working with the ASKII codebase. It provides explicit instructions on how to use the documentation, rich metadata about each file's purpose and content, and guidance on which files to consult for specific types of questions.

## How to Use This Documentation

### For AI Assistants

1. **Start Here**: When answering questions about the codebase, consult this index first to identify relevant documentation files.

2. **Targeted Lookup**: Use the table of contents below to find files relevant to your question type:
   - **Architecture questions**: See `architecture.md`
   - **Component details**: See `components.md`
   - **API/Interface questions**: See `interfaces.md`
   - **Data structure questions**: See `data_models.md`
   - **Process/workflow questions**: See `workflows.md`
   - **Dependency questions**: See `dependencies.md`
   - **General codebase info**: See `codebase_info.md`

3. **Cross-Reference**: Many topics span multiple files. Use the relationships section to find related information.

4. **Metadata Tags**: Each file includes metadata tags to help identify its content scope and relevance.

## Table of Contents

### Core Documentation

| File | Purpose | Content Summary | When to Use |
|------|---------|----------------|-------------|
| `codebase_info.md` | Basic codebase information | Project overview, structure, technology stack, entry points | General questions about project structure, languages, dependencies |
| `architecture.md` | System architecture and design | High-level architecture, component relationships, design decisions | Questions about system design, architecture patterns, design rationale |
| `components.md` | Component details | Detailed component descriptions, responsibilities, interactions | Questions about specific components, their functions, how they work |
| `interfaces.md` | APIs and interfaces | Public APIs, data models, integration points, extension points | Questions about how to use APIs, integrate components, extend the system |
| `data_models.md` | Data structures | Pydantic models, dataclasses, internal data structures | Questions about data structures, model fields, data flow |
| `workflows.md` | Processes and workflows | Detailed workflow descriptions, step-by-step processes | Questions about how processes work, execution flows, step sequences |
| `dependencies.md` | External dependencies | Dependency descriptions, usage patterns, version info | Questions about dependencies, their purposes, how they're used |

### Consolidated Documentation

| File | Purpose | Content Summary | When to Use |
|------|---------|----------------|-------------|
| `../AGENTS.md` | AI assistant guide | Comprehensive guide for AI coding assistants | Primary reference for AI assistants, includes patterns, guidelines, examples |

## File Relationships

### Architecture → Components
- `architecture.md` provides high-level view
- `components.md` provides detailed component descriptions
- **Use together** for understanding system structure

### Components → Interfaces
- `components.md` describes what components do
- `interfaces.md` describes how to use them
- **Use together** for implementation and integration

### Interfaces → Data Models
- `interfaces.md` describes APIs and data flow
- `data_models.md` describes data structures
- **Use together** for understanding data handling

### Workflows → Components
- `workflows.md` describes processes
- `components.md` describes components involved
- **Use together** for understanding execution flows

### Dependencies → Components
- `dependencies.md` describes external libraries
- `components.md` shows where they're used
- **Use together** for understanding external integrations

## Quick Reference Guide

### Common Question Types

#### "How does X work?"
1. Check `workflows.md` for process descriptions
2. Check `components.md` for component details
3. Check `architecture.md` for high-level flow

#### "What is X?"
1. Check `codebase_info.md` for general information
2. Check `components.md` for component descriptions
3. Check `data_models.md` for data structure definitions

#### "How do I use X?"
1. Check `interfaces.md` for API documentation
2. Check `components.md` for usage examples
3. Check `workflows.md` for integration workflows

#### "Where is X implemented?"
1. Check `components.md` for component locations
2. Check `codebase_info.md` for file structure
3. Check `architecture.md` for module organization

#### "What dependencies does X use?"
1. Check `dependencies.md` for dependency descriptions
2. Check `components.md` for component dependencies
3. Check `interfaces.md` for integration points

## Metadata Tags

### Content Scope Tags

- **#architecture**: System architecture and design
- **#components**: Component descriptions and details
- **#interfaces**: APIs, interfaces, and integration points
- **#data-models**: Data structures and models
- **#workflows**: Processes and execution flows
- **#dependencies**: External dependencies and libraries
- **#codebase-info**: General codebase information

### Topic Tags

- **#rag**: Retrieval-Augmented Generation
- **#chunking**: File chunking strategies
- **#retrieval**: ChromaDB retrieval operations
- **#synthesis**: Answer generation
- **#graph**: Strands graph orchestration
- **#agents**: Agent factories and configuration
- **#nodes**: Deterministic graph nodes
- **#cli**: Command-line interface
- **#chromadb**: Vector database operations
- **#git**: Git repository operations
- **#embeddings**: Embedding generation
- **#llm**: Large language model usage

## Documentation Maintenance

### When to Update

- **New components**: Update `components.md` and `architecture.md`
- **New APIs**: Update `interfaces.md`
- **New data models**: Update `data_models.md`
- **New workflows**: Update `workflows.md`
- **New dependencies**: Update `dependencies.md`
- **Structural changes**: Update `codebase_info.md` and `architecture.md`

### Update Process

1. Identify affected documentation files
2. Update relevant sections
3. Update this index if file purposes change
4. Update relationships if new connections emerge
5. Update metadata tags if scope changes

## Example Queries

### Example 1: Understanding the RAG Loop

**Query**: "How does the RAG loop work?"

**Files to Consult**:
1. `workflows.md` → "Main Workflow: Query Execution"
2. `architecture.md` → "Agent Flow" section
3. `components.md` → "Graph Orchestration" section

**Answer Strategy**: Start with workflow description, then architecture overview, then component details.

### Example 2: Adding a New Chunking Strategy

**Query**: "How do I add a new chunking strategy?"

**Files to Consult**:
1. `interfaces.md` → "Extension Points" section
2. `components.md` → "Chunking Module" section
3. `workflows.md` → "Chunking Workflow" section

**Answer Strategy**: Start with extension points, then component details, then workflow integration.

### Example 3: Understanding Data Models

**Query**: "What data models are used for chunks?"

**Files to Consult**:
1. `data_models.md` → "Chunk" section
2. `interfaces.md` → "Data Models" section
3. `components.md` → "Chunking Module" section

**Answer Strategy**: Start with data model definition, then interface usage, then component implementation.

### Example 4: Debugging Retrieval Issues

**Query**: "Why is retrieval not finding relevant chunks?"

**Files to Consult**:
1. `workflows.md` → "Retrieval Workflow" section
2. `components.md` → "RetrieverNode" section
3. `data_models.md` → "RetrievalResult" section
4. `interfaces.md` → "ChromaDB Interface" section

**Answer Strategy**: Start with workflow, then component logic, then data structures, then integration.

## File Summaries

### codebase_info.md

**Purpose**: Basic codebase information and structure

**Key Content**:
- Project overview and characteristics
- Technology stack
- Project structure (directory tree)
- File counts and entry points
- Configuration overview
- Data storage locations

**Best For**: Getting started, understanding project structure, finding entry points

### architecture.md

**Purpose**: System architecture and design patterns

**Key Content**:
- High-level architecture diagrams
- Agent flow and responsibilities
- Component descriptions
- Design decisions and rationale
- Error handling strategy
- Performance considerations
- Security considerations

**Best For**: Understanding system design, architecture patterns, design rationale

### components.md

**Purpose**: Detailed component descriptions

**Key Content**:
- Component hierarchy
- Core component descriptions
- Node interfaces and responsibilities
- Agent factory details
- Chunking module details
- Database module details
- Utilities module details
- Component interactions

**Best For**: Understanding specific components, their responsibilities, how they interact

### interfaces.md

**Purpose**: APIs, interfaces, and integration points

**Key Content**:
- Public APIs (CLI, Graph, Chunking, ChromaDB, Git)
- Data models (Chunk, RetrievalResult, RepoInfo, FilesResponse)
- Node interfaces and state requirements
- Agent interfaces
- Integration points (ChromaDB, Strands, Environment)
- Error handling
- Extension points

**Best For**: Using APIs, integrating components, extending the system

### data_models.md

**Purpose**: Data structures and models

**Key Content**:
- Pydantic models (Chunk, RetrievalResult, RepoInfo, FilesResponse)
- Dataclasses (IndexingRun)
- Internal data structures (Invocation State, Node Result State)
- Data flow diagrams
- Validation rules
- Serialization details
- Constants

**Best For**: Understanding data structures, model fields, data flow, validation

### workflows.md

**Purpose**: Processes and workflows

**Key Content**:
- Main workflow: Query execution
- Targeted indexing workflow
- Chunking workflow
- Retrieval workflow
- Synthesis workflow
- Error handling workflow
- Collection management workflow
- Progress indication workflow
- Configuration workflow
- Testing workflow

**Best For**: Understanding processes, execution flows, step sequences

### dependencies.md

**Purpose**: External dependencies

**Key Content**:
- Core dependencies (strands-agents, chromadb, tiktoken, etc.)
- Development dependencies (pytest, pytest-mock)
- Dependency relationships
- Dependency management
- API key dependencies
- Platform dependencies
- Optional dependencies
- Security considerations

**Best For**: Understanding dependencies, their purposes, usage patterns, version info

## Additional Resources

### External Documentation

- **README.md**: User-facing documentation
- **ARCHITECTURE.md**: Architecture documentation (may overlap with `.sop/summary/architecture.md`)
- **AGENTS.md**: AI assistant guide (consolidated documentation)

### Codebase Locations

- **Source Code**: `src/` directory
- **Tests**: `tests/` directory
- **Examples**: `examples/` directory
- **Configuration**: `requirements.txt`, `.env` (if present)

## Notes for AI Assistants

1. **Always check this index first** when answering questions about the codebase
2. **Use metadata tags** to quickly identify relevant files
3. **Cross-reference files** when topics span multiple documents
4. **Update documentation** when making significant changes to the codebase
5. **Maintain consistency** across documentation files when updating

## Version Information

- **Documentation Version**: 1.0
- **Last Updated**: Generated during codebase summary
- **Codebase**: ASKII
- **Language**: Python 3.8+

