import sqlite3
import random
from datetime import datetime
from config import Config
from app.models import RadiusModel, DBConnection

class RadiusService:
    @staticmethod
    def register_user_device(student_id, telephone, mac_address, ip_address=None):
        """Registers a device locally and configures it in the RADIUS auth db."""
        success = RadiusModel.register_device(student_id, telephone, mac_address, ip_address)
        if success:
            # Simulate a post-auth login request for verification logs
            RadiusService.log_auth_attempt(mac_address, f"AECC-Auth-{student_id[-4:]}", 'Access-Accept')
        return success

    @staticmethod
    def log_auth_attempt(mac_address, password, reply_status):
        """Records a connection attempt log in radpostauth."""
        mac_upper = mac_address.upper()
        try:
            conn = sqlite3.connect(Config.RADIUS_DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO radpostauth (username, pass, reply) VALUES (?, ?, ?)",
                (mac_upper, password, reply_status)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Failed to record auth log: {e}")
            return False

    @staticmethod
    def create_mock_acct_session(mac_address, ip_address):
        """Creates a mock accounting session for testing RADIUS tracking."""
        mac_upper = mac_address.upper()
        session_id = f"sess_{random.randint(100000, 999999)}"
        unique_id = f"uniq_{random.randint(100000, 999999)}"
        try:
            conn = sqlite3.connect(Config.RADIUS_DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO radacct (acctsessionid, acctuniqueid, username, acctstarttime, framedipaddress, acctinputoctets, acctoutputoctets)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, unique_id, mac_upper, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ip_address, 0, 0))
            conn.commit()
            conn.close()
            return session_id
        except Exception as e:
            print(f"Failed to record accounting session: {e}")
            return None

    @staticmethod
    def terminate_mock_sessions(mac_address):
        """Closes any open accounting sessions for a MAC address."""
        mac_upper = mac_address.upper()
        try:
            conn = sqlite3.connect(Config.RADIUS_DB_PATH)
            cursor = conn.cursor()
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Find open sessions
            cursor.execute("SELECT radacctid, acctstarttime FROM radacct WHERE username = ? AND acctstoptime IS NULL", (mac_upper,))
            rows = cursor.fetchall()
            
            for row in rows:
                acct_id = row[0]
                start_time_str = row[1]
                
                # Calculate elapsed time in seconds
                try:
                    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                    elapsed = int((datetime.now() - start_time).total_seconds())
                except:
                    elapsed = 3600 # Default to 1 hour
                    
                # Update accounting info
                in_bytes = random.randint(500000, 50000000)
                out_bytes = random.randint(2000000, 200000000)
                cursor.execute('''
                    UPDATE radacct 
                    SET acctstoptime = ?, acctsessiontime = ?, acctinputoctets = ?, acctoutputoctets = ?
                    WHERE radacctid = ?
                ''', (now_str, elapsed, in_bytes, out_bytes, acct_id))
                
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Failed to close mock sessions: {e}")
            return False
