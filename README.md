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
  - GitHub Personal Access Token `GITHUB_TOKEN` (read-only repo scope)

### Environment variables

- Copy `docs/.env.example` to `.env` and fill in values locally, or set them as CI secrets in GitHub Actions.
- `GITHUB_TOKEN` is required for reading PRs and issues across `jogaliga/frontend` and `jogaliga/backend`.
  - Optional:
    - `FRONTEND_REPO` (default `AppArara/jogaliga_frontend`)
    - `BACKEND_REPO` (default `AppArara/jogaliga_backend`)

### GitHub Actions setup

- Secrets to add in the repo (Settings → Secrets and variables → Actions):
  - `GITHUB_TOKEN` — PAT with read access to both repos
  - `SENDER_EMAIL`, `GMAIL_APP_PASSWORD`, `RECEIVER_EMAIL` — for email sending
  - `GOOGLE_SERVICE_ACCOUNT_JSON` — contents of your service account JSON
- The workflow `.github/workflows/daily-report.yml` runs daily at 23:59 Asia/Manila.
- You can also trigger it manually via the Actions tab (workflow_dispatch).

### Manual run (local)

```bash
source venv/bin/activate
python - <<'PY'
from jogaliga_daily_report_mailer import render_daily_report_dry_run
print(render_daily_report_dry_run())
PY
```

Manual mock email run:

```bash
export MANUAL_MOCK=True
export MOCK_RECEIVER_EMAIL=you@example.com
python jogaliga_daily_report_mailer.py
```

See `docs/manual_run.md` for a complete manual run guide.

### Troubleshooting

- Ensure the service account has access to the target Google Sheet.
- Check rate limits for GitHub API if results look incomplete.
- No secrets are printed in logs by design; verify env is loaded if values seem missing.

### Future enhancement

- Optional `--since YYYY-MM-DD` flag for backfilling a previous date range.

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