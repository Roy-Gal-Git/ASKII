# Examples

This directory contains example queries and usage patterns for the CLI Repo Analyst Tool.

## Files

- `example_queries.md`: Sample questions and expected answer formats

## Usage Examples

### Basic Query

```bash
# Query the current directory
python app.py "How does the code handle timeouts?"
```

### Query Specific Repository

```bash
# Query a specific repository
python app.py "What is the main entry point?" --repository-path /path/to/repo
```

### Force Reindexing

```bash
# Force reindexing before querying
python app.py "Explain the authentication flow" --force-reindex
```

## Common Use Cases

### Understanding Functions

Ask about specific functions to understand their implementation:

```bash
python app.py "How does the calculate_average function work?"
```

### Class Overview

Get an overview of a class and its methods:

```bash
python app.py "What does the Calculator class do?"
```

### Configuration Questions

Ask about configuration and settings:

```bash
python app.py "What are the default timeout settings?"
```

### Architecture Questions

Understand the overall structure:

```bash
python app.py "How is the codebase organized?"
```

### Error Handling

Learn about error handling strategies:

```bash
python app.py "How does the code handle errors?"
```

## Tips for Better Results

1. **Be Specific**: More specific questions yield better results
   - Good: "How does the add function handle negative numbers?"
   - Less effective: "Tell me about the code"

2. **Use Function/Class Names**: Including specific names helps retrieval
   - Good: "What does the Calculator class do?"
   - Less effective: "What does the class do?"

3. **Ask About Patterns**: Questions about patterns work well
   - Good: "How are timeouts configured?"
   - Good: "What error handling patterns are used?"

4. **Rephrase if Needed**: If you don't get good results, try rephrasing
   - Original: "How does it work?"
   - Rephrased: "What is the main entry point and how does it initialize?"

## Expected Answer Format

All answers include:
- Plain text format (no markdown in output)
- Inline citations: `[file.py:line-range]` (square brackets for better visual distinction)
- Grounded in retrieved code
- Concise and focused

Answers may include:
- Code snippets (when relevant)
- Line-by-line explanations (for complex logic)
- Limitations or uncertainties (when evidence is weak)
