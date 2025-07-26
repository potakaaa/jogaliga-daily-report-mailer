# Jogaliga Daily Report Mailer

This script automatically generates and sends daily reports for the Jogaliga frontend and backend teams.

## One-Click Running Options

### Option 1: Spotlight Search (Recommended)
- Press `Cmd + Space` to open Spotlight
- Type "Jogaliga Daily Report" 
- Press Enter to run the application
- This will open a new Terminal window and run the script with full logging

### Option 2: Double-click from Finder
- Navigate to your project folder in Finder
- Double-click `run_report.command`
- This will open Terminal and run the script with full logging

### Option 3: Applications Folder
- Open Finder
- Go to Applications folder
- Double-click "Jogaliga Daily Report.app"
- This will open a new Terminal window and run the script

### Option 4: Terminal Command
```bash
./run_daily_report.sh
```

## Features

- ✅ **One-click execution** - No need to manually activate virtual environment
- ✅ **Spotlight searchable** - Easily find and run from anywhere
- ✅ **Full logging** - See all output and any errors
- ✅ **Auto-close** - Terminal stays open until you press a key
- ✅ **Professional formatting** - Capitalized bullet points in emails

## Requirements

- macOS
- Python virtual environment (`venv/`)
- Properly configured `.env` file with:
  - Google Service Account credentials
  - Email credentials
  - Developer names and emails

## Troubleshooting

If the script doesn't run:
1. Make sure your virtual environment is properly set up
2. Check that your `.env` file is configured correctly
3. Verify that the Google Service Account JSON file exists
4. Ensure you have internet connection for email sending

## Logs

All logs will be displayed in the Terminal window, including:
- Virtual environment activation status
- Google Sheets data fetching
- Email sending status
- Any errors or warnings 