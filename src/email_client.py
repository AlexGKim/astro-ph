import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def get_gmail_service(token_path="token.json", creds_path="credentials.json"):
    """Shows basic usage of the Gmail API."""
    creds = None
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception:
            # Fallback if token is corrupted
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                raise FileNotFoundError(f"Missing {creds_path}")
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def get_body_data(parts_list):
    for part in parts_list:
        if part.get("mimeType") == "text/plain":
            return part.get("body", {}).get("data", "")
        elif "parts" in part:
            res = get_body_data(part["parts"])
            if res:
                return res
    return ""


def fetch_latest_astroph_email(service, mark_read=True):
    """Fetches the latest unread astro-ph daily email."""
    try:
        query = 'from:no-reply@arxiv.org subject:"astro-ph daily" is:unread'
        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=1)
            .execute()
        )
        messages = results.get("messages", [])

        if not messages:
            return None

        msg_id = messages[0]["id"]
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )

        # Parse payload
        payload = msg.get("payload", {})
        parts = payload.get("parts", [])
        body_data = ""

        if parts:
            body_data = get_body_data(parts)
        else:
            body_data = payload.get("body", {}).get("data", "")

        if not body_data:
            return None

        # Pad to multiple of 4
        body_data += "=" * ((4 - len(body_data) % 4) % 4)
        text = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")

        if mark_read:
            service.users().messages().modify(
                userId="me", id=msg_id, body={"removeLabelIds": ["UNREAD"]}
            ).execute()

        return text
    except HttpError as error:
        print(f"An API error occurred: {error}")
        return None
