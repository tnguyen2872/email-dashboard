import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# This tells Google we want read-only access to Gmail
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def authenticate():
    """Connect to Gmail and return a service object."""
    creds = None

    # If we've logged in before, load the saved token
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If no valid token, ask the user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the token so we don't have to log in every time
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def get_emails(service, max_results=10):
    """Fetch the latest emails from the inbox."""
    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        maxResults=max_results
    ).execute()

    messages = results.get("messages", [])

    if not messages:
        print("No emails found.")
        return

    print(f"Fetching {len(messages)} emails...\n")
    print("-" * 60)

    for msg in messages:
        # Get the full email details
        email_data = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()

        headers = email_data.get("payload", {}).get("headers", [])

        # Extract the fields we care about
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No subject")
        sender  = next((h["value"] for h in headers if h["name"] == "From"), "Unknown sender")
        date    = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown date")
        snippet = email_data.get("snippet", "")

        print(f"From:    {sender}")
        print(f"Date:    {date}")
        print(f"Subject: {subject}")
        print(f"Preview: {snippet[:100]}...")
        print("-" * 60)


if __name__ == "__main__":
    print("Connecting to Gmail...\n")
    service = authenticate()
    get_emails(service, max_results=10)
    print("\nDone!")