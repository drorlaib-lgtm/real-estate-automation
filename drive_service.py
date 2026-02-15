"""
Google Drive Service - Upload files and create folders
Uses OAuth2 for personal Google accounts
"""

import os
import io
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

# Configuration
CREDENTIALS_FILE = Path(__file__).parent / "oauth_credentials.json"
TOKEN_FILE = Path(__file__).parent / "token.json"
PARENT_FOLDER_ID = "1LskZ4d15jU4v28WfkIW6-1tqJpa0BDc4"  # חוזי נדלן folder
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Cache the service to avoid recreating it for each file upload
_cached_service = None


def get_drive_service():
    """Get authenticated Google Drive service using OAuth2 (cached for performance)."""
    global _cached_service

    # Return cached service if available
    if _cached_service is not None:
        return _cached_service

    creds = None

    # Try to load from Streamlit secrets (for cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'google_drive' in st.secrets:
            token_data = dict(st.secrets['google_drive'])
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    except:
        pass

    # If no credentials from secrets, try local file
    if creds is None and TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # If no valid credentials, do OAuth flow (only works locally)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token locally if possible
            try:
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            except:
                pass
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    "oauth_credentials.json not found. "
                    "Download it from Google Cloud Console > APIs > Credentials > OAuth 2.0 Client IDs"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=8080)

            # Save token for next time
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)
    _cached_service = service
    return service


def create_folder(folder_name: str, parent_id: str = PARENT_FOLDER_ID) -> str:
    """Create a folder in Google Drive and return its ID."""
    service = get_drive_service()

    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }

    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')


def upload_file(file_path: str, folder_id: str, file_name: str = None) -> dict:
    """Upload a file to Google Drive folder."""
    service = get_drive_service()

    if file_name is None:
        file_name = os.path.basename(file_path)

    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }

    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink'
    ).execute()

    return file


def upload_bytes(content: bytes, file_name: str, folder_id: str, mime_type: str = None) -> dict:
    """Upload bytes content directly to Google Drive (no temp file)."""
    service = get_drive_service()

    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }

    # Use BytesIO to avoid temp file issues on Windows
    fh = io.BytesIO(content)
    media = MediaIoBaseUpload(fh, mimetype=mime_type or 'application/octet-stream', resumable=True)

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink'
    ).execute()

    return file


def upload_json(data: dict, file_name: str, folder_id: str) -> dict:
    """Upload JSON data directly to Google Drive."""
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    content = json_str.encode('utf-8')
    return upload_bytes(content, file_name, folder_id, 'application/json')


def create_transaction_folder(property_address: str) -> dict:
    """Create a folder for a transaction using property address."""
    # Use address as folder name (clean special characters)
    folder_name = property_address.strip()

    folder_id = create_folder(folder_name)
    folder_link = f"https://drive.google.com/drive/folders/{folder_id}"

    return {
        "folder_id": folder_id,
        "folder_name": folder_name,
        "folder_link": folder_link
    }


def test_connection():
    """Test if Google Drive connection works."""
    try:
        service = get_drive_service()
        # Try to list files (just to test connection)
        results = service.files().list(pageSize=1, fields="files(id, name)").execute()
        return {"success": True, "message": "Connected to Google Drive"}
    except Exception as e:
        return {"success": False, "message": str(e)}


if __name__ == "__main__":
    # Test the connection
    result = test_connection()
    print(result)
