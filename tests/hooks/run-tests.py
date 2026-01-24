#!/usr/bin/env python3
"""Cross-platform test runner that works with any Python executable."""
import subprocess
import sys

if __name__ == "__main__":
    sys.exit(subprocess.call([sys.executable, "-m", "pytest", "tests/integration/"]))
