import yagmail, datetime, os, dotenv
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
        """Convert a block of text into HTML bullet points, splitting by commas."""
        # Split the text into items by comma and filter out empty items
        items = [item.strip() for item in text.split(',') if item.strip()]
        # Convert each item into a bullet point with capitalized first letter
        bullet_points = [f"• {item.capitalize()}" for item in items]
        # Join with line breaks
        return "<br>".join(bullet_points)

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


def main():

    dotenv.load_dotenv()
    
    CREDS_PATH = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "jogaliga-daily-report-652c86c83d3f.json")
    MOCK_MODE = os.getenv("MOCK_MODE", "True")
    
    sender = os.getenv("SENDER_EMAIL")
    app_password = os.getenv("GMAIL_APP_PASSWORD")
    # Receivers for each repo
    frontend_receivers = [os.getenv("RECEIVER_EMAIL")]
    backend_receivers = [os.getenv("RECEIVER_EMAIL")]
    if os.getenv("JESREAL_EMAIL"):
        frontend_receivers.append(os.getenv("JESREAL_EMAIL"))
    if os.getenv("HANS_EMAIL"):
        backend_receivers.append(os.getenv("HANS_EMAIL"))
    # For mock mode, override receivers
    test_email = "rhelbiro@gmail.com"
    if MOCK_MODE != "False":
        frontend_receivers = [test_email]
        backend_receivers = [test_email]
        print("Mock mode is enabled")
    else:
        print("Mock mode is disabled")

    # Define expected developers for each repo
    expected_devs = {
        'frontend': [os.getenv("DEV1_NAME_FRONTEND", "Gerald"), os.getenv("DEV2_NAME_FRONTEND", "Jesreal"), os.getenv("DEV3_NAME_FRONTEND", "Erick")],
        'backend': [os.getenv("DEV1_NAME_BACKEND", "Gerald"), os.getenv("DEV2_NAME_BACKEND", "Hans")],
    }

    # Fetch today's responses
    responses = fetch_todays_reports(CREDS_PATH)
    grouped = group_reports_by_repo_and_developer(responses, expected_devs)

    for repo in ["frontend", "backend"]:
        devs = expected_devs[repo]
        dev_entries = grouped[repo]
        # Prepare data for mailer
        dev1 = dev_entries[devs[0]]
        dev2 = dev_entries[devs[1]]
        receivers = frontend_receivers if repo == "frontend" else backend_receivers
        mailer = DailyReportMailer(repo, sender, receivers, app_password)
        
        if repo == "frontend":
            # Frontend has 3 developers
            dev3 = dev_entries[devs[2]]
            mailer.send_report(
                dev1_accomplishments=dev1['accomplishments'],
                dev2_accomplishments=dev2['accomplishments'],
                dev3_accomplishments=dev3['accomplishments'],
                dev1_plans=dev1['plans'],
                dev2_plans=dev2['plans'],
                dev3_plans=dev3['plans'],
                dev1_blockers=dev1['blockers'],
                dev2_blockers=dev2['blockers'],
                dev3_blockers=dev3['blockers'],
                dev1_notes=dev1['notes'],
                dev2_notes=dev2['notes'],
                dev3_notes=dev3['notes'],
                attachments=[]
            )
            if MOCK_MODE != "False":
                print(f"\n--- MOCK REPORT for {repo.upper()} ---")
                print(f"{devs[0]}: {dev1}")
                print(f"{devs[1]}: {dev2}")
                print(f"{devs[2]}: {dev3}")
        else:
            # Backend has 2 developers
            mailer.send_report(
                dev1_accomplishments=dev1['accomplishments'],
                dev2_accomplishments=dev2['accomplishments'],
                dev1_plans=dev1['plans'],
                dev2_plans=dev2['plans'],
                dev1_blockers=dev1['blockers'],
                dev2_blockers=dev2['blockers'],
                dev1_notes=dev1['notes'],
                dev2_notes=dev2['notes'],
                attachments=[]
            )
            if MOCK_MODE != "False":
                print(f"\n--- MOCK REPORT for {repo.upper()} ---")
                print(f"{devs[0]}: {dev1}")
                print(f"{devs[1]}: {dev2}")

if __name__ == "__main__":
    main()

# .venv/Scripts/activate.ps1