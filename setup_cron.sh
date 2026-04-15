#!/bin/bash
# setup_cron.sh — adds a cron job for Linux/macOS
# Run: bash setup_cron.sh

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_EXE="$(which python3)"
CRON_CMD="0 18 * * * cd \"$PROJECT_DIR\" && $PYTHON_EXE runner.py >> \"$PROJECT_DIR/cron.log\" 2>&1"

echo ""
echo "  Adding cron job:"
echo "  $CRON_CMD"
echo ""

# Add to crontab (avoiding duplicates)
(crontab -l 2>/dev/null | grep -v "runner.py"; echo "$CRON_CMD") | crontab -

echo "  ✦ Cron job added! Runs every day at 6 PM."
echo "  ✦ Logs → $PROJECT_DIR/cron.log"
echo ""
echo "  To test immediately (no delay):"
echo "    python3 runner.py --no-delay"
echo ""
