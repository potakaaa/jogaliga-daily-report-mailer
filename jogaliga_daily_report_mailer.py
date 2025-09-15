import yagmail, datetime, os, dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from zoneinfo import ZoneInfo
import gspread
from google.oauth2.service_account import Credentials
from collections import defaultdict

SPREADSHEET_ID = '1wjbi6vxm2dZMHG2xvLCsTJW3rTJ206y2tXIAMHvam0M'


class DailyReportMailer:
    def __init__(self, repo: str, sender: str, receiver: str, app_password: str):
        self.repo = repo
        self.sender = sender
        self.receiver = receiver
        self.app_password = app_password
        self.today = datetime.date.today().strftime('%B %d, %Y')
        self.developer = []
        
        # Frontend has three developers (Gerald, Jesreal & Erick). Backend has two developers (Gerald & Hans).
        if repo == "frontend":
            self.developer.append(os.getenv("DEV1_NAME_FRONTEND"))  # Gerald
            self.developer.append(os.getenv("DEV2_NAME_FRONTEND"))  # Jesreal
            self.developer.append(os.getenv("DEV3_NAME_FRONTEND"))  # Erick
        elif repo == "backend":
            self.developer.append(os.getenv("DEV1_NAME_BACKEND"))  # Gerald
            self.developer.append(os.getenv("DEV2_NAME_BACKEND"))  # Hans
        else:
            raise ValueError("Invalid repo")

    def format_bullet_points(self, text: str) -> str:
        """Convert text into HTML bullets splitting on commas or newlines."""
        if not text:
            return "None"
        if '•' in text:
            return text.replace('\n', '<br>')
        # Split by comma or newline
        raw = []
        for part in text.split('\n'):
            raw.extend(part.split(','))
        items = [p.strip() for p in raw if p and p.strip()]
        if not items:
            return "None"
        return "<br>".join([f"• {item}" for item in items])

    @staticmethod
    def previous_day_window_asia_manila() -> tuple:
        """Return (start_iso_utc, end_iso_utc, label_date) for the previous calendar day in Asia/Manila.

        - start/end returned as ISO8601 UTC timestamps suitable for GitHub API query parameters.
        - label_date returned as a human-readable date string in Asia/Manila.
        """
        tz = ZoneInfo("Asia/Manila")
        now_ph = datetime.datetime.now(tz)
        prev_day = (now_ph.date() - datetime.timedelta(days=1))
        start_ph = datetime.datetime.combine(prev_day, datetime.time(0, 0, 0), tzinfo=tz)
        end_ph = datetime.datetime.combine(prev_day, datetime.time(23, 59, 59), tzinfo=tz)
        # Truncate to seconds and append Z to satisfy GitHub Search API
        start_utc_dt = start_ph.astimezone(ZoneInfo("UTC"))
        end_utc_dt = end_ph.astimezone(ZoneInfo("UTC"))
        start_utc = start_utc_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_utc = end_utc_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        label_date = prev_day.strftime('%B %d, %Y')
        return start_utc, end_utc, label_date

    @staticmethod
    def today_window_asia_manila() -> tuple:
        """Return (start_iso_utc, end_iso_utc, label_date) for the current calendar day in Asia/Manila.

        - Matches activities for "today" when the script runs, e.g., 11:59 PM still uses today's date.
        - start/end returned as ISO8601 UTC timestamps suitable for GitHub API query parameters.
        - label_date returned as a human-readable date string in Asia/Manila.
        """
        tz = ZoneInfo("Asia/Manila")
        now_ph = datetime.datetime.now(tz)
        curr_day = now_ph.date()
        start_ph = datetime.datetime.combine(curr_day, datetime.time(0, 0, 0), tzinfo=tz)
        end_ph = datetime.datetime.combine(curr_day, datetime.time(23, 59, 59), tzinfo=tz)
        start_utc_dt = start_ph.astimezone(ZoneInfo("UTC"))
        end_utc_dt = end_ph.astimezone(ZoneInfo("UTC"))
        start_utc = start_utc_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_utc = end_utc_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        label_date = curr_day.strftime('%B %d, %Y')
        return start_utc, end_utc, label_date

    @staticmethod
    def custom_date_window_asia_manila(date_str: str) -> tuple:
        """Return (start_iso_utc, end_iso_utc, label_date) for a custom date in Asia/Manila.

        Supports multiple date formats:
        - "Sep 9" or "September 9" (current year assumed)
        - "Sep 9, 2024" or "September 9, 2024" (with year)
        - "2024-09-09" (ISO format)
        - "09/09/2024" (MM/DD/YYYY)

        - start/end returned as ISO8601 UTC timestamps suitable for GitHub API query parameters.
        - label_date returned as a human-readable date string in Asia/Manila.
        """
        tz = ZoneInfo("Asia/Manila")
        current_year = datetime.datetime.now(tz).year
        
        # Try multiple date formats
        date_formats = [
            "%b %d",           # Sep 9
            "%B %d",           # September 9
            "%b %d, %Y",       # Sep 9, 2024
            "%B %d, %Y",       # September 9, 2024
            "%Y-%m-%d",        # 2024-09-09
            "%m/%d/%Y",        # 09/09/2024
            "%d/%m/%Y",        # 09/09/2024 (alternative)
        ]
        
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.datetime.strptime(date_str.strip(), fmt).date()
                # If no year in format, use current year
                if fmt in ["%b %d", "%B %d"]:
                    parsed_date = parsed_date.replace(year=current_year)
                break
            except ValueError:
                continue
        
        if parsed_date is None:
            raise ValueError(f"Unable to parse date: {date_str}. Supported formats: 'Sep 9', 'September 9, 2024', '2024-09-09', '09/09/2024'")
        
        start_ph = datetime.datetime.combine(parsed_date, datetime.time(0, 0, 0), tzinfo=tz)
        end_ph = datetime.datetime.combine(parsed_date, datetime.time(23, 59, 59), tzinfo=tz)
        start_utc_dt = start_ph.astimezone(ZoneInfo("UTC"))
        end_utc_dt = end_ph.astimezone(ZoneInfo("UTC"))
        start_utc = start_utc_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_utc = end_utc_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        label_date = parsed_date.strftime('%B %d, %Y')
        return start_utc, end_utc, label_date

    def send_report(self, dev1_accomplishments: str = "", dev2_accomplishments: str = "", dev3_accomplishments: str = "",
                   dev1_plans: str = "", dev2_plans: str = "", dev3_plans: str = "",
                   dev1_blockers: str = "", dev2_blockers: str = "", dev3_blockers: str = "",
                   dev1_notes: str = "", dev2_notes: str = "", dev3_notes: str = "",
                   attachments: list = None):
        subject = f"DAILY REPORT FOR JOGALIGA {self.repo.upper()} [{self.today.upper()}]"
        
        # Format all the text inputs into bullet points
        dev1_acc = self.format_bullet_points(dev1_accomplishments) if dev1_accomplishments else "None"
        dev2_acc = self.format_bullet_points(dev2_accomplishments) if dev2_accomplishments else "None"
        dev1_plan = self.format_bullet_points(dev1_plans) if dev1_plans else "None"
        dev2_plan = self.format_bullet_points(dev2_plans) if dev2_plans else "None"
        dev1_block = self.format_bullet_points(dev1_blockers) if dev1_blockers else "None"
        dev2_block = self.format_bullet_points(dev2_blockers) if dev2_blockers else "None"
        dev1_note = self.format_bullet_points(dev1_notes) if dev1_notes else "None"
        dev2_note = self.format_bullet_points(dev2_notes) if dev2_notes else "None"
        
        # Handle 3rd developer data (only for frontend)
        if self.repo == "frontend":
            dev3_acc = self.format_bullet_points(dev3_accomplishments) if dev3_accomplishments else "None"
            dev3_plan = self.format_bullet_points(dev3_plans) if dev3_plans else "None"
            dev3_block = self.format_bullet_points(dev3_blockers) if dev3_blockers else "None"
            dev3_note = self.format_bullet_points(dev3_notes) if dev3_notes else "None"
        
        # Dynamically build HTML sections based on the number of developers
        dev_data = [
            {
                "name": self.developer[0],
                "acc": dev1_acc,
                "plan": dev1_plan,
                "block": dev1_block,
                "note": dev1_note,
            },
            {
                "name": self.developer[1],
                "acc": dev2_acc,
                "plan": dev2_plan,
                "block": dev2_block,
                "note": dev2_note,
            }
        ]
        
        # Add 3rd developer data for frontend
        if self.repo == "frontend":
            dev_data.append({
                "name": self.developer[2],
                "acc": dev3_acc,
                "plan": dev3_plan,
                "block": dev3_block,
                "note": dev3_note,
            })

        def build_section(title: str, key: str) -> str:
            """Return an HTML section for the given title and key."""
            html = (
                f'<h2 style="color:#27a25a;font-size:25px;margin:0 0 3px 0;padding:0;">{title}</h2>'
            )
            for item in dev_data:
                html += (
                    f'<p style="margin:0 0 5px 0;font-size:18px"><b>{item["name"]}:</b></p>'
                )
                html += (
                    f'<p style="margin:0 0 10px 20px;font-size:16px">{item[key]}</p>'
                )
            return html

        accomplishments_html = build_section("Today's Accomplishments", "acc")
        plans_html = build_section("Tomorrow's Plan", "plan")
        blockers_html = build_section("Blockers & Questions", "block")
        notes_html = build_section("Notes", "note")

        # Assemble the whole email body
        body = f'''<table width="600" cellpadding="0" cellspacing="0" border="0" style="font-family:Arial,sans-serif;margin:0;padding:0;">
<tr><td bgcolor="#27a25a" style="color:#fff;padding:30px;border-radius:15px"><h1 style="margin:0;font-size:30px;">Jogaliga {self.repo.capitalize()} Daily Report</h1><p style="margin:10px 0 0 0;font-size:18px"><b>Developer{'s' if len(self.developer) > 1 else ''}:</b> {', '.join(self.developer)}<br><b>Date:</b> {self.today}</p></td></tr>
<tr><td bgcolor="#ffffff" style="padding:10px;">
{accomplishments_html}
{plans_html}
{blockers_html}
{notes_html}
</td></tr>
<tr><td bgcolor="#f9fafb" style="padding:15px;text-align:center;font-size:12px;color:#666;">This is an automated report generated by the Jogaliga {self.repo.capitalize()} team</td></tr>
</table>'''

        yag = yagmail.SMTP(self.sender, self.app_password)
        # Prepare the email contents
        contents = [body]
        if attachments:
            contents.extend(attachments)
        yag.send(self.receiver, subject, contents)
        print("Daily report sent successfully")




