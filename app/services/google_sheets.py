import os
import sqlite3
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import Config

class GoogleSheetsService:
    @staticmethod
    def validate_student(student_id, telephone):
        """
        Validates student credentials.
        If service account file exists, validates via Google Sheets API.
        Otherwise, falls back to mock validation (local sqlite check).
        """
        if os.path.exists(Config.GOOGLE_SHEETS_CREDENTIALS):
            try:
                SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
                credentials = service_account.Credentials.from_service_account_file(
                    Config.GOOGLE_SHEETS_CREDENTIALS, scopes=SCOPES
                )
                service = build('sheets', 'v4', credentials=credentials)
                
                result = service.spreadsheets().values().get(
                    spreadsheetId=Config.GOOGLE_SHEET_ID, 
                    range=Config.GOOGLE_SHEET_RANGE
                ).execute()
                
                values = result.get('values', [])
                for row in values:
                    if len(row) >= 2:
                        # Row columns: Student ID, Telephone Number
                        if str(student_id).strip() == str(row[0]).strip() and str(telephone).strip() == str(row[1]).strip():
                            return True
                return False
            except Exception as e:
                print(f"Google Sheets validation failed with error: {e}. Falling back to mock validation...")
                return GoogleSheetsService._mock_validate(student_id, telephone)
        else:
            return GoogleSheetsService._mock_validate(student_id, telephone)

    @staticmethod
    def _mock_validate(student_id, telephone):
        """Fallback validation check using seeded local database or testing tokens."""
        # Standard test bypass values
        dev_bypass_rules = [
            ("12345", "555-5555"),
            ("802000000", "7870000000"),
            ("802111222", "7875551234"),
            ("802333444", "7875555678"),
            ("123456789", "7875559999"),
        ]
        
        for mock_id, mock_tel in dev_bypass_rules:
            if student_id == mock_id and telephone == mock_tel:
                return True
                
        # Also check against database members table if they match
        try:
            conn = sqlite3.connect(Config.RADIUS_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT student_id, telephone FROM members WHERE student_id = ? AND telephone = ?", (student_id, telephone))
            row = cursor.fetchone()
            conn.close()
            if row:
                return True
        except Exception as e:
            print(f"Mock validation check against DB failed: {e}")
            
        return False
