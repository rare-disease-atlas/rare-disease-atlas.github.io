"""CLI entrypoint for `python3 -m orphan_disease_mcp`."""

from .server import main

if __name__ == "__main__":
    raise SystemExit(main())
