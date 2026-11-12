from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

from youtube_tools.config import get_api_key

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def _search_top_item(query: str, api_key: str | None = None) -> dict | None:
    """Return the raw top result item from the YouTube search API for `query`, or None if no match."""
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 1,
        "key": api_key or get_api_key(),
    }
    response = requests.get(SEARCH_URL, params=params, timeout=10)
    response.raise_for_status()
    items = response.json().get("items", [])
    return items[0] if items else None


def search_video_url(query: str, api_key: str | None = None) -> str | None:
    """Return the URL of the top matching YouTube video for `query`, or None if no match."""
    item = _search_top_item(query, api_key)
    if item is None:
        return None
    return f"https://www.youtube.com/watch?v={item['id']['videoId']}"


def search_video(query: str, api_key: str | None = None) -> dict[str, str | None] | None:
    """Return {"title": ..., "url": ...} for the top matching YouTube video, or None if no match."""
    item = _search_top_item(query, api_key)
    if item is None:
        return None
    return {
        "title": item.get("snippet", {}).get("title"),
        "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
    }


def search_video_urls(queries: list[str], api_key: str | None = None) -> dict[str, str | None]:
    """Map each query string to its top matching YouTube video URL (or None)."""
    resolved_key = api_key or get_api_key()
    return {query: search_video_url(query, api_key=resolved_key) for query in queries}


PLAYLIST_ITEMS_URL = "https://www.googleapis.com/youtube/v3/playlistItems"


def extract_playlist_id(url_or_id: str) -> str:
    """Return the playlist ID from a YouTube playlist URL (`...list=ID...`) or a bare ID."""
    values = parse_qs(urlparse(url_or_id).query).get("list")
    return values[0] if values else url_or_id.strip()


def list_playlist_items(playlist_id_or_url: str, api_key: str | None = None) -> list[dict[str, str | int | None]]:
    """Return every video in a public playlist as {position, title, channel, url, published_at} dicts."""
    params = {
        "part": "snippet",
        "playlistId": extract_playlist_id(playlist_id_or_url),
        "maxResults": 50,
        "key": api_key or get_api_key(),
    }
    rows: list[dict[str, str | int | None]] = []
    while True:
        response = requests.get(PLAYLIST_ITEMS_URL, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
        for item in payload.get("items", []):
            snippet = item.get("snippet", {})
            video_id = snippet.get("resourceId", {}).get("videoId")
            rows.append(
                {
                    "position": snippet.get("position"),
                    "title": snippet.get("title"),
                    "channel": snippet.get("videoOwnerChannelTitle"),
                    "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
                    "published_at": snippet.get("publishedAt"),
                }
            )
        next_token = payload.get("nextPageToken")
        if not next_token:
            return rows
        params["pageToken"] = next_token


PLAYLISTS_URL = "https://www.googleapis.com/youtube/v3/playlists"


def extract_video_id(url_or_id: str) -> str:
    """Return the video ID from a youtube.com/watch?v=, youtu.be/ or shorts URL, or a bare ID."""
    parsed = urlparse(url_or_id)
    values = parse_qs(parsed.query).get("v")
    if values:
        return values[0]
    if parsed.netloc.endswith("youtu.be") or "/shorts/" in parsed.path:
        return parsed.path.rstrip("/").rsplit("/", 1)[-1]
    return url_or_id.strip()


def _auth_headers(access_token: str | None = None) -> dict[str, str]:
    if access_token is None:
        from youtube_tools.auth import get_credentials

        access_token = get_credentials().token
    return {"Authorization": f"Bearer {access_token}"}


def create_playlist(
    title: str,
    description: str = "",
    privacy: str = "private",
    access_token: str | None = None,
) -> str:
    """Create a playlist on the authenticated user's channel and return its ID (costs 50 quota units)."""
    body = {
        "snippet": {"title": title, "description": description},
        "status": {"privacyStatus": privacy},
    }
    response = requests.post(
        PLAYLISTS_URL,
        params={"part": "snippet,status"},
        json=body,
        headers=_auth_headers(access_token),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["id"]


def add_video_to_playlist(playlist_id: str, video_url_or_id: str, access_token: str | None = None) -> str:
    """Append one video to a playlist you own and return the new playlist-item ID (costs 50 quota units)."""
    body = {
        "snippet": {
            "playlistId": extract_playlist_id(playlist_id),
            "resourceId": {"kind": "youtube#video", "videoId": extract_video_id(video_url_or_id)},
        }
    }
    response = requests.post(
        PLAYLIST_ITEMS_URL,
        params={"part": "snippet"},
        json=body,
        headers=_auth_headers(access_token),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["id"]


def add_videos_to_playlist(
    playlist_id: str, videos: list[str], access_token: str | None = None
) -> dict[str, str | None]:
    """Add each video in order; map each input to its playlist-item ID, or None if that insert failed."""
    token = access_token or _auth_headers()["Authorization"].removeprefix("Bearer ")
    results: dict[str, str | None] = {}
    for video in videos:
        try:
            results[video] = add_video_to_playlist(playlist_id, video, access_token=token)
        except requests.HTTPError:
            results[video] = None
    return results


UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"


def upload_video(
    file_path: str,
    title: str,
    description: str = "",
    privacy: str = "private",
    access_token: str | None = None,
) -> str:
    """Upload a local video file to the authenticated channel and return its video ID (costs 1600 quota units)."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Video file not found: {file_path}")
    headers = _auth_headers(access_token)
    body = {
        "snippet": {"title": title, "description": description},
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    init = requests.post(
        UPLOAD_URL,
        params={"uploadType": "resumable", "part": "snippet,status"},
        json=body,
        headers={**headers, "X-Upload-Content-Type": "video/*", "X-Upload-Content-Length": str(path.stat().st_size)},
        timeout=30,
    )
    init.raise_for_status()
    session_url = init.headers["Location"]
    with path.open("rb") as handle:
        response = requests.put(
            session_url,
            data=handle,
            headers={**headers, "Content-Type": "video/*", "Content-Length": str(path.stat().st_size)},
            timeout=None,
        )
    response.raise_for_status()
    return response.json()["id"]
