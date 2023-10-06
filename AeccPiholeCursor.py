#############################################
#           Propiedad de la AECC            #
#############################################
'''
Author: Jeann C. Hernandez Franco
Co-Author: Luis F. Velazquez
Date: October 5, 2023
Last Updated: October 6, 2023
'''

import os
import sqlite3
import time
import schedule
import getmac
from getmac import get_mac_address


def connectToDb():

    # Name of DB
    database_file = "gravity.db"

    # Check if the database file exists
    if not os.path.isfile(database_file):
        # If the doest not exists, raise an exception
        raise FileNotFoundError(f"Database file not found: {database_file} ")

    # Connect to the database
    conn = sqlite3.connect(database_file)

    # Create a cursor object to execute SQL statements
    cursor = conn.cursor()

    # Return the cursor and connection
    return cursor, conn


def discconectFromDb(cursor, conn):
    cursor.close()
    conn.close()
    print('Successfully disconnected...Have a nice day!')


def updateDb(conn):
    try:
        conn.commit()
    except Exception as e:
        print('Rolling back any changes...')
        conn.rollback()
        return e



def getTable():
    file_path = "Newly_Registered_Members.txt"

    # Check if the file exists
    table_exists = os.path.isfile(file_path)

    # If the file does not exist, create it
    if not table_exists:
        with open(file_path, 'w') as file:
            file.write("AECC Newly Registered Members:\n")

    # Return the file object
    return open(file_path, 'r')

def addToTable(mac_address):

    file_path = "Newly_Registered_Members.txt"

    # Check if the file exists
    table_exists = os.path.isfile(file_path)

    # If the file does exist, add mac address
    if table_exists:
        with open(file_path, 'w') as file:
            file.write(f"{mac_address}\n")
    else:
        pass

def driverProgram():

    try:
        # Start by connecting to Db
        cursor, conn = connectToDb()

        # Get new users that paid
        newly_registered_members = [L.strip() for L in getTable()]

        # Compare users that paid with the registered tables in gravity db
        compareTables(cursor, newly_registered_members)

        # Commit changes
        updateDb(conn)

        # Disconnect from DB
        discconectFromDb(cursor, conn)

        # Notify user that is safe to close program now

    except FileNotFoundError as e:
        print('Database file was not found. Check error below for details:')
        print(e)
        return -1
    except Exception as e:
        print('Unhandled Exception caught. Check error below for details:')
        print(e)
        return -1  # return -1 as a signal error



def compareTables(cursor, newly_registered_members):

    # Select all registered members
    cursor.execute('select ip from "client_by_group" join client where client_id=client.id and group_id=1')
    already_registered_members_list = cursor.fetchall()

    for new_member in newly_registered_members:
        if new_member in [ip[0] for ip in already_registered_members_list]:
            print(f"User: {new_member} already registered as a member...Ignoring")
        else:
            cursor.execute(f'select * from client where client.ip="{new_member}"')
            member_data = cursor.fetchall()

            # Check if user already exists in Pihole, if pihole doesn't have him there's a problem
            if member_data == []:
                pass
            else:
                # Add user to registered members
                print(f"Inserting user with ip: {new_member} at the Db")
                cursor.execute(f"INSERT INTO client_by_group(client_id, group_id) VALUES ({int(member_data[0][0])}, 1)")
                cursor.execute(f"DELETE FROM client_by_group WHERE client_id = {member_data[0][0]} AND group_id = 0")


def getMac():
    ip_address = "192.168.0.236"  # Replace to receive from flask

    mac_address = get_mac_address(ip=ip_address)

    if mac_address is None:
        print("MAC address not found")
    else:
        print(f"Recieved: {mac_address} from flask")



#getMac()
exit_value = driverProgram()
exit(exit_value)
