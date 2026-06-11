"""Pytest configuration — ensures backend package is importable."""

import sys
from pathlib import Path

# Add project root to sys.path so `backend.app.*` imports resolve
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