def fetch_todays_reports(creds_path):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.sheet1  # Assumes first sheet is correct
    records = worksheet.get_all_records()
    today = datetime.date.today()
    todays_responses = []
    for row in records:
        ts = str(row['Timestamp'])
        try:
            # Try parsing as MM/DD/YYYY HH:MM:SS
            date_part = ts.split(' ')[0]
            month, day, year = map(int, date_part.split('/'))
            row_date = datetime.date(year, month, day)
            if row_date == today:
                todays_responses.append(row)
        except Exception as e:
            continue  # Skip rows with invalid date
    return todays_responses


def get_sheets_client(creds_path: str):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    return gspread.authorize(creds)


def open_spreadsheet(sheet_id: str, creds_path: str):
    gc = get_sheets_client(creds_path)
    return gc.open_by_key(sheet_id)


def get_worksheets_map(sh):
    """Return a mapping of worksheet title to worksheet object."""
    return {ws.title: ws for ws in sh.worksheets()}


def _first_present(row: dict, keys: list, default: str = "") -> str:
    for k in keys:
        if k in row and row[k] is not None and str(row[k]).strip() != "":
            return str(row[k])
    return default


def parse_tab_generic(ws) -> list:
    """Parse a worksheet into list of normalized dicts with date, developer, text.

    Tries multiple header variants to be robust.
    """
    records = ws.get_all_records()
    out = []
    for row in records:
        date_val = _first_present(row, ["Date", "Timestamp", "date"])
        dev_val = _first_present(row, ["Developer", "Developer Name", "Name", "Developer name"])
        text_val = _first_present(
            row,
            [
                "Text",
                "Value",
                "Accomplishments",
                "Accomplishment Today (separate items with commas)",
                "Blockers",
                "Blockers/Questions (separate items with commas)",
                "Notes",
                "Notes (separate items with commas)",
            ],
        )
        if dev_val:
            out.append({"date": str(date_val), "developer": dev_val.strip(), "text": str(text_val)})
    return out


