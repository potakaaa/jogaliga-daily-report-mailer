## Automated Daily Reports (GitHub + Google Sheets Fallback)

### 1. Introduction/Overview
Automate daily progress reports using GitHub activity as the primary data source and a Google Sheets fallback for manual entries when there are no PR updates. The goal is to provide consistent, hands-free daily visibility for Dan while reducing manual report creation.

### 2. Goals
- Provide a daily summary of work across `jogaliga/frontend` and `jogaliga/backend`.
- Use PR titles/descriptions and issues activity as the canonical source; exclude commit-level data.
- Fallback to a shared Google Sheet for developer-entered accomplishments, blockers, and notes when GitHub activity is absent per developer.
- Deliver a styled HTML email nightly at 11:59 PM Asia/Manila.
- Run automatically via GitHub Actions; version-controlled scripts and workflow.

### 3. User Stories
- As Dan, I receive a daily email summarizing the team’s progress without asking for manual updates.
- As a developer, I can log accomplishments, blockers, and notes in the spreadsheet if I didn’t open/merge/review PRs or update issues that day.
- As a maintainer, I can adjust configuration via env variables without changing code.

### 4. Functional Requirements
1. Repositories: Include `jogaliga/frontend` and `jogaliga/backend`.
2. Time window: Calendar previous day 00:00–23:59 in Asia/Manila.
3. Data sources (GitHub primary):
   - PRs opened (title + first line of body).
   - PRs merged (title + first line of body).
   - PRs reviewed (reviews/comments where available).
   - Issues closed and issues updated/worked on.
   - Exclude commits as a data source.
4. Detail level: Use title + first line of body; include linked issues/labels where easily derivable from the PR/issue payloads.
5. AI summarization: None; deterministic formatting (configurable later).
6. Email delivery: Use existing repo email structure (current SMTP/yagmail setup). Recipients follow current configuration.
7. Scheduling: Daily at 11:59 PM Asia/Manila via GitHub Actions if available; otherwise compatible with local execution.
8. Authentication: GitHub Personal Access Token via env `GITHUB_TOKEN` with read scopes.
9. Spreadsheet fallback (when a developer has no GitHub activity):
   - Use the existing Google Sheet already wired in the repo.
   - Read from the following worksheet tabs if present:
     i) Today’s Accomplishments
     ii) Blockers
     iii) Notes
   - If both GitHub and Sheet have entries for the same developer on the same day, prefer GitHub-only (do not merge).
10. Developer identity: Use existing matching logic in the repo to map contributors to developers.
11. Email sections (enabled):
   - Header (date, repos, timeframe)
   - Per-developer summary
   - PRs: opened/merged/reviewed
   - Issues: closed/updated
   - Blockers
   - Notes
   - Omit Tomorrow Plan.
12. No-activity behavior:
   - If no GitHub activity for a developer, attempt to fetch that developer’s row(s) from the Sheet.
   - If Sheet has no entries as well, include an explicit “No updates.”
13. Error handling: On failure, send an error email to maintainers.
14. Configuration: Use `.env` for tokens and runtime options.
15. Version control: Add GitHub Actions workflow `.github/workflows/daily-report.yml` and README setup instructions.
16. Permissions/Security: Restrict recipient list to approved addresses; mask secrets in logs as feasible.
17. Backfill: Start from next run; optionally support `--since YYYY-MM-DD` manual flag (future enhancement).
18. Language/Runtime: Python, reusing existing repo libraries/utilities.

### 5. Non-Goals (Out of Scope)
- Commit-level analysis or heuristics beyond PRs/issues.
- Tomorrow Plan section (explicitly omitted for now).
- Complex AI summarization beyond deterministic formatting.
- Building dashboards; email-only output for this iteration.

### 6. Design Considerations (Optional)
- Leverage existing email sender and Google Sheets integration already present in the repository to minimize changes.
- HTML email template with section badges and clear grouping by developer.

### 7. Technical Considerations (Optional)
- Timezone handling must use Asia/Manila for determining the previous calendar day.
- GitHub Actions runners are free for public repos; for private repos, usage is subject to plan limits. This workflow should be lightweight (API reads + email send).
- Ensure graceful handling when GitHub API rate limits are encountered (retry/backoff).

### 8. Success Metrics
- Daily email sent at expected time (>95% reliability).
- Report content matches PRs/issues and spreadsheet entries as per rules.
- Reduced manual report creation time to near-zero.

### 9. Open Questions
- Should PR reviews be summarized by reviewer or grouped under the PR item only?
- Confirm exact recipients and from-name for the email header (use current config until specified).


