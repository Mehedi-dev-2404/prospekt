import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly'
]

def main():
    creds = None
    if os.path.exists('gmail_token.json'):
        creds = Credentials.from_authorized_user_file('gmail_token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('gmail_credentials.json', SCOPES)
            creds = flow.run_local_server(port=8888)
        with open('gmail_token.json', 'w') as token:
            token.write(creds.to_json())
        print("Token saved to gmail_token.json")
    print("Authentication successful")

if __name__ == '__main__':
    main()
