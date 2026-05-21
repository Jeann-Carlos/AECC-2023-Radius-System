import os
import sqlite3
from config import Config

class PiholeService:
    @staticmethod
    def add_to_newly_registered_file(mac_address):
        """Appends MAC address to Newly_Registered_Members.txt for compatibility with legacy components."""
        file_path = os.path.join(Config.BASE_DIR, '..', '..', 'Newly_Registered_Members.txt')
        # Ensure directory exists
        dir_name = os.path.dirname(file_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
            
        try:
            # Open file and write MAC address
            with open(file_path, 'a') as file:
                file.write(f"{mac_address}\n")
        except Exception as e:
            print(f"Failed to write MAC to legacy text file: {e}")

    @staticmethod
    def sync_device_to_pihole(mac_address, action='add'):
        """
        Connects directly to gravity.db to assign/remove MAC address to AECC group (group_id=1).
        If the client does not exist in the client table, it registers them first.
        """
        mac_upper = mac_address.upper()
        try:
            conn = sqlite3.connect(Config.PIHOLE_DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Find client in client table
            cursor.execute('SELECT id FROM client WHERE ip = ?', (mac_upper,))
            client_row = cursor.fetchone()
            
            if not client_row:
                # If not found, add client to Pi-hole database
                cursor.execute('INSERT INTO client (ip, comment) VALUES (?, ?)', (mac_upper, 'AECC Registered Member'))
                client_id = cursor.lastrowid
            else:
                client_id = client_row['id']
                
            if action == 'add':
                # Map to group 1 (AECC network), delete from group 0 (default)
                cursor.execute('INSERT OR IGNORE INTO client_by_group (client_id, group_id) VALUES (?, 1)', (client_id,))
                cursor.execute('DELETE FROM client_by_group WHERE client_id = ? AND group_id = 0', (client_id,))
                print(f"Added Pi-hole client {mac_upper} to AECC group.")
            elif action == 'remove':
                # Map to group 0 (default/blocked), delete from group 1 (AECC network)
                cursor.execute('INSERT OR IGNORE INTO client_by_group (client_id, group_id) VALUES (?, 0)', (client_id,))
                cursor.execute('DELETE FROM client_by_group WHERE client_id = ? AND group_id = 1', (client_id,))
                print(f"Removed Pi-hole client {mac_upper} from AECC group.")
                
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Pi-hole database operations failed: {e}")
            return False

    @staticmethod
    def run_legacy_sync():
        """
        Implements the logic of the original driverProgram.
        Reads Newly_Registered_Members.txt, compares with client_by_group and updates accordingly.
        """
        file_path = os.path.join(Config.BASE_DIR, '..', '..', 'Newly_Registered_Members.txt')
        if not os.path.exists(file_path):
            print(f"Legacy registration text file not found at {file_path}")
            return False
            
        try:
            with open(file_path, 'r') as file:
                new_members = [line.strip().upper() for line in file if line.strip() and not line.startswith("AECC")]
                
            if not new_members:
                print("No new members in legacy text file to sync.")
                return True
                
            conn = sqlite3.connect(Config.PIHOLE_DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Select all registered members in group 1
            cursor.execute('SELECT c.ip FROM client_by_group cg JOIN client c ON cg.client_id = c.id WHERE cg.group_id = 1')
            already_registered_list = [row['ip'].upper() for row in cursor.fetchall()]
            
            for member in new_members:
                if member in already_registered_list:
                    print(f"User MAC: {member} already registered in group 1. Ignoring.")
                else:
                    cursor.execute('SELECT id FROM client WHERE ip = ?', (member,))
                    client_row = cursor.fetchone()
                    
                    if client_row:
                        client_id = client_row['id']
                        print(f"Inserting user with MAC: {member} into group 1 in Pi-hole database")
                        cursor.execute('INSERT OR IGNORE INTO client_by_group (client_id, group_id) VALUES (?, 1)', (client_id,))
                        cursor.execute('DELETE FROM client_by_group WHERE client_id = ? AND group_id = 0', (client_id,))
                    else:
                        print(f"Client MAC: {member} not found in client table. Creating record...")
                        cursor.execute('INSERT INTO client (ip, comment) VALUES (?, ?)', (member, 'AECC Registered Member'))
                        new_client_id = cursor.lastrowid
                        cursor.execute('INSERT INTO client_by_group (client_id, group_id) VALUES (?, 1)', (new_client_id,))
                        
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Legacy sync run failed: {e}")
            return False
