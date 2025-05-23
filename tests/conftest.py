"""Pytest configuration for task_runner tests"""

import sys
from pathlib import Path

# Add src directory to Python path so tests can import the package
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))
