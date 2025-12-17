#!/usr/bin/env python3
"""Entry point for CLI Repo Analyst Tool."""

from dotenv import load_dotenv
import os

# Load environment variables from .env file as early as possible so downstream
# Gemini/Chroma components can rely on env vars without passing client args.
try:
    # In some sandboxes/CI environments, `.env` may be unreadable (permission-restricted
    # or excluded). Treat it as optional and fall back to system env vars.
    load_dotenv()
except (OSError, PermissionError):
    pass

# Ensure Strands runs in non-interactive mode for CLI flows
os.environ.setdefault("STRANDS_NON_INTERACTIVE", "true")

from src.cli.main import main as cli_main


def main() -> None:
    """Main entry point for the askii command."""
    cli_main()


if __name__ == "__main__":
    main()
