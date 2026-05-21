import os
import sqlite3
from flask import Flask
from config import Config

def init_databases():
    """Initializes local SQLite databases for RADIUS and Pi-hole mock mode."""
    # 1. Initialize RADIUS SQLite Database
    db_dir = os.path.dirname(Config.RADIUS_DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        
    conn = sqlite3.connect(Config.RADIUS_DB_PATH)
    cursor = conn.cursor()
    
    # Create FreeRADIUS schema tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS radcheck (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            attribute TEXT NOT NULL,
            op VARCHAR(2) NOT NULL DEFAULT '==',
            value TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS radreply (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            attribute TEXT NOT NULL,
            op VARCHAR(2) NOT NULL DEFAULT '=',
            value TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS radusergroup (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            groupname TEXT NOT NULL,
            priority INTEGER NOT NULL DEFAULT 1
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS radacct (
            radacctid INTEGER PRIMARY KEY AUTOINCREMENT,
            acctsessionid TEXT NOT NULL,
            acctuniqueid TEXT UNIQUE,
            username TEXT,
            groupname TEXT,
            realm TEXT,
            nasipaddress TEXT,
            nasportid TEXT,
            nasporttype TEXT,
            acctstarttime TIMESTAMP,
            acctupdatetime TIMESTAMP,
            acctstoptime TIMESTAMP,
            acctinterval INTEGER,
            acctsessiontime INTEGER,
            acctauthentic TEXT,
            connectinfo_start TEXT,
            connectinfo_stop TEXT,
            acctinputoctets INTEGER,
            acctoutputoctets INTEGER,
            calledstationid TEXT,
            callingstationid TEXT,
            acctterminatecause TEXT,
            servicetype TEXT,
            framedprotocol TEXT,
            framedipaddress TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS radpostauth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            pass TEXT,
            reply TEXT,
            authdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create local user registry metadata table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            student_id TEXT PRIMARY KEY,
            telephone TEXT NOT NULL,
            mac_address TEXT,
            ip_address TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed mock members and logs if database is empty
    cursor.execute("SELECT COUNT(*) FROM members")
    if cursor.fetchone()[0] == 0:
        # Initial mock student records for local dev validation
        cursor.execute("INSERT INTO members (student_id, telephone, mac_address, status) VALUES ('802111222', '7875551234', 'AA:BB:CC:DD:EE:01', 'Active')")
        cursor.execute("INSERT INTO members (student_id, telephone, mac_address, status) VALUES ('802333444', '7875555678', 'AA:BB:CC:DD:EE:02', 'Active')")
        cursor.execute("INSERT INTO members (student_id, telephone, mac_address, status) VALUES ('123456789', '7875559999', 'AA:BB:CC:DD:EE:03', 'Pending')")

        # Seed mock RADIUS accounting sessions for dashboard
        cursor.execute("""
            INSERT INTO radacct (acctsessionid, acctuniqueid, username, acctstarttime, acctstoptime, acctsessiontime, framedipaddress, acctinputoctets, acctoutputoctets)
            VALUES ('sess_1', 'uniq_1', 'AA:BB:CC:DD:EE:01', '2026-05-21 08:00:00', '2026-05-21 12:00:00', 14400, '192.168.1.101', 5420110, 102482390)
        """)
        cursor.execute("""
            INSERT INTO radacct (acctsessionid, acctuniqueid, username, acctstarttime, acctstoptime, acctsessiontime, framedipaddress, acctinputoctets, acctoutputoctets)
            VALUES ('sess_2', 'uniq_2', 'AA:BB:CC:DD:EE:02', '2026-05-21 09:30:00', NULL, 1800, '192.168.1.102', 1238910, 4820199)
        """)
        cursor.execute("""
            INSERT INTO radacct (acctsessionid, acctuniqueid, username, acctstarttime, acctstoptime, acctsessiontime, framedipaddress, acctinputoctets, acctoutputoctets)
            VALUES ('sess_3', 'uniq_3', 'AA:BB:CC:DD:EE:04', '2026-05-21 14:15:00', '2026-05-21 14:45:00', 1800, '192.168.1.103', 450000, 2100000)
        """)

        # Seed mock postauth logs
        cursor.execute("INSERT INTO radpostauth (username, pass, reply) VALUES ('AA:BB:CC:DD:EE:01', 'AECC-Pass', 'Access-Accept')")
        cursor.execute("INSERT INTO radpostauth (username, pass, reply) VALUES ('AA:BB:CC:DD:EE:02', 'AECC-Pass', 'Access-Accept')")
        cursor.execute("INSERT INTO radpostauth (username, pass, reply) VALUES ('FF:FF:FF:FF:FF:FF', 'Wrong-Pass', 'Access-Reject')")
        
    conn.commit()
    conn.close()

    # 2. Initialize Pi-hole gravity.db mock if it does not exist
    if not os.path.exists(Config.PIHOLE_DB_PATH):
        print(f"Pi-hole gravity.db not found at {Config.PIHOLE_DB_PATH}. Creating mock file...")
        conn_ph = sqlite3.connect(Config.PIHOLE_DB_PATH)
        c_ph = conn_ph.cursor()
        
        c_ph.execute('''
            CREATE TABLE IF NOT EXISTS client (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT UNIQUE NOT NULL,
                comment TEXT
            )
        ''')
        
        c_ph.execute('''
            CREATE TABLE IF NOT EXISTS client_by_group (
                client_id INTEGER,
                group_id INTEGER,
                PRIMARY KEY (client_id, group_id)
            )
        ''')
        
        c_ph.execute('''
            CREATE TABLE IF NOT EXISTS "group" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Seed group ID 1 (standard AECC registration group) and group ID 0 (default)
        c_ph.execute("INSERT OR IGNORE INTO \"group\" (id, name) VALUES (0, 'default')")
        c_ph.execute("INSERT OR IGNORE INTO \"group\" (id, name) VALUES (1, 'AECC-RADIUS')")
        
        # Seed some clients
        c_ph.execute("INSERT OR IGNORE INTO client (id, ip, comment) VALUES (1, 'AA:BB:CC:DD:EE:01', 'Mock Student 1')")
        c_ph.execute("INSERT OR IGNORE INTO client (id, ip, comment) VALUES (2, 'AA:BB:CC:DD:EE:02', 'Mock Student 2')")
        c_ph.execute("INSERT OR IGNORE INTO client (id, ip, comment) VALUES (3, 'AA:BB:CC:DD:EE:03', 'Mock Student 3')")
        
        c_ph.execute("INSERT OR IGNORE INTO client_by_group (client_id, group_id) VALUES (1, 1)")
        c_ph.execute("INSERT OR IGNORE INTO client_by_group (client_id, group_id) VALUES (2, 1)")
        c_ph.execute("INSERT OR IGNORE INTO client_by_group (client_id, group_id) VALUES (3, 0)")
        
        conn_ph.commit()
        conn_ph.close()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize SQLite databases
    init_databases()

    # Import blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # Context processors to share mock status and user data across templates
    @app.context_processor
    def inject_global_vars():
        return {
            'mock_mode': app.config['MOCK_MODE']
        }

    return app