def parse_accomplishments_tab(ws) -> list:
    return parse_tab_generic(ws)


def parse_blockers_tab(ws) -> list:
    return parse_tab_generic(ws)


def parse_notes_tab(ws) -> list:
    return parse_tab_generic(ws)


def _parse_date_to_ph_date(date_str: str) -> datetime.date:
    tz = ZoneInfo("Asia/Manila")
    # Try common formats
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y", "%Y-%m-%d"):  # flexible
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            return dt.date()
        except Exception:
            continue
    # ISO with timezone
    try:
        dt = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.astimezone(tz).date()
    except Exception:
        pass
    # Fallback: today PH
    return datetime.datetime.now(tz).date()


def filter_rows_by_previous_day_ph(rows: list) -> list:
    tz = ZoneInfo("Asia/Manila")
    prev_day = (datetime.datetime.now(tz).date() - datetime.timedelta(days=1))
    out = []
    for r in rows:
        d = _parse_date_to_ph_date(str(r.get("date", "")))
        if d == prev_day:
            out.append(r)
    return out


def filter_rows_by_date_ph(rows: list, target_date: datetime.date) -> list:
    """Return only rows whose date equals target_date in Asia/Manila."""
    out = []
    for r in rows:
        d = _parse_date_to_ph_date(str(r.get("date", "")))
        if d == target_date:
            out.append(r)
    return out


def build_sheet_fallback_by_repo_and_dev(sh, expected_devs: dict, target_date: datetime.date) -> dict:
    """Return fallback structure from sheets for target PH date.

    {repo: {developer: {accomplishments, blockers, notes}}}
    """
    ws_map = get_worksheets_map(sh)
    acc = filter_rows_by_date_ph(
        parse_accomplishments_tab(
            ws_map.get("Today’s Accomplishments")
            or ws_map.get("Today's Accomplishments")
            or ws_map.get("Accomplishments")
            or ws_map.get("Today Accomplishments")
            or sh.sheet1
        ),
        target_date,
    )
    blk = filter_rows_by_date_ph(
        parse_blockers_tab(ws_map.get("Blockers") or ws_map.get("Blockers & Questions") or sh.sheet1),
        target_date,
    )
    nts = filter_rows_by_date_ph(
        parse_notes_tab(ws_map.get("Notes") or sh.sheet1),
        target_date,
    )

    def repo_for_dev(dev_name: str) -> str:
        for repo_key, devs in expected_devs.items():
            for d in devs:
                if d and dev_name and d.strip().lower() == dev_name.strip().lower():
                    return repo_key
        return "unknown"

    out: dict = {"frontend": {}, "backend": {}}
    for row in acc:
        repo = repo_for_dev(row["developer"]) 
        if repo in ("frontend", "backend"):
            out[repo].setdefault(row["developer"], {"accomplishments": "", "blockers": "", "notes": ""})
            out[repo][row["developer"]]["accomplishments"] = row["text"]
    for row in blk:
        repo = repo_for_dev(row["developer"]) 
        if repo in ("frontend", "backend"):
            out[repo].setdefault(row["developer"], {"accomplishments": "", "blockers": "", "notes": ""})
            out[repo][row["developer"]]["blockers"] = row["text"]
    for row in nts:
        repo = repo_for_dev(row["developer"]) 
        if repo in ("frontend", "backend"):
            out[repo].setdefault(row["developer"], {"accomplishments": "", "blockers": "", "notes": ""})
            out[repo][row["developer"]]["notes"] = row["text"]
    return out


def merge_with_sheet_fallback(activity_by_dev: dict, fallback_by_dev: dict) -> dict:
    """Merge, preferring GitHub activity where present; otherwise use Sheet values.

    Only fills accomplishments/blockers/notes from Sheet when corresponding GH sections
    for a developer are empty (no PRs/issues/reviews/comments).
    """
    merged = {}
    for repo in ("frontend", "backend"):
        merged[repo] = {}
        repo_activity = activity_by_dev.get(repo, {})
        repo_fallback = fallback_by_dev.get(repo, {})
        dev_names = set(list(repo_activity.keys()) + list(repo_fallback.keys()))
        for dev in dev_names:
            act = repo_activity.get(dev, {
                "prs_opened": [],
                "prs_merged": [],
                "issues_closed": [],
                "issues_updated": [],
            })
            fb = repo_fallback.get(dev, {"accomplishments": "", "blockers": "", "notes": ""})

            has_any_gh = any([
                act["prs_opened"], act["prs_merged"], act["issues_closed"], act["issues_updated"]
            ])

            merged[repo][dev] = {
                **act,
                "accomplishments_fallback": None if has_any_gh else fb.get("accomplishments") or "",
                "blockers_fallback": None if has_any_gh else fb.get("blockers") or "",
                "notes_fallback": None if has_any_gh else fb.get("notes") or "",
            }
    return merged

