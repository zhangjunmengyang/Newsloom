#!/usr/bin/env python3
"""Entry point for Newsloom v2 pipeline"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from pipeline_v2 import main

if __name__ == '__main__':
    main()
