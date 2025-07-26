#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Run the daily report script
echo "Running Jogaliga Daily Report Mailer..."
echo "========================================"
python jogaliga_daily_report_mailer.py

# Keep terminal open to see logs
echo ""
echo "Press any key to close..."
read -n 1 -s 