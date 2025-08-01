# google-python-management
Manage Google Workspace via Python

# google-workspace-add-emails-to-groups.py
Requirements
- A Google Cloud project
- A Google Cloud service account.
- Enable Admin SDK API.
- Enable domain-wide delegation.
- Authorize scopes in the Admin console: https://www.googleapis.com/auth/admin.directory.group.member
- CSV file (encoded in UTF-8) with the Google Primary Group mails and the new members.
- Python packages: google-api-python-client google-auth-httplib2 google-auth-oauthlib

Below you could find a guide to meet all the requirements.  

## CSV Template
Template file: `./csv/csv-template.csv`  
Table rappresented.  
*Keep in mind that multiple members will be in multiple lines. So could be present lines without group primary mail in the CSV file.*

| Gruppo Primary Mail; | New Google Group Members |
| --- | --- |
| google-group00@domain.com; | membermail00@domain.com |
| google-group01@domain.com; | membermail00@ext-domain.com |
| google-group02@domain.com; | "membermail00@ext-domain.com</br>membermail01@ext-domain.com" |

## Run the script
Change accordingly to your needs all the variables in the `### VARIABLES ###` area.  
By default 
the script will create a basic log file in the `./logs` directory and save the list of each Google Group members before and after the changes.  
If some of the members are already in the group the script will print a message accordingly.

Run the script when ready.

## Google cloud Service Account
Create a service account (IAM | Service Accounts).  
Create Service Account Key and download the JSON file.

## Enable Admin SDK API
From APIs & Services | Library search `admin sdk`. Click `Enable`.

## Enable Domain-wide Delegation
Go the service account that you want enable (IAM | Service Accounts).  
Expand the Advanced settings settings in the service account view.  
Copy the `Client ID` and keep it, because we need it later.  
Than click `View Google Workspace Admin Console`.  
From the left menu in the Google Workspace Admin Console navigate to Security | Access and data control | API controls.  
Now you will see the Domain wide delegation title. Select Manage Domain wide delegation.  
Click `Add new` and insert the previously copied `Client ID` and add the scope `https://www.googleapis.com/auth/admin.directory.group.member`.

## Install Python packages
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

```
# Trovare account non profilati all'interno del file di log (./logs)
cat shared_drives_missing_users_2025-02-27_09-40-26.txt | grep "New member not profiled on Google:" > temp.txt
```

