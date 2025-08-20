"""Pytest configuration to ensure the package is importable during tests."""

import sys
from pathlib import Path

# Add repository root to sys.path so tests can import gitshelves without installation
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
