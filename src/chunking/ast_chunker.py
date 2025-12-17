"""AST-based chunking for Python files."""

import ast
import os
from typing import List, Optional
from src.chunking.models import Chunk
from src.chunking.token_counter import count_tokens


class FunctionClassVisitor(ast.NodeVisitor):
    """AST visitor to extract function and class definitions."""

    def __init__(self, source_lines: List[str]):
        """
        Initialize visitor with source lines.

        Args:
            source_lines: List of source code lines (for extracting text)
        """
        self.source_lines = source_lines
        self.definitions = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition nodes."""
        self._extract_definition(node, "function")
        self.generic_visit(node)  # Continue visiting children (nested functions)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition nodes."""
        self._extract_definition(node, "function")
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition nodes."""
        self._extract_definition(node, "class")
        self.generic_visit(node)  # Continue visiting children (methods)

    def _extract_definition(
        self, node: ast.AST, definition_type: str
    ) -> None:
        """
        Extract definition information from AST node.

        Args:
            node: AST node (FunctionDef, AsyncFunctionDef, or ClassDef)
            definition_type: "function" or "class"
        """
        # Get line numbers (1-based)
        start_line = node.lineno
        end_line = getattr(node, "end_lineno", None)

        # If end_lineno is not available (Python < 3.8), estimate from node
        if end_line is None:
            # Estimate end line by finding the last line of the node
            end_line = self._estimate_end_line(node)

        # Extract the source code for this definition
        # Include decorators if present
        decorator_lines = []
        if hasattr(node, "decorator_list") and node.decorator_list:
            for decorator in node.decorator_list:
                decorator_start = decorator.lineno
                decorator_end = getattr(
                    decorator, "end_lineno", decorator_start
                )
                decorator_lines.extend(
                    range(decorator_start - 1, decorator_end)
                )

        # Get the actual source code
        start_idx = start_line - 1  # Convert to 0-based index
        end_idx = end_line  # end_lineno is inclusive, so we use it directly

        # Include decorator lines before the definition
        actual_start_line = start_line
        if decorator_lines:
            min_decorator = min(decorator_lines)
            if min_decorator < start_idx:
                start_idx = min_decorator
                actual_start_line = min_decorator + 1  # Convert back to 1-based

        # Extract text (preserve original formatting)
        definition_text = "\n".join(
            self.source_lines[start_idx:end_idx]
        )

        self.definitions.append(
            {
                "type": definition_type,
                "name": node.name,
                "start_line": actual_start_line,  # Include decorator lines
                "end_line": end_line,
                "text": definition_text,
                "decorator_lines": decorator_lines,
            }
        )

    def _estimate_end_line(self, node: ast.AST) -> int:
        """
        Estimate end line for nodes without end_lineno (Python < 3.8).

        Args:
            node: AST node

        Returns:
            int: Estimated end line number
        """
        # For Python < 3.8, we need to traverse the node to find the last line
        last_line = node.lineno

        for child in ast.walk(node):
            if hasattr(child, "lineno") and child.lineno:
                last_line = max(last_line, child.lineno)
            if hasattr(child, "end_lineno") and child.end_lineno:
                last_line = max(last_line, child.end_lineno)

        return last_line


def chunk_python_file(file_path: str, source: str, repo_path: str) -> List[Chunk]:
    """
    Chunk a Python file using AST-based extraction.

    Args:
        file_path: Absolute path to the Python file
        source: Source code content of the file
        repo_path: Path to repository root (for relative paths)

    Returns:
        List[Chunk]: List of chunks extracted from the file
    """
    chunks = []

    try:
        # Parse the source code into AST
        tree = ast.parse(source, filename=file_path)

        # Split source into lines for extraction
        source_lines = source.splitlines()

        # Visit AST to extract definitions
        visitor = FunctionClassVisitor(source_lines)
        visitor.visit(tree)

        # Convert definitions to chunks
        # Note: We keep functions and classes intact as semantic units,
        # regardless of token count, to preserve semantic coherence.
        for defn in visitor.definitions:
            chunk_text = defn["text"]
            token_count = count_tokens(chunk_text)

            # Create chunk for this definition
            relative_path = os.path.relpath(file_path, repo_path)
            chunk_id = f"{relative_path}:{defn['start_line']}-{defn['end_line']}"

            chunk = Chunk(
                text=chunk_text,
                file_path=relative_path,
                line_range=f"{defn['start_line']}-{defn['end_line']}",
                symbol_name=defn["name"],
                symbol_type=defn["type"],
                token_count=token_count,
                chunk_id=chunk_id,
            )
            chunks.append(chunk)

    except SyntaxError as e:
        # Handle syntax errors gracefully
        # Log error but don't crash - return empty list
        print(f"Warning: Syntax error in {file_path} at line {e.lineno}: {e.msg}")
        return []
    except Exception as e:
        # Handle other errors
        print(f"Error processing {file_path}: {str(e)}")
        return []

    return chunks
