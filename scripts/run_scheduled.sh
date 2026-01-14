#!/bin/bash
#
# Home Search - Scheduled Runner
# This script is called by launchd/cron to run the daily search job
#

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Add Python packages to PATH
export PATH="$PATH:/Users/sunil/Library/Python/3.9/bin"

# Set up logging
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/scheduled_$(date +%Y-%m-%d).log"

# Log start
echo "========================================" >> "$LOG_FILE"
echo "Scheduled run started: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Run the scheduled job
python3 -m src.scheduler.runner \
    --location "LB Nagar" \
    --max-videos 10 \
    >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

# Log completion
echo "========================================" >> "$LOG_FILE"
echo "Scheduled run completed: $(date)" >> "$LOG_FILE"
echo "Exit code: $EXIT_CODE" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

exit $EXIT_CODE
