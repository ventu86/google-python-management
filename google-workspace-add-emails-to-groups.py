#pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

import os
import time
import datetime
# Import necessary libraries for CSV parsing
import csv
import re
# Import Google API client libraries
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
#

### VARIABLES ###
# Path to the CSV file containing group mappings
# CSV format: UTF-8 with semicolon (;) as delimiters
CSV_PATH = 'csv/ett-dedagroup-new-members-20250731-redo01.csv'
CSV_HAS_HEADER = True  # Set to True if the CSV file has a header row

# Path to the service account JSON key file
#SERVICE_ACCOUNT_FILE = 'json-keys/gsuite-ett-4e2152819eb4.json'
SERVICE_ACCOUNT_FILE = 'json-keys/gsuite-scai-migrazione-gruppi.json'
# The Google Workspace Admin SDK scopes
SCOPES = ['https://www.googleapis.com/auth/admin.directory.group.member']
#https://www.googleapis.com/auth/admin.directory.group', 'https://www.googleapis.com/auth/admin.directory.group.member', 'https://www.googleapis.com/auth/contacts.readonly'
# The email of the user to impersonate (must be an admin)
#SUBJECT_EMAIL = 'admin@ettsolutions.cloud'
SUBJECT_EMAIL = 'admin@grupposcai.it'


# Google Workspace Info
#WORKSPACE_CUSTOMER_ID = 'C02f4be4t'  # Your Google Workspace Customer ID ETT
WORKSPACE_CUSTOMER_ID = 'C01d28ohr'  # Your Google Workspace Customer ID GruppoSCAI

### ###

### SCRIPT VARIABLES - DON'T CHANGE ###
# Get current date and time for the filename
CURRENT_TIME = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Set log file name
LOG_FILENAME = f"logs/add-emails-to-groups_{CURRENT_TIME}.txt"

# ### Variables for resume the script from the last group processed ###
# Group to resume the script from
RESUME_GROUP = ''
# ### ###
### ###


### CSV function to read CSV files ###
def has_utf8_bom(file_path):
    with open(file_path, 'rb') as f:
        start = f.read(3)
        return start == b'\xef\xbb\xbf'


def parse_group_mappings(csv_file_path, has_header=True):
    # Check if the file has a UTF-8 BOM
    if has_utf8_bom(csv_file_path):
        raise ValueError(f"File '{csv_file_path}' has a UTF-8 BOM. Please save it without BOM.")

    mappings = []
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=';', quotechar='"')
        
        buffer = []
        for i, row in enumerate(reader):
            # Skip header line if requested
            if has_header and i == 0:
                continue

            # Flatten multi-line records
            if len(row) == 1 and buffer:
                buffer[-1] += ' ' + row[0]
                continue

            if buffer:
                full_line = buffer[0]
                buffer = []
            else:
                full_line = row[0] if len(row) else ''

            if len(row) == 2:
                source, destinations = row
            elif len(row) == 1:
                parts = full_line.split(';', 1)
                if len(parts) == 2:
                    source, destinations = parts
                else:
                    continue  # skip malformed
            else:
                continue  # skip malformed rows

            # Clean and split destination emails
            destination_list = re.split(r'\s+', destinations.strip().replace('"', ''))
            mappings.append((source.strip(), destination_list))

    return mappings
### ###

### Google Workspace functions ###
# Add multiple members to a group from a list
def add_members_to_group(service, group_email, member_emails, role='MEMBER'):
    if not member_emails:
        print(f'\n Skipping {group_email} — no members provided in CSV.')
        return

    for email in member_emails:
        try:
            service.members().insert(
                groupKey=group_email,
                body={
                    'email': email.strip().lower(),
                    'role': role
                }
            ).execute()
            print(f'Added {email} to {group_email}')
        except HttpError as error:
            if error.resp.status == 409:
                print(f'{email} is already a member of {group_email}')
            else:
                print(f'Error adding {email} to {group_email}: {error}')
            time.sleep(1)

# Save group members and their roles to a file
def save_group_members_to_file_for_csv_source(group_email, member_emails, role, suffix=''):
    # Sanitize the group name to create a valid filename
    group_name = group_email.replace('@', '_').replace('.', '_')

    # Open the file for writing (create it if it doesn't exist)
    with open(f'logs/group_members/{CURRENT_TIME}_{group_name}_members{suffix}.txt', 'w') as file:
        file.write(f"Group: {group_email}\n")
        file.write(f"Members and Roles:\n")
        for member in member_emails:
            file.write(f"{member['email'].strip().lower()},{role}\n")

        print(f"Saved members and roles for {group_email} to logs/group_members/{CURRENT_TIME}_{group_name}_members{suffix}.txt")

### ###

# Run the script
try:
    # Initialize the credentials
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES, subject=SUBJECT_EMAIL)
    service = build('admin', 'directory_v1', credentials=credentials)

    # Mapping groups and group members from CSV file
    group_mappings = parse_group_mappings(CSV_PATH, CSV_HAS_HEADER)
    print(group_mappings)

    # Check if the RESUME_GROUP is set
    if RESUME_GROUP:
        BOOL_RESUME_GROUP = True
    else:
        BOOL_RESUME_GROUP = False

    for group_email, members in group_mappings:

        # Check if the group is the one to resume from
        if BOOL_RESUME_GROUP:
            if group_email != RESUME_GROUP:
                continue # Skip to the next group if not the one to resume from
            else :
                BOOL_RESUME_GROUP = False

        # DEBUG
        time.sleep(5)

        print(f'Processing group: {group_email}')
        # Append the output to the file
        with open(LOG_FILENAME, 'a') as file:
            file.write(f"Processing group: {group_email}\n")

        # Save the group members to a file before making any changes
        google_group_object = service.members().list(groupKey=group_email).execute()
        google_group_object_members = google_group_object.get('members', [])
        save_group_members_to_file_for_csv_source(group_email, google_group_object_members, 'MEMBER', '_before')

        # DEBUG
        time.sleep(5)

        # Add members to the group
        add_members_to_group(service, group_email, members, 'MEMBER')

        # DEBUG
        time.sleep(8)

        # Save the group members to a file after making changes
        google_group_object = service.members().list(groupKey=group_email).execute()
        google_group_object_members = google_group_object.get('members', [])
        save_group_members_to_file_for_csv_source(group_email, google_group_object_members, 'MEMBER', '_after')

        time.sleep(3)
    
    print("All groups processed successfully.")
    with open(LOG_FILENAME, 'a') as file:
        file.write(f"All groups processed successfully.\n")

except ValueError as e:
    print(e)
