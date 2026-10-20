import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_api_key() -> str:
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "YOUTUBE_API_KEY is not set. Copy .env.example to .env and fill it in."
        )
    return api_key


def get_openai_api_key() -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and fill it in."
        )
    return api_key


def get_google_credentials_path() -> str:
    path = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not path:
        raise RuntimeError(
            "GOOGLE_CREDENTIALS_JSON is not set. Point it at the OAuth client JSON in .env."
        )
    return path


def get_youtube_analytics_token_path() -> str:
    """Token cache for the analytics scopes; defaults to a sibling of YOUTUBE_TOKEN_JSON."""
    path = os.environ.get("YOUTUBE_ANALYTICS_TOKEN_JSON")
    if path:
        return path
    return str(Path(get_youtube_token_path()).with_name("youtube_analytics_token.json"))


def get_youtube_token_path() -> str:
    path = os.environ.get("YOUTUBE_TOKEN_JSON")
    if not path:
        raise RuntimeError(
            "YOUTUBE_TOKEN_JSON is not set. Set it in .env to where the YouTube OAuth token should be cached."
        )
    return path