def _html_h1(title: str) -> str:
    return f'<h1 style="color:#27a25a;font-size:28px;margin:12px 0 8px 0;padding:0;">{title}</h1>'


def _html_h2(title: str) -> str:
    return f'<h2 style="color:#111;font-size:20px;margin:10px 0 6px 0;padding:0;">{title}</h2>'


def _html_h2_title(title: str) -> str:
    """Green section titles (keep developer names black via _html_h2)."""
    return f'<h2 style="color:#27a25a;font-size:20px;margin:10px 0 6px 0;padding:0;">{title}</h2>'


def _html_h3_block(content_html: str) -> str:
    return f'<div style="font-size:16px;margin:0 0 8px 0;">{content_html}</div>'


def _html_list(items: list) -> str:
    if not items:
        return _html_h3_block('<p style="margin:0 0 10px 20px;">No updates</p>')
    li = []
    for it in items:
        title = it.get("title", "")
        url = it.get("html_url", "")
        number = it.get("number")
        description = it.get("description", "")
        label = f"#{number} {title}" if number is not None else title
        line = f"<a href=\"{url}\" style=\"text-decoration:none;color:#111\">{label}</a>"

        # Add description as sub-bullet if available
        if description:
            line += f"<br><span style=\"margin-left:15px;color:#666;font-size:14px;\">• {description}</span>"

        li.append(f"<li style=\"margin:4px 0;\">{line}</li>")
    return _html_h3_block('<ul style="margin:0 0 10px 20px;">' + "".join(li) + "</ul>")


def _html_dev_block(dev_name: str, data: dict) -> str:
    parts = [_html_h2(dev_name)]
    parts.append(_html_h2_title("PRs Created") + _html_list(data.get("prs_opened", [])))
    parts.append(_html_h2_title("PRs Merged") + _html_list(data.get("prs_merged", [])))
    parts.append(_html_h2_title("Issues Closed") + _html_list(data.get("issues_closed", [])))
    parts.append(_html_h2_title("Issues Updated") + _html_list(data.get("issues_updated", [])))

    # Optional manual entries (if present), with clean titles
    if data.get("accomplishments_fallback") is not None:
        acc = data.get("accomplishments_fallback") or "No updates"
        parts.append(_html_h2_title("Accomplishments") + _html_h3_block(f'<p style="margin:0 0 10px 20px;">{acc}</p>'))
    if data.get("blockers_fallback") is not None:
        blk = data.get("blockers_fallback") or "No updates"
        parts.append(_html_h2_title("Blockers") + _html_h3_block(f'<p style=\"margin:0 0 10px 20px;\">{blk}</p>'))
    if data.get("notes_fallback") is not None:
        nts = data.get("notes_fallback") or "No updates"
        parts.append(_html_h2_title("Notes") + _html_h3_block(f'<p style="margin:0 0 10px 20px;">{nts}</p>'))

    return "".join(parts)


def build_daily_report_email_for_repo(repo_key: str, repo_activity: dict, label_date: str) -> tuple:
    """Return (subject, body_html) for a single-repo daily report."""
    dev_names = ", ".join([d for d in repo_activity.keys()]) or "N/A"
    header = (
        f"<h1 style=\"margin:0;font-size:26px;\">Jogaliga {repo_key.capitalize()} Daily Report</h1>"
        f"<p style=\"margin:10px 0 0 0;font-size:16px\"><b>Developers:</b> {dev_names} &nbsp;&nbsp; <b>Date:</b> {label_date}</p>"
    )
    sections = [_html_h1("Today's Accomplishments")]
    blocks = []
    for dev_name, dev_data in repo_activity.items():
        blocks.append(_html_dev_block(dev_name, dev_data))
    if blocks:
        sections.append("".join(blocks))
    else:
        sections.append('<p style="margin:0 0 10px 0;font-size:16px">No updates</p>')

    body = f'''<table width="600" cellpadding="0" cellspacing="0" border="0" style="font-family:Arial,sans-serif;margin:0;padding:0;">
<tr><td bgcolor="#27a25a" style="color:#fff;padding:24px;border-radius:15px">{header}</td></tr>
<tr><td bgcolor="#ffffff" style="padding:10px;">{''.join(sections)}</td></tr>
<tr><td bgcolor="#f9fafb" style="padding:15px;text-align:center;font-size:12px;color:#666;">This is an automated report.</td></tr>
</table>'''
    subject = f"Daily Report - {repo_key.capitalize()} [{label_date}]"
    return subject, body


def render_daily_report_dry_run() -> str:
    """Generate a minimal dry-run HTML using placeholder content for smoke testing."""
    sample = {
        "frontend": {
            "Gerald": {"prs_opened": [{"number": 1, "title": "Feat", "html_url": "#"}],
                        "prs_merged": [], "issues_closed": [], "issues_updated": [],
                        "accomplishments_fallback": None, "blockers_fallback": None, "notes_fallback": None},
        },
        "backend": {}
    }
    _, html = build_daily_report_email_for_repo("frontend", sample["frontend"], "January 01, 2025")
    return html


