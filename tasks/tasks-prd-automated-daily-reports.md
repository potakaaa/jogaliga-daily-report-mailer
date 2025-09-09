## Relevant Files

- `jogaliga_daily_report_mailer.py` - Core mailer; integrate GitHub API fetch and Sheets fallback.
- `.github/workflows/daily-report.yml` - Scheduled workflow to run report at 11:59 PM Asia/Manila.
- `README.md` - Add setup docs for tokens, schedule, and workflow usage.
- `.env.example` - Document required env vars: `GITHUB_TOKEN`, email creds, sheet IDs.
  - Note: If root `.env.example` cannot be added, use `docs/.env.example` instead.
 - `docs/.env.example` - Template env file to copy to `.env` locally or CI secrets.
 - `docs/env_setup.md` - Environment variable template and setup steps.
- `scripts/validate-config.py` (optional) - Validate required env/config at startup.
- `email_templates/daily_report.html` (optional) - Rich HTML template for the email body.
- `github_integration.py` (optional) - Functions to query PRs/issues for repos and time window.
- `sheets_fallback.py` (optional) - Functions to read accomplishments/blockers/notes from Google Sheets.
- `report_builder.py` (optional) - Compose per-developer sections and final HTML/text content.

### Notes

- Use Asia/Manila timezone to compute the previous calendar day window.
- Prefer GH activity; if none per developer, use Sheet; if none, output "No updates".
- Exclude commit data; rely on PRs and Issues only.

## Tasks

- [ ] 1.0 Add GitHub data collection (PRs/issues) for selected repos and window
  - [x] 1.1 Add `GITHUB_TOKEN` to `.env.example` with read-only scope guidance
  - [x] 1.2 Implement previous-day window calculation in Asia/Manila timezone
  - [x] 1.3 Fetch PRs opened in window for `jogaliga/frontend` and `jogaliga/backend`
  - [x] 1.4 Fetch PRs merged in window for both repos
  - [x] 1.5 Fetch PR reviews/comments in window (if available via API)
  - [x] 1.6 Fetch issues closed and issues updated/worked on in window
  - [x] 1.7 Normalize fetched items and group by developer using existing mapping logic
  - [x] 1.8 Ensure commits are excluded from data sources
  - [x] 1.9 Add basic unit tests for time-window computation and normalization

- [ ] 2.0 Implement Google Sheets fallback for per-developer updates
  - [x] 2.1 Read existing spreadsheet using current service account setup
  - [x] 2.2 Parse tabs: Today’s Accomplishments, Blockers, Notes
  - [x] 2.3 Filter rows by target date (previous calendar day, Asia/Manila)
  - [x] 2.4 Map sheet rows to developers using existing identity logic
  - [x] 2.5 On conflict (GH + Sheet), prefer GitHub-only (do not merge)
  - [x] 2.6 Add unit tests for sheet parsing and conflict preference

- [ ] 3.0 Update HTML email template and assembly logic to new sections
  - [x] 3.1 Create/extend HTML template with sections: Header, Per-developer, PRs, Issues, Blockers, Notes
  - [x] 3.2 Omit “Tomorrow Plan” section
  - [x] 3.3 Assemble per-developer sections from GH data or Sheet fallback
  - [x] 3.4 Insert explicit "No updates" when both sources are empty
  - [x] 3.5 Ensure recipients restriction via existing configuration
  - [x] 3.6 Send error email to maintainers on failure
  - [x] 3.7 Add smoke test/dry-run renderer for template (optional)

- [ ] 4.0 Add GitHub Actions workflow to run daily at 11:59 PM Asia/Manila
  - [x] 4.1 Create `.github/workflows/daily-report.yml`
  - [x] 4.2 Set cron to `59 15 * * *` (15:59 UTC = 23:59 Asia/Manila)
  - [x] 4.3 Configure Python setup and dependencies installation
  - [x] 4.4 Provide secrets: `GITHUB_TOKEN`, email creds, sheet creds via repo secrets
  - [x] 4.5 Run the report script entrypoint (dry-run render step included)
  - [x] 4.6 On failure: upload logs as artifacts and trigger error email (implicit via job logs)

- [ ] 5.0 Add configuration, docs, and minimal observability (error email)
  - [x] 5.1 Update `README.md` with setup, scheduling, and troubleshooting
  - [x] 5.2 Populate `.env.example` with all required keys/IDs
  - [x] 5.3 Add structured logging with clear start/end and section markers
  - [x] 5.4 Mask secrets in logs; avoid printing tokens or creds
  - [x] 5.5 Document manual run instructions and future `--since` backfill flag

- [ ] 6.0 Add manual run using `MOCK_RECEIVER_EMAIL`
  - [x] 6.1 Read `MOCK_RECEIVER_EMAIL` from `.env`
  - [x] 6.2 Add a CLI flag or env switch to force mock recipients
  - [x] 6.3 Override recipients with `MOCK_RECEIVER_EMAIL` for manual runs
  - [x] 6.4 Update `README.md` with manual mock run instructions
  - [x] 6.5 Add a small test ensuring override behavior

