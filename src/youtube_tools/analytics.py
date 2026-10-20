from datetime import date

import pandas as pd
import requests

from youtube_tools.api import extract_video_id

CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"
PLAYLIST_ITEMS_URL = "https://www.googleapis.com/youtube/v3/playlistItems"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
ANALYTICS_URL = "https://youtubeanalytics.googleapis.com/v2/reports"

TOTAL_METRICS = (
    "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,"
    "likes,comments,shares,subscribersGained,subscribersLost"
)


def _analytics_token(access_token: str | None = None) -> str:
    if access_token is not None:
        return access_token
    from youtube_tools.auth import ANALYTICS_SCOPES, get_credentials
    from youtube_tools.config import get_youtube_analytics_token_path

    return get_credentials(token_path=get_youtube_analytics_token_path(), scopes=ANALYTICS_SCOPES).token


def _get(url: str, params: dict, token: str) -> dict:
    response = requests.get(url, params=params, headers={"Authorization": f"Bearer {token}"}, timeout=15)
    response.raise_for_status()
    return response.json()


def list_my_uploads(max_results: int = 50, access_token: str | None = None) -> list[dict]:
    """Return the authenticated channel's most recent uploads as {video_id, title, published_at} dicts."""
    token = _analytics_token(access_token)
    channel = _get(CHANNELS_URL, {"part": "contentDetails", "mine": "true"}, token)
    uploads_id = channel["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    payload = _get(
        PLAYLIST_ITEMS_URL,
        {"part": "snippet", "playlistId": uploads_id, "maxResults": min(max_results, 50)},
        token,
    )
    return [
        {
            "video_id": item["snippet"]["resourceId"]["videoId"],
            "title": item["snippet"]["title"],
            "published_at": item["snippet"]["publishedAt"],
        }
        for item in payload.get("items", [])
    ]


def get_video_stats(video_url_or_id: str, access_token: str | None = None) -> dict:
    """Return public details + lifetime counters for one video (Data API videos.list, 1 quota unit)."""
    token = _analytics_token(access_token)
    video_id = extract_video_id(video_url_or_id)
    payload = _get(VIDEOS_URL, {"part": "snippet,statistics,contentDetails", "id": video_id}, token)
    items = payload.get("items", [])
    if not items:
        raise ValueError(f"No video found for id {video_id!r}")
    item = items[0]
    stats = item.get("statistics", {})
    return {
        "video_id": video_id,
        "title": item["snippet"]["title"],
        "published_at": item["snippet"]["publishedAt"],
        "duration": item["contentDetails"]["duration"],
        "views": int(stats.get("viewCount", 0)),
        "likes": int(stats.get("likeCount", 0)),
        "comments": int(stats.get("commentCount", 0)),
    }


def query_report(
    video_id: str,
    metrics: str,
    dimensions: str | None = None,
    start_date: str = "2005-04-23",
    end_date: str | None = None,
    sort: str | None = None,
    max_results: int | None = None,
    access_token: str | None = None,
) -> pd.DataFrame:
    """Run a YouTube Analytics reports.query for one video and return it as a DataFrame."""
    params = {
        "ids": "channel==MINE",
        "filters": f"video=={video_id}",
        "metrics": metrics,
        "startDate": start_date,
        "endDate": end_date or date.today().isoformat(),
    }
    if dimensions:
        params["dimensions"] = dimensions
    if sort:
        params["sort"] = sort
    if max_results:
        params["maxResults"] = max_results
    payload = _get(ANALYTICS_URL, params, _analytics_token(access_token))
    columns = [h["name"] for h in payload.get("columnHeaders", [])]
    return pd.DataFrame(payload.get("rows", []), columns=columns)


def build_video_report(video_url_or_id: str, access_token: str | None = None) -> dict[str, pd.DataFrame]:
    """Collect all report tables for one video, keyed by sheet name."""
    token = _analytics_token(access_token)
    video_id = extract_video_id(video_url_or_id)
    summary = pd.DataFrame([get_video_stats(video_id, token)])
    # Analytics reports are limited to the video's lifetime; earliest valid startDate is the publish date.
    start = summary.loc[0, "published_at"][:10]

    def q(metrics, dimensions=None, **kw):
        return query_report(video_id, metrics, dimensions, start_date=start, access_token=token, **kw)

    return {
        "summary": summary,
        "totals": q(TOTAL_METRICS),
        "daily": q("views,estimatedMinutesWatched,averageViewDuration", "day", sort="day"),
        "traffic_sources": q("views,estimatedMinutesWatched", "insightTrafficSourceType", sort="-views"),
        "countries": q("views,estimatedMinutesWatched", "country", sort="-views", max_results=25),
        "retention": q("audienceWatchRatio,relativeRetentionPerformance", "elapsedVideoTimeRatio", sort="elapsedVideoTimeRatio"),
    }


def write_report_xlsx(report: dict[str, pd.DataFrame], path: str) -> None:
    """Write each report table to its own sheet of an Excel file."""
    with pd.ExcelWriter(path) as writer:
        for name, df in report.items():
            df.to_excel(writer, sheet_name=name, index=False)