def send_error_email(sender: str, app_password: str, receiver: str, message: str) -> None:
    try:
        yag = yagmail.SMTP(sender, app_password)
        yag.send(receiver, "Daily Report Error", [message])
    except Exception:
        pass


def _env_flag_true(var_name: str, default: bool = False) -> bool:
    """Return True if env var is a truthy value.

    Truthy values: '1', 'true', 'yes', 'on' (case-insensitive).
    Falsy values: '0', 'false', 'no', 'off', '' (case-insensitive) or unset.
    """
    raw = os.getenv(var_name)
    if raw is None:
        return default
    val = raw.strip().lower()
    if val in ("1", "true", "yes", "on"):  # Truthy
        return True
    if val in ("0", "false", "no", "off", ""):  # Falsy
        return False
    # Fallback: non-empty defaults to True
    return True

def group_reports_by_repo_and_developer(responses, expected_devs):
    grouped = defaultdict(dict)
    for row in responses:
        # Normalize repo/position
        position = row['Position'].strip().lower()
        if 'frontend' in position:
            repo = 'frontend'
        elif 'backend' in position:
            repo = 'backend'
        else:
            continue  # skip unknown positions
        dev = row['Developer Name'].strip()
        grouped[repo][dev] = {
            'accomplishments': str(row.get("Accomplishment Today (separate items with commas)", "None")),
            'plans': str(row.get("Tomorrow's Plans (separate items with commas)", "None")),
            'blockers': str(row.get("Blockers/Questions (separate items with commas)", "None")),
            'notes': str(row.get("Notes (separate items with commas)", "None"))
        }
    # Fill missing devs with 'None'
    for repo, devs in expected_devs.items():
        for dev in devs:
            if dev not in grouped[repo]:
                grouped[repo][dev] = {
                    'accomplishments': 'None',
                    'plans': 'None',
                    'blockers': 'None',
                    'notes': 'None'
                }
    return grouped


def _github_headers() -> dict:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "JogaligaDailyReportMailer/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


_GH_SESSION = None


def _github_session():
    """Return a requests.Session with retries/backoff configured for GitHub API."""
    global _GH_SESSION
    if _GH_SESSION is not None:
        return _GH_SESSION
    session = requests.Session()
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    # Default headers (can be overridden per-request)
    session.headers.update({"User-Agent": "JogaligaDailyReportMailer/1.0"})
    _GH_SESSION = session
    return _GH_SESSION


def _search_date_range(start_iso_utc: str, end_iso_utc: str) -> str:
    """Convert ISO UTC timestamps to GitHub Search API date range (YYYY-MM-DD..YYYY-MM-DD).

    The Search API does not reliably accept timestamp precision; use date-only.
    """
    s = datetime.datetime.fromisoformat(start_iso_utc.replace("Z", "+00:00"))
    e = datetime.datetime.fromisoformat(end_iso_utc.replace("Z", "+00:00"))
    return f"{s.date()}..{e.date()}"


def _safe_get(url: str, headers: dict, params: dict) -> dict:
    """HTTP GET with graceful fallback: returns {} on HTTP errors like 401/403/422."""
    try:
        session = _github_session()
        resp = session.get(url, headers=headers, params=params, timeout=(10, 30))
        if resp.status_code >= 400:
            # Best-effort log to console, but don't crash
            try:
                msg = resp.json()
            except Exception:
                msg = resp.text
            print(f"GitHub API GET {url} failed: {resp.status_code} {msg}")
            return {}
        return resp.json()
    except Exception as exc:
        print(f"GitHub API GET {url} exception: {exc}")
        return {}


def _extract_pr_description(body: str) -> str:
    """Extract the first sentence after '## 📝 Description' from PR body.

    Returns the first sentence or empty string if not found.
    """
    if not body:
        return ""

    # Find the Description section
    desc_marker = "## 📝 Description"
    desc_start = body.find(desc_marker)

    if desc_start == -1:
        return ""

    # Extract text after the Description header
    desc_text = body[desc_start + len(desc_marker):].strip()

    # Look for the next section header (##) to limit the scope
    next_section = desc_text.find("## ")
    if next_section != -1:
        desc_text = desc_text[:next_section].strip()

    # Split into sentences and get the first one
    import re
    sentences = re.split(r'(?<=[.!?])\s+', desc_text.strip())

    if sentences and sentences[0].strip():
        # Clean up the sentence (remove extra whitespace, bullet points, etc.)
        first_sentence = sentences[0].strip()
        # Remove common prefixes like bullet points
        first_sentence = re.sub(r'^[-•*]\s*', '', first_sentence)
        return first_sentence

    return ""

def fetch_prs_opened(owner: str, repo: str, start_iso_utc: str, end_iso_utc: str) -> list:
    """Fetch PRs opened within [start, end] using GitHub search API.

    Returns list of dicts: {number, title, html_url, author, created_at, description}
    """
    date_range = _search_date_range(start_iso_utc, end_iso_utc)
    query = f"repo:{owner}/{repo} is:pr created:{date_range}"
    url = "https://api.github.com/search/issues"
    headers = _github_headers()
    page = 1
    per_page = 100
    results = []
    while True:
        params = {"q": query, "per_page": per_page, "page": page, "sort": "created", "order": "desc"}
        data = _safe_get(url, headers, params) or {}
        items = data.get("items", [])
        for it in items:
            # Strictly enforce the PH-day window using exact timestamps
            if not _iso_in_window(it.get("created_at", ""), start_iso_utc, end_iso_utc):
                continue
            body = it.get("body", "")
            description = _extract_pr_description(body)
            results.append({
                "number": it.get("number"),
                "title": it.get("title", ""),
                "html_url": it.get("html_url", ""),
                "author": (it.get("user") or {}).get("login", ""),
                "created_at": it.get("created_at", ""),
                "description": description,
            })
        if len(items) < per_page:
            break
        page += 1
    return results


