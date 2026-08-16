"""
conftest.py
-----------
Shared pytest configuration.

Adds the project root to sys.path so `import env.*`, `import config.*`,
etc. resolve regardless of where pytest is invoked from. This replaces
the per-file sys.path.append() boilerplate that used to live at the
top of every test_*.py file.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))