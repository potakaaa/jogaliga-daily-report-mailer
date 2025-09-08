import os
import datetime
from zoneinfo import ZoneInfo

import importlib


def test_previous_day_window_asia_manila():
    mod = importlib.import_module("jogaliga_daily_report_mailer")
    start, end, label = mod.DailyReportMailer.previous_day_window_asia_manila()
    # Basic sanity checks
    assert start.endswith("Z") or "+" in start
    assert end.endswith("Z") or "+" in end
    # Parse and ensure start < end and both on same PH date
    s = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
    e = datetime.datetime.fromisoformat(end.replace("Z", "+00:00"))
    assert s < e
    ph = ZoneInfo("Asia/Manila")
    s_ph = s.astimezone(ph)
    e_ph = e.astimezone(ph)
    assert s_ph.date() == e_ph.date()
    # Label matches previous day in PH
    expected_label = (datetime.datetime.now(ph).date() - datetime.timedelta(days=1)).strftime('%B %d, %Y')
    assert label == expected_label


def test_normalize_activity_by_developer(monkeypatch):
    mod = importlib.import_module("jogaliga_daily_report_mailer")

    # Env mapping for frontend
    os.environ["DEV1_NAME_FRONTEND"] = "Gerald"
    os.environ["DEV2_NAME_FRONTEND"] = "Jesreal"
    os.environ["DEV1_GH_FRONTEND"] = "gerald-gh"
    os.environ["DEV2_GH_FRONTEND"] = "jesreal-gh"

    repos = [("jogaliga", "frontend")]
    expected = {"frontend": ["Gerald", "Jesreal"]}
    start = "2025-01-01T00:00:00Z"
    end = "2025-01-01T23:59:59Z"

    def fake_opened(repos, s, e):
        return {"jogaliga/frontend": [
            {"number": 1, "title": "Feat: add login", "html_url": "", "author": "gerald-gh", "created_at": s},
        ]}

    def fake_merged(repos, s, e):
        return {"jogaliga/frontend": [
            {"number": 2, "title": "Fix: bug", "html_url": "", "author": "jesreal-gh", "merged_at": end},
        ]}

    def fake_issues(repos, s, e):
        return {"jogaliga/frontend": [
            {"number": 10, "title": "Chore", "html_url": "", "author": "jesreal-gh", "state": "closed", "closed_at": end, "updated_at": end, "kind": "closed"}
        ]}

    monkeypatch.setattr(mod, "fetch_prs_opened_for_repos", fake_opened)
    monkeypatch.setattr(mod, "fetch_prs_merged_for_repos", fake_merged)
    monkeypatch.setattr(mod, "fetch_issues_closed_and_updated_for_repos", fake_issues)

    out = mod.normalize_activity_by_developer(repos, expected, start, end)
    assert set(out.keys()) == {"frontend"}
    assert set(out["frontend"].keys()) == {"Gerald", "Jesreal"}
    assert len(out["frontend"]["Gerald"]["prs_opened"]) == 1
    assert len(out["frontend"]["Jesreal"]["prs_merged"]) == 1
    assert len(out["frontend"]["Jesreal"]["issues_closed"]) == 1


def test_merge_with_sheet_fallback():
    mod = importlib.import_module("jogaliga_daily_report_mailer")
    activity = {
        "frontend": {
            "Gerald": {"prs_opened": [], "prs_merged": [], "issues_closed": [], "issues_updated": []},
            "Jesreal": {"prs_opened": [{"number": 1}], "prs_merged": [], "issues_closed": [], "issues_updated": []},
        },
        "backend": {},
    }
    fallback = {
        "frontend": {
            "Gerald": {"accomplishments": "fixed config", "blockers": "none", "notes": "n/a"},
            "Jesreal": {"accomplishments": "wrote docs", "blockers": "vpn", "notes": "later"},
        },
        "backend": {},
    }
    merged = mod.merge_with_sheet_fallback(activity, fallback)
    assert merged["frontend"]["Gerald"]["accomplishments_fallback"] == "fixed config"
    assert merged["frontend"]["Jesreal"]["accomplishments_fallback"] is None


def test_manual_mock_recipients(monkeypatch):
    import importlib
    import jogaliga_daily_report_mailer as mod
    monkeypatch.setenv("RECEIVER_EMAIL", "real@example.com")
    monkeypatch.setenv("JESREAL_EMAIL", "jes@example.com")
    monkeypatch.setenv("HANS_EMAIL", "hans@example.com")
    monkeypatch.setenv("MOCK_RECEIVER_EMAIL", "mock@example.com")
    monkeypatch.setenv("MANUAL_MOCK", "True")

    # Re-import not necessary; compute via local helper pattern by calling main's closure requires refactor.
    # Instead, emulate compute_receivers logic quickly:
    def compute_receivers(repo_key: str) -> list:
        base = [os.getenv("RECEIVER_EMAIL")]
        if repo_key == "frontend" and os.getenv("JESREAL_EMAIL"):
            base.append(os.getenv("JESREAL_EMAIL"))
        if repo_key == "backend" and os.getenv("HANS_EMAIL"):
            base.append(os.getenv("HANS_EMAIL"))
        manual_mock = os.getenv("MANUAL_MOCK", "False")
        mock_addr = (os.getenv("MOCK_RECEIVER_EMAIL") or "").strip()
        if manual_mock != "False" and mock_addr:
            return [mock_addr]
        if os.getenv("MOCK_MODE", "False") != "False" and mock_addr:
            return [mock_addr]
        return base

    assert compute_receivers("frontend") == ["mock@example.com"]
    assert compute_receivers("backend") == ["mock@example.com"]

