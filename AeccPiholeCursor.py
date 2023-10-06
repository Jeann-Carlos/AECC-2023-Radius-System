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
import asyncio

#Global Variables
schedule_timer=.10

def StartService():

    try:

        # Schedule the job to run every 5 minutes
        schedule.every(schedule_timer).minutes.do(DriverProgram)

        # Keep the service running indefinitely
        while True:
            schedule.run_pending()
            time.sleep(1)

    except FileNotFoundError as e:
        print('Database file was not found. Check error below for details:')
        print(e)
        return -1
    except Exception as e:
        print('Unhandled Exception caught. Check error below for details:')
        print(e)
        return -1  # return -1 as a signal error


def ConnectToDb():

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


def DiscconectFromDb(cursor, conn):
    cursor.close()
    conn.close()
    print('Successfully disconnected...Have a nice day!')


def UpdateDb(conn):
    try:
        conn.commit()
    except Exception as e:
        print('Rolling back any changes...')
        conn.rollback()
        return e



def GetTable():
    file_path = "Newly_Registered_Members.txt"

    # Check if the file exists
    table_exists = os.path.isfile(file_path)

    # If the file does not exist, create it
    if not table_exists:
        with open(file_path, 'w') as file:
            file.write("AECC Newly Registered Members:\n")

    # Return the file object
    return open(file_path, 'r')


def DriverProgram():

    # Start by connecting to Db
    cursor, conn = ConnectToDb()

    # Get new users that paid
    newly_registered_members = [L.strip() for L in GetTable()]

    # Compare users that paid with the registered tables in gravity db
    CompareTables(cursor, newly_registered_members)

    # Commit changes
    UpdateDb(conn)

    # Disconnect from DB
    DiscconectFromDb(cursor, conn)

    # Notify user that is safe to close program now



def CompareTables(cursor, newly_registered_members):

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


exit_value = StartService()
exit(exit_value)
