from google.oauth2 import service_account
from googleapiclient.discovery import build


def validate_with_google_sheets(student_id, telephone):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SERVICE_ACCOUNT_FILE = 'aecc-flask2023-f18201f75c25.json'

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    service = build('sheets', 'v4', credentials=credentials)

    spreadsheet_id = '1HbdWfqoD7kuvN_iv1OPHccbnIvkSf2V1buC_x_TcZu4'
    range_name = 'A1:B100'  # Adjust as needed
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])

    for row in values:
        if student_id == row[0] and telephone == row[1]:
            return True
    return False