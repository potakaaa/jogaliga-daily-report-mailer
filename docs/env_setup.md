## Environment Setup

Copy the following template into a local `.env` file (do not commit your real secrets). For CI (GitHub Actions), add these as repository Secrets.

```env
# GitHub
# GitHub Personal Access Token with read-only repo scope
# Create at: https://github.com/settings/tokens (classic) or create a fine-grained token with repository read access
GITHUB_TOKEN=

# Email (uses existing mailer structure)
# SENDER_EMAIL=
# SENDER_PASSWORD=
# SMTP_HOST=
# SMTP_PORT=

# Manual mock run configuration
# When MANUAL_MOCK is set (e.g., True), recipients are overridden with MOCK_RECEIVER_EMAIL
MANUAL_MOCK=False
MOCK_RECEIVER_EMAIL=

# Google Sheets (existing setup assumed)
# Path to your service account JSON (if needed by local runs)
# GOOGLE_SERVICE_ACCOUNT_JSON=./jogaliga-daily-report-credentials.json
# Target Google Sheet ID
# SHEET_ID=
```

Notes:
- Keep `.env` out of version control. Use `.gitignore` and CI Secrets.
- `GITHUB_TOKEN` is required to read PRs/issues for `jogaliga/frontend` and `jogaliga/backend`.
- For GitHub Actions, set `GITHUB_TOKEN`, email creds, and Sheets creds in the repository settings → Secrets and variables → Actions.

