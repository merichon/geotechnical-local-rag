"""Shared stdio/logging setup for the RAG assistant.

Importing this module is enough to make console output safe: Windows consoles
default to a locale codepage (cp1254 here) that cannot encode characters like
"✓" or "İ", which used to crash the pipeline mid-run. Reconfiguring stdio to
UTF-8 at import time means every entry point (CLI, ingest, Streamlit, tests)
gets the fix without having to remember to ask for it.

Entry points additionally call configure_logging() once, which sets the root
log level from the LOG_LEVEL variable in .env.
"""

import logging
import os
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        # Not a real text stream (pytest capture, pipes) — nothing to fix.
        pass


def configure_logging() -> None:
    """Initialise root logging from LOG_LEVEL. Safe to call more than once."""
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(message)s",
    )
