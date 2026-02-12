#!/bin/bash
# Newsloom runner - activates conda env and runs pipeline
set -e

# Conda activation
eval "$(conda shell.bash hook)"
conda activate newsloom

# Set environment variables
export ANTHROPIC_API_KEY="cr_07d471a61fa7a471003df012202ea71cca9fa87527fec0c23b1ffd22a613f30e"
export ANTHROPIC_BASE_URL="http://155.138.214.61:3000/api"

# Run pipeline
cd /Users/peterzhang/project/newsloom/src
python pipeline.py "$@"
