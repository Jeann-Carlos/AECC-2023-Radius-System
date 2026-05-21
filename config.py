import os

class Config:
    # Flask Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'aecc_radius_secret_key_2026_dev')

    # Base paths
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # SQLite Databases
    # Local RADIUS database path
    RADIUS_DB_PATH = os.environ.get('RADIUS_DB_PATH', os.path.join(BASE_DIR, 'radius.db'))
    
    # Pi-hole gravity.db database path
    PIHOLE_DB_PATH = os.environ.get('PIHOLE_DB_PATH', os.path.join(BASE_DIR, 'gravity.db'))

    # Google Sheets Integration
    GOOGLE_SHEETS_CREDENTIALS = os.environ.get('GOOGLE_SHEETS_CREDENTIALS', os.path.join(BASE_DIR, 'aecc-flask2023-f18201f75c25.json'))
    GOOGLE_SHEET_ID = '1HbdWfqoD7kuvN_iv1OPHccbnIvkSf2V1buC_x_TcZu4'
    GOOGLE_SHEET_RANGE = 'A1:B100'

    # Admin Login Configuration
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'aecc2026')
    
    # Mock fallback settings
    MOCK_MODE = not os.path.exists(GOOGLE_SHEETS_CREDENTIALS) or not os.path.exists(PIHOLE_DB_PATH)
