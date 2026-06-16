#!/usr/bin/env python3
"""Convenience launcher — run The Program without installing it.

Equivalent to the installed `the-program` command. After `pip install -e .` you can
also use `the-program <command>` or `python -m the_program <command>`.

    python run.py demo
    python run.py rift
    python run.py chat
"""

from __future__ import annotations

import os
import sys

# Make the package importable when running from a source checkout.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from the_program.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