def fetch_prs_opened_for_repos(repos: list, start_iso_utc: str, end_iso_utc: str) -> dict:
    """Fetch opened PRs for multiple repos. repos entries like (owner, repo_name)."""
    data: dict = {}
    for owner, repo in repos:
        data[f"{owner}/{repo}"] = fetch_prs_opened(owner, repo, start_iso_utc, end_iso_utc)
    return data


def fetch_prs_merged(owner: str, repo: str, start_iso_utc: str, end_iso_utc: str) -> list:
    """Fetch PRs merged within [start, end] using GitHub search API.

    Returns list of dicts: {number, title, html_url, author, merged_at, description}
    """
    date_range = _search_date_range(start_iso_utc, end_iso_utc)
    query = f"repo:{owner}/{repo} is:pr is:merged merged:{date_range}"
    url = "https://api.github.com/search/issues"
    headers = _github_headers()
    page = 1
    per_page = 100
    results = []
    while True:
        params = {"q": query, "per_page": per_page, "page": page, "sort": "updated", "order": "desc"}
        data = _safe_get(url, headers, params) or {}
        items = data.get("items", [])
        for it in items:
            # Enforce PH-day window using closed_at (which reflects merge time for merged PRs in Search API)
            merged_ts = it.get("closed_at", "")
            if not _iso_in_window(merged_ts, start_iso_utc, end_iso_utc):
                continue
            body = it.get("body", "")
            description = _extract_pr_description(body)
            results.append({
                "number": it.get("number"),
                "title": it.get("title", ""),
                "html_url": it.get("html_url", ""),
                "author": (it.get("user") or {}).get("login", ""),
                "merged_at": it.get("closed_at", ""),
                "description": description,
            })
        if len(items) < per_page:
            break
        page += 1
    return results


def fetch_prs_merged_for_repos(repos: list, start_iso_utc: str, end_iso_utc: str) -> dict:
    data: dict = {}
    for owner, repo in repos:
        data[f"{owner}/{repo}"] = fetch_prs_merged(owner, repo, start_iso_utc, end_iso_utc)
    return data


def _iso_in_window(iso_ts: str, start_iso_utc: str, end_iso_utc: str) -> bool:
    if not iso_ts:
        return False
    try:
        ts = datetime.datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        start = datetime.datetime.fromisoformat(start_iso_utc.replace("Z", "+00:00"))
        end = datetime.datetime.fromisoformat(end_iso_utc.replace("Z", "+00:00"))
        return start <= ts <= end
    except Exception:
        return False


def fetch_pr_reviews_and_comments(owner: str, repo: str, start_iso_utc: str, end_iso_utc: str) -> list:
    """Fetch PR reviews and top-level PR comments within the window.

    NOTE: Reviews and comments are excluded from reports per user request.
    Returns empty list.
    """
    return []


def fetch_pr_reviews_and_comments_for_repos(repos: list, start_iso_utc: str, end_iso_utc: str) -> dict:
    data: dict = {}
    for owner, repo in repos:
        data[f"{owner}/{repo}"] = fetch_pr_reviews_and_comments(owner, repo, start_iso_utc, end_iso_utc)
    return data


def _search_issues(query: str, sort: str = "updated", order: str = "desc") -> list:
    url = "https://api.github.com/search/issues"
    headers = _github_headers()
    page = 1
    per_page = 100
    out = []
    while True:
        params = {"q": query, "per_page": per_page, "page": page, "sort": sort, "order": order}
        data = _safe_get(url, headers, params) or {}
        items = data.get("items", [])
        out.extend(items)
        if len(items) < per_page:
            break
        page += 1
    return out


def fetch_issues_closed_and_updated(owner: str, repo: str, start_iso_utc: str, end_iso_utc: str) -> list:
    """Fetch issues closed and issues updated within [start, end].

    Returns list of dicts with union of both sets. Duplicates are merged by issue number.
    Each item: {number, title, html_url, author, state, closed_at, updated_at, kind}
    kind in {"closed", "updated"}
    """
    base = f"repo:{owner}/{repo} is:issue"
    date_range = _search_date_range(start_iso_utc, end_iso_utc)
    closed_items = _search_issues(f"{base} closed:{date_range}", sort="updated")
    updated_items = _search_issues(f"{base} updated:{date_range}", sort="updated")

    by_num: dict = {}
    def add_items(items: list, kind: str):
        for it in items:
            number = it.get("number")
            if number is None:
                continue
            rec = by_num.get(number, {
                "number": number,
                "title": it.get("title", ""),
                "html_url": it.get("html_url", ""),
                "author": (it.get("user") or {}).get("login", ""),
                "state": it.get("state", ""),
                "closed_at": it.get("closed_at", ""),
                "updated_at": it.get("updated_at", ""),
                "kind": kind,
            })
            # If we already have an entry, prefer marking as closed if applicable
            if rec.get("kind") != "closed" and kind == "closed":
                rec["kind"] = "closed"
                rec["closed_at"] = it.get("closed_at", rec.get("closed_at", ""))
            else:
                # ensure updated_at is the latest seen
                rec["updated_at"] = it.get("updated_at", rec.get("updated_at", ""))
            by_num[number] = rec

    add_items(closed_items, "closed")
    add_items(updated_items, "updated")
    return list(by_num.values())


def fetch_issues_closed_and_updated_for_repos(repos: list, start_iso_utc: str, end_iso_utc: str) -> dict:
    data: dict = {}
    for owner, repo in repos:
        data[f"{owner}/{repo}"] = fetch_issues_closed_and_updated(owner, repo, start_iso_utc, end_iso_utc)
    return data


