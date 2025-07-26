import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_PATH = 'jogaliga-daily-report-652c86c83d3f.json'
# Paste your spreadsheet ID below (from the URL between /d/ and /edit)
SPREADSHEET_ID = '1wjbi6vxm2dZMHG2xvLCsTJW3rTJ206y2tXIAMHvam0M'

def main():
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    print("SUCCESS! Sheet title is:", sh.title)

if __name__ == "__main__":
    main() 