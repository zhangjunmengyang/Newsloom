#!/usr/bin/env python3
"""Entry point for the pipeline"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import and run
from pipeline import main

if __name__ == '__main__':
    main()
