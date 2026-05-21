import sqlite3
from config import Config

class DBConnection:
    """Context manager for SQLite connections."""
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn.cursor(), self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type is not None:
                self.conn.rollback()
            else:
                self.conn.commit()
            self.conn.close()


class RadiusModel:
    @staticmethod
    def get_all_devices():
        """Fetches all registered devices and metadata."""
        with DBConnection(Config.RADIUS_DB_PATH) as (cursor, conn):
            cursor.execute('''
                SELECT m.*, rc.value as cleartext_pwd, rc.id as radcheck_id
                FROM members m
                LEFT JOIN radcheck rc ON m.mac_address = rc.username AND rc.attribute = 'Cleartext-Password'
                ORDER BY m.created_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def register_device(student_id, telephone, mac_address, ip_address=None, status='Active'):
        """Registers a device in both members table and radcheck table."""
        with DBConnection(Config.RADIUS_DB_PATH) as (cursor, conn):
            # Normalize MAC to uppercase
            mac_upper = mac_address.upper()
            
            # Insert or update member record
            cursor.execute('''
                INSERT INTO members (student_id, telephone, mac_address, ip_address, status)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(student_id) DO UPDATE SET
                    telephone=excluded.telephone,
                    mac_address=excluded.mac_address,
                    ip_address=excluded.ip_address,
                    status=excluded.status
            ''', (student_id, telephone, mac_upper, ip_address, status))
            
            # Register in radcheck (FreeRADIUS authentication)
            # Default password is the telephone number or a standard security key
            pwd = f"AECC-Auth-{student_id[-4:]}"
            
            # Delete old credentials if they existed for this MAC
            cursor.execute("DELETE FROM radcheck WHERE username = ?", (mac_upper,))
            
            # Insert new credential entry
            cursor.execute('''
                INSERT INTO radcheck (username, attribute, op, value)
                VALUES (?, 'Cleartext-Password', ':=', ?)
            ''', (mac_upper, pwd))
            
            # Insert default accept check rule if required by NAS configuration
            # In some setups: attribute='Auth-Type', op=':=', value='Accept'
            
            # Register in radusergroup
            cursor.execute("DELETE FROM radusergroup WHERE username = ?", (mac_upper,))
            cursor.execute('''
                INSERT INTO radusergroup (username, groupname, priority)
                VALUES (?, 'AECC-RADIUS', 1)
            ''', (mac_upper,))
            
            return True

    @staticmethod
    def delete_device(student_id):
        """Deletes a device from all local databases and RADIUS credentials."""
        with DBConnection(Config.RADIUS_DB_PATH) as (cursor, conn):
            # Get MAC address first
            cursor.execute("SELECT mac_address FROM members WHERE student_id = ?", (student_id,))
            row = cursor.fetchone()
            if row and row['mac_address']:
                mac = row['mac_address']
                cursor.execute("DELETE FROM radcheck WHERE username = ?", (mac,))
                cursor.execute("DELETE FROM radusergroup WHERE username = ?", (mac,))
            
            cursor.execute("DELETE FROM members WHERE student_id = ?", (student_id,))
            return True

    @staticmethod
    def update_device_status(student_id, status):
        """Updates device connection privileges."""
        with DBConnection(Config.RADIUS_DB_PATH) as (cursor, conn):
            cursor.execute("UPDATE members SET status = ? WHERE student_id = ?", (status, student_id))
            
            # Update usergroup priority or name based on status
            cursor.execute("SELECT mac_address FROM members WHERE student_id = ?", (student_id,))
            row = cursor.fetchone()
            if row and row['mac_address']:
                mac = row['mac_address']
                group = 'AECC-RADIUS' if status == 'Active' else 'AECC-Blocked'
                cursor.execute("UPDATE radusergroup SET groupname = ? WHERE username = ?", (group, mac))
            return True

    @staticmethod
    def get_auth_logs(limit=50):
        """Retrieves recent authentication logs from radpostauth."""
        with DBConnection(Config.RADIUS_DB_PATH) as (cursor, conn):
            cursor.execute('''
                SELECT * FROM radpostauth
                ORDER BY authdate DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_accounting_sessions(limit=50):
        """Retrieves RADIUS session accounting details."""
        with DBConnection(Config.RADIUS_DB_PATH) as (cursor, conn):
            cursor.execute('''
                SELECT * FROM radacct
                ORDER BY acctstarttime DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_dashboard_stats():
        """Aggregates system statistics for the dashboard."""
        stats = {}
        with DBConnection(Config.RADIUS_DB_PATH) as (cursor, conn):
            # Total registered
            cursor.execute("SELECT COUNT(*) FROM members")
            stats['total_devices'] = cursor.fetchone()[0]

            # Active vs Blocked
            cursor.execute("SELECT COUNT(*) FROM members WHERE status = 'Active'")
            stats['active_devices'] = cursor.fetchone()[0]
            
            stats['blocked_devices'] = stats['total_devices'] - stats['active_devices']

            # Active RADIUS sessions (acctstoptime is null)
            cursor.execute("SELECT COUNT(*) FROM radacct WHERE acctstoptime IS NULL")
            stats['active_sessions'] = cursor.fetchone()[0]

            # Auth failures count
            cursor.execute("SELECT COUNT(*) FROM radpostauth WHERE reply = 'Access-Reject'")
            stats['auth_failures'] = cursor.fetchone()[0]
            
            # Total data usage (bytes upload + download)
            cursor.execute("SELECT SUM(acctinputoctets + acctoutputoctets) FROM radacct")
            total_bytes = cursor.fetchone()[0] or 0
            # Convert to MegaBytes
            stats['total_mb_transferred'] = round(total_bytes / (1024 * 1024), 2)

        return stats
