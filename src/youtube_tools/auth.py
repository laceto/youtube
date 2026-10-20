from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from youtube_tools.config import get_google_credentials_path, get_youtube_token_path

YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube"]
ANALYTICS_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def get_credentials(
    credentials_path: str | None = None,
    token_path: str | None = None,
    scopes: list[str] | None = None,
) -> Credentials:
    """Return valid user OAuth credentials, refreshing the cached token or running the browser consent flow if needed."""
    scopes = scopes or YOUTUBE_SCOPES
    token_file = Path(token_path or get_youtube_token_path())
    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), scopes)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path or get_google_credentials_path(), scopes)
        creds = flow.run_local_server(port=0)
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(creds.to_json(), encoding="utf-8")
    return creds
