## Manual Run Guide

This guide shows how to manually generate and send the daily report using a mock recipient to avoid spamming real inboxes.

### Prerequisites

- Python venv set up and activated
- `.env` configured (see `docs/env_setup.md`)
- Ensure these variables exist in your environment or `.env`:
  - `SENDER_EMAIL`, `GMAIL_APP_PASSWORD`
  - `RECEIVER_EMAIL` (real recipient but will be overridden in mock runs)
  - `MOCK_RECEIVER_EMAIL` (mock/inbox for tests)
  - `DEV1_NAME_FRONTEND`, `DEV2_NAME_FRONTEND`, `DEV1_NAME_BACKEND`, `DEV2_NAME_BACKEND`
  - Optional GitHub mapping (for attribution): `DEV1_GH_FRONTEND`, `DEV2_GH_FRONTEND`, `DEV1_GH_BACKEND`, `DEV2_GH_BACKEND`

### 1) Dry-run HTML (no email sent)

```bash
source venv/bin/activate
python - <<'PY'
from jogaliga_daily_report_mailer import render_daily_report_dry_run
print(render_daily_report_dry_run())
PY
```

Use this to preview structure and styling without querying APIs or sending email.

### 2) Manual mock email run

Send the real report email layout to your mock inbox.

```bash
export MANUAL_MOCK=True
export MOCK_RECEIVER_EMAIL=you@example.com
python jogaliga_daily_report_mailer.py
```

Notes:
- When `MANUAL_MOCK=True` and `MOCK_RECEIVER_EMAIL` is set, the script overrides all recipients and sends only to the mock address.
- If `MANUAL_MOCK` is not set but `MOCK_MODE` is set and `MOCK_RECEIVER_EMAIL` is present, it also uses the mock recipient.

### 3) Disable mock and send to real recipients (be careful)

```bash
unset MANUAL_MOCK
python jogaliga_daily_report_mailer.py
```

This will send to `RECEIVER_EMAIL` plus repo-specific recipients (e.g., `JESREAL_EMAIL`, `HANS_EMAIL`) if configured.

### 4) Troubleshooting

- No email received: verify `SENDER_EMAIL`/`GMAIL_APP_PASSWORD` and that your SMTP account allows app passwords.
- Mock override not working: ensure `MANUAL_MOCK=True` (any non-"False" value) and `MOCK_RECEIVER_EMAIL` is non-empty.
- Time window: the script uses Asia/Manila previous calendar day for GitHub data and Sheets.
- GitHub/API errors: confirm `GITHUB_TOKEN` scope and rate limits.



