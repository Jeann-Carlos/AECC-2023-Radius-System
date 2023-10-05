#############################################
#           Propiedad de la AECC            #
#############################################
'''
Author: Jeann C. Hernandez Franco
Co-Author: Luis F. Velazquez
Date: October 5, 2023
Last Updated: ---------
'''


import os
import sqlite3
import time
import schedule


def StartService():
    try:
        # Start by connecting to Db
        cursor,conn = ConnectToDb()

        # Schedule the job to run every 5 minutes
        schedule.every(.10).minutes.do(CheckUsers,cursor=cursor,conn=conn)
        # schedule.every(1).minutes.do(CloseProgram)

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
        return -1 # return -1 as a signal error

def ConnectToDb():

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
    return cursor,conn


def DiscconectFromDb(cursor,conn):
        cursor.close()
        conn.close()
        print('Successfully disconnected...Have a nice day!')

def SaveTable():
    pass

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


def CheckUsers(cursor,conn):
    newly_registered_members = GetTable()
    CompareTables(cursor,newly_registered_members)



def CompareTables(cursor,newly_registered_members):
    cursor.execute('select ip from "client_by_group" join client where client_id=client.id and group_id=1')
    already_registered_members_list = cursor.fetchall()
    for new_member in newly_registered_members.readlines():
        if new_member in [ip[0] for ip in already_registered_members_list]:
            print(f"User: {new_member} already registered as a member...Ignoring")
        else:
            cursor.execute(f'select * from client where client.ip="{new_member}"')
            member_data = cursor.fetchall()
            # check if user already exists in Pihole
            if member_data == []:
                pass
            else:
                # add user to registered members
                 cursor.execute(f'insert into client_by_group values (client_id={new_member[0][0]},group_id=1')

class CloseProgram:
    # user_input = input("Press 'q' to quit: ")
    #if user_input.lower() == "q":
    pass

exit_value = StartService()
exit(exit_value)