def _get_github_user_map(repo: str) -> dict:
    """Optional mapping of GitHub usernames to developer display names per repo.

    Env variables supported (optional):
    - DEV1_NAME_FRONTEND, DEV2_NAME_FRONTEND, DEV1_GH_FRONTEND, DEV2_GH_FRONTEND
    - DEV1_NAME_BACKEND,  DEV2_NAME_BACKEND,  DEV1_GH_BACKEND,  DEV2_GH_BACKEND
    """
    mapping: dict = {}
    if repo == "frontend":
        name1 = os.getenv("DEV1_NAME_FRONTEND") or ""
        name2 = os.getenv("DEV2_NAME_FRONTEND") or ""
        gh1_orig = (os.getenv("DEV1_GH_FRONTEND") or "").strip()
        gh2_orig = (os.getenv("DEV2_GH_FRONTEND") or "").strip()
        gh1_lower = gh1_orig.lower()
        gh2_lower = gh2_orig.lower()
        if gh1_orig and name1:
            mapping[gh1_orig] = name1  # Store original case
            mapping[gh1_lower] = name1  # Also store lowercase
        if gh2_orig and name2:
            mapping[gh2_orig] = name2  # Store original case
            mapping[gh2_lower] = name2  # Also store lowercase
    elif repo == "backend":
        name1 = os.getenv("DEV1_NAME_BACKEND") or ""
        name2 = os.getenv("DEV2_NAME_BACKEND") or ""
        gh1_orig = (os.getenv("DEV1_GH_BACKEND") or "").strip()
        gh2_orig = (os.getenv("DEV2_GH_BACKEND") or "").strip()
        gh1_lower = gh1_orig.lower()
        gh2_lower = gh2_orig.lower()
        if gh1_orig and name1:
            mapping[gh1_orig] = name1  # Store original case
            mapping[gh1_lower] = name1  # Also store lowercase
        if gh2_orig and name2:
            mapping[gh2_orig] = name2  # Store original case
            mapping[gh2_lower] = name2  # Also store lowercase
    return mapping


def _assign_dev_for_login(repo: str, login: str, expected_devs_for_repo: list) -> str:
    """Map a GitHub login to a developer name using optional env mapping; fallback to login string."""
    if not login:
        return "Unmapped"

    # Skip bot accounts
    if login.endswith('[bot]') or login == 'github-actions[bot]':
        return ""

    mapping = _get_github_user_map(repo)
    # Try original case first, then lowercase
    if login in mapping:
        return mapping[login]
    login_lower = login.strip().lower()
    if login_lower in mapping:
        return mapping[login_lower]
    # if login already equals one of expected developers (rare), allow it
    for d in expected_devs_for_repo:
        if d and d.strip().lower() == login_lower:
            return d
    return login


def normalize_activity_by_developer(
    repos: list,
    expected_devs: dict,
    start_iso_utc: str,
    end_iso_utc: str,
) -> dict:
    """Collect and normalize activity grouped by developer per repo.

    Returns structure: {repo_name: {developer_name: {prs_opened, prs_merged, issues_closed, issues_updated}}}
    """
    # Explicitly exclude commits as a data source per PRD.
    # Only PRs (opened/merged) and Issues (closed/updated) are considered.
    opened = fetch_prs_opened_for_repos(repos, start_iso_utc, end_iso_utc)
    merged = fetch_prs_merged_for_repos(repos, start_iso_utc, end_iso_utc)
    issues = fetch_issues_closed_and_updated_for_repos(repos, start_iso_utc, end_iso_utc)

    out: dict = {}
    for owner, repo_name in repos:
        key = f"{owner}/{repo_name}"
        repo_short = "frontend" if "frontend" in repo_name else ("backend" if "backend" in repo_name else repo_name)
        out[repo_short] = {}
        devs = expected_devs.get(repo_short, [])
        # Initialize
        for d in devs:
            out[repo_short][d] = {
                "prs_opened": [],
                "prs_merged": [],
                "issues_closed": [],
                "issues_updated": [],
            }

        # PRs opened
        for it in opened.get(key, []):
            dev = _assign_dev_for_login(repo_short, it.get("author", ""), devs)
            if not dev:  # Skip bots and empty assignments
                continue
            out[repo_short].setdefault(dev, {"prs_opened": [], "prs_merged": [], "issues_closed": [], "issues_updated": []})
            out[repo_short][dev]["prs_opened"].append(it)

        # PRs merged
        for it in merged.get(key, []):
            dev = _assign_dev_for_login(repo_short, it.get("author", ""), devs)
            if not dev:  # Skip bots and empty assignments
                continue
            out[repo_short].setdefault(dev, {"prs_opened": [], "prs_merged": [], "issues_closed": [], "issues_updated": []})
            out[repo_short][dev]["prs_merged"].append(it)

        # Issues
        for it in issues.get(key, []):
            dev = _assign_dev_for_login(repo_short, it.get("author", ""), devs)
            if not dev:  # Skip bots and empty assignments
                continue
            out[repo_short].setdefault(dev, {"prs_opened": [], "prs_merged": [], "issues_closed": [], "issues_updated": []})
            if it.get("kind") == "closed":
                out[repo_short][dev]["issues_closed"].append(it)
            else:
                out[repo_short][dev]["issues_updated"].append(it)

    return out

