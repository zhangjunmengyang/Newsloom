#!/bin/bash
# Newsloom runner - activates conda env and runs pipeline v2
set -e

# Ensure conda is in PATH (needed for cron/non-interactive shells)
export PATH="/opt/homebrew/bin:$PATH"

# Conda activation
eval "$(/opt/homebrew/bin/conda shell.bash hook)"
conda activate newsloom

# Set environment variables
export ANTHROPIC_API_KEY="cr_07d471a61fa7a471003df012202ea71cca9fa87527fec0c23b1ffd22a613f30e"
export ANTHROPIC_BASE_URL="http://155.138.214.61:3000/api"

# Proxy for Reddit and other sources that need it
export https_proxy="http://127.0.0.1:7897"
export http_proxy="http://127.0.0.1:7897"

# Run pipeline v2 with global timeout (10 minutes)
# Uses gtimeout (GNU coreutils) if available, otherwise relies on Python-level signal timeout
cd /Users/peterzhang/project/newsloom/src
if command -v gtimeout &>/dev/null; then
    gtimeout 600 python pipeline_v2.py "$@"
elif command -v timeout &>/dev/null; then
    timeout 600 python pipeline_v2.py "$@"
else
    # Fallback: background + wait with shell timeout
    python pipeline_v2.py "$@" &
    PID=$!
    ( sleep 600 && kill -TERM $PID 2>/dev/null ) &
    WATCHDOG=$!
    wait $PID 2>/dev/null
    EXIT_CODE=$?
    kill $WATCHDOG 2>/dev/null
    wait $WATCHDOG 2>/dev/null
    exit $EXIT_CODE
fi
