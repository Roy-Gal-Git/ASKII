"""Main CLI entry point."""

import argparse
import asyncio
import os
import sys

from src.agents.graphs import build_rag_loop_graph, get_node_actions
from src.agents.factories import Synthesizer
from src.cli.progress import SpinnerUI
from src.db.chroma import client
from src.db.embedding import GeminiEmbeddingFunction
from src.utils.git_utils import get_repo_info


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="CLI Repo Analyst Tool - Answer questions about codebases using RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "How does the code handle timeouts?"
  %(prog)s "What is the main entry point?" --repository-path /path/to/repo
  %(prog)s "Explain the authentication flow" --reset-index
        """,
    )
    parser.add_argument(
        "question",
        type=str,
        nargs="?",
        default=None,
        help="Natural language question about the codebase (optional if only indexing)",
    )
    parser.add_argument(
        "--repository-path",
        type=str,
        default=None,
        help="Path to repository (defaults to current directory)",
    )
    parser.add_argument(
        "--reset-index",
        action="store_true",
        help="Delete the existing index for this repository before querying",
    )
    return parser.parse_args()


async def _run_graph_with_streaming(*, graph: object, question: str, invocation_state: dict[str, object]) -> None:
    """Run the Strands graph via stream_async and stream Synthesizer output.

    Spinner behavior:
    - Show spinner during node execution
    - Update spinner text on node start
    - Print per-node completion lines on node stop
    - Stop spinner when Synthesizer begins streaming its final output
    """

    node_actions = get_node_actions()
    ui = SpinnerUI.start(node_actions=node_actions, text="Thinking")

    synth_stream_started = False
    try:
        async for event in graph.stream_async(question, invocation_state=invocation_state):
            event_type = event.get("type")
            if event_type == "multiagent_node_start":
                node_id = event.get("node_id")

                if isinstance(node_id, str) and node_id:
                    ui.set_node(node_id=node_id)

            elif event_type == "multiagent_node_stream":
                node_id = event.get("node_id")
                if node_id != Synthesizer.NAME:
                    continue

                inner_event = event.get("event")
                if not isinstance(inner_event, dict):
                    continue

                data = inner_event.get("data")
                if not isinstance(data, str) or not data:
                    continue

                if not synth_stream_started:
                    ui.stop()
                    synth_stream_started = True

                print(data, end="", flush=True)
    finally:
        print()  # new line
        ui.stop()


def main() -> None:
    """Main entry point for CLI."""
    try:
        args = parse_args()

        # Validate question if provided
        if args.question and not args.question.strip():
            print("Error: Question cannot be empty.", file=sys.stderr)
            sys.exit(1)

        # Get repository path (default to current directory)
        repo_path = os.path.abspath(args.repository_path or os.getcwd())

        # Validate repository once
        try:
            repo_info = get_repo_info(repo_path)
        except ValueError as e:
            print(f"Error: {str(e)}\nPlease provide a valid path to a git repository.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: Failed to extract repository information: {str(e)}", file=sys.stderr)
            sys.exit(1)

        # If no question, we're done (just setup)
        if not args.question or not args.question.strip():
            return

        embedding_function = GeminiEmbeddingFunction()

        # Reset index if requested (delete collection for this repo)
        if getattr(args, "reset_index", False):
            try:
                client.delete_collection(repo_info.collection_name)
            except Exception as e:
                print(f"Error: Failed to reset index: {str(e)}", file=sys.stderr)
                sys.exit(1)

        # Open/create collection handle (Indexer/Retriever nodes do add/query)
        try:
            collection = client.get_or_create_collection(
                name=repo_info.collection_name,
                embedding_function=embedding_function,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            print(f"Error: Failed to access collection: {str(e)}", file=sys.stderr)
            sys.exit(1)

        # Execute Strands graph
        try:
            graph = build_rag_loop_graph(repo_path=repo_path)
            invocation_state = {
                "repo_path": repo_path,
                "repo_name": repo_info.name,
                "collection": collection,
                "question": args.question,
                "attempts": 0,
                "already_indexed": set(),
            }
            asyncio.run(
                _run_graph_with_streaming(
                    graph=graph,
                    question=args.question,
                    invocation_state=invocation_state,
                )
            )

        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: An unexpected error occurred: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