def main():

    dotenv.load_dotenv()
    
    CREDS_PATH = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "jogaliga-daily-report-652c86c83d3f.json")
    sender = os.getenv("SENDER_EMAIL")
    app_password = os.getenv("GMAIL_APP_PASSWORD")
    # Robust boolean env flags
    no_send = _env_flag_true("NO_SEND", default=False)
    skip_sheets = _env_flag_true("NO_SHEETS", default=False)

    def compute_receivers(repo_key: str) -> list:
        base = [os.getenv("RECEIVER_EMAIL")]
        if repo_key == "frontend" and os.getenv("JESREAL_EMAIL"):
            base.append(os.getenv("JESREAL_EMAIL"))
        if repo_key == "backend" and os.getenv("HANS_EMAIL"):
            base.append(os.getenv("HANS_EMAIL"))
        manual_mock = os.getenv("MANUAL_MOCK", "False")
        mock_addr = (os.getenv("MOCK_RECEIVER_EMAIL") or "").strip()
        # Treat MANUAL_MOCK via robust boolean evaluation as well
        if _env_flag_true("MANUAL_MOCK", default=False) and mock_addr:
            return [mock_addr]
        if _env_flag_true("MOCK_MODE", default=False) and mock_addr:
            print("MOCK_MODE enabled; using MOCK_RECEIVER_EMAIL")
            return [mock_addr]
        return base

    frontend_receivers = compute_receivers("frontend")
    backend_receivers = compute_receivers("backend")

    expected_devs = {
        'frontend': [os.getenv("DEV1_NAME_FRONTEND", "Gerald"), os.getenv("DEV2_NAME_FRONTEND", "Jesreal")],
        'backend': [os.getenv("DEV1_NAME_BACKEND", "Gerald"), os.getenv("DEV2_NAME_BACKEND", "YOUR_NAME")],
    }

    # GitHub activity window and repos
    print("[1/6] Calculating window...", flush=True)
    custom_date = os.getenv("CUSTOM_DATE", "").strip()
    if custom_date:
        try:
            start_iso, end_iso, label_date = DailyReportMailer.custom_date_window_asia_manila(custom_date)
            print(f"Using custom date: {label_date}", flush=True)
        except ValueError as e:
            print(f"Error parsing custom date '{custom_date}': {e}", flush=True)
            print("Falling back to previous day's date", flush=True)
            start_iso, end_iso, label_date = DailyReportMailer.previous_day_window_asia_manila()
    else:
        # Default to previous day window so a 00:10 run sends yesterday's report
        start_iso, end_iso, label_date = DailyReportMailer.previous_day_window_asia_manila()
    # Resolve repo slugs from env (owner/repo). Defaults to AppArara slugs provided.
    frontend_slug = os.getenv("FRONTEND_REPO", "AppArara/jogaliga_frontend")
    backend_slug = os.getenv("BACKEND_REPO", "AppArara/jogaliga_backend")
    def _split_slug(slug: str):
        parts = (slug or "").split("/", 1)
        return (parts[0], parts[1]) if len(parts) == 2 else ("", slug)
    repos = [_split_slug(frontend_slug), _split_slug(backend_slug)]

    # Activity + Sheets fallback
    print("[2/6] Fetching GitHub activity...", flush=True)
    activity = normalize_activity_by_developer(repos, expected_devs, start_iso, end_iso)
    if skip_sheets:
        print("[3/6] Skipping Google Sheets fallback (NO_SHEETS=True)", flush=True)
        fallback = {"frontend": {}, "backend": {}}
    else:
        print("[3/6] Reading Google Sheets fallback...", flush=True)
        try:
            sh = open_spreadsheet(os.getenv("SHEET_ID", SPREADSHEET_ID), CREDS_PATH)
            # Use the same labeled date as the report (Asia/Manila previous or custom)
            # Parse label_date back to a date object in Asia/Manila
            tz = ZoneInfo("Asia/Manila")
            target_date = datetime.datetime.strptime(label_date, '%B %d, %Y').date()
            fallback = build_sheet_fallback_by_repo_and_dev(sh, expected_devs, target_date)
        except Exception as e:
            print(f"Sheets fallback failed: {e}", flush=True)
            print("Continuing with GitHub activity only...", flush=True)
            fallback = {"frontend": {}, "backend": {}}
    merged = merge_with_sheet_fallback(activity, fallback)

    print("[4/6] Building emails...", flush=True)
    yag = None if no_send else yagmail.SMTP(sender, app_password)

    # Frontend email
    subj_f, body_f = build_daily_report_email_for_repo("frontend", merged.get("frontend", {}), label_date)

    if no_send:
        print(f"[5/6] Would send Frontend email to: {frontend_receivers}", flush=True)
    else:
        if frontend_receivers:
            print("[5/6] Sending Frontend email...", flush=True)
            try:
                yag.send(frontend_receivers, subj_f, [body_f])
                print("Frontend email sent successfully!", flush=True)
            except Exception as e:
                print(f"Failed to send Frontend email: {e}", flush=True)
                # Don't exit on email failure - continue with backend email
                if "authentication" in str(e).lower():
                    print("This appears to be an authentication issue. Check your Gmail app password and account settings.", flush=True)

    # Backend email
    subj_b, body_b = build_daily_report_email_for_repo("backend", merged.get("backend", {}), label_date)
    if no_send:
        print(f"[6/6] Would send Backend email to: {backend_receivers}", flush=True)
    else:
        if backend_receivers:
            print("[6/6] Sending Backend email...", flush=True)
            try:
                yag.send(backend_receivers, subj_b, [body_b])
                print("Backend email sent successfully!", flush=True)
            except Exception as e:
                print(f"Failed to send Backend email: {e}", flush=True)
                if "authentication" in str(e).lower():
                    print("This appears to be an authentication issue. Check your Gmail app password and account settings.", flush=True)

    print("Done.", flush=True)

if __name__ == "__main__":
    main()

# .venv/Scripts/activate.ps1