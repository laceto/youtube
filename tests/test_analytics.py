from unittest.mock import MagicMock, patch

import pytest

from youtube_tools.analytics import get_video_stats, list_my_uploads, query_report


def _resp(payload):
    m = MagicMock()
    m.json.return_value = payload
    m.raise_for_status.return_value = None
    return m


@patch("youtube_tools.analytics.requests.get")
def test_list_my_uploads_follows_uploads_playlist(mock_get):
    mock_get.side_effect = [
        _resp({"items": [{"contentDetails": {"relatedPlaylists": {"uploads": "UU1"}}}]}),
        _resp({"items": [{"snippet": {"resourceId": {"videoId": "v1"}, "title": "T", "publishedAt": "2026-01-01T00:00:00Z"}}]}),
    ]
    assert list_my_uploads(access_token="tok") == [
        {"video_id": "v1", "title": "T", "published_at": "2026-01-01T00:00:00Z"}
    ]
    assert mock_get.call_args.kwargs["params"]["playlistId"] == "UU1"


@patch("youtube_tools.analytics.requests.get")
def test_get_video_stats_parses_counters(mock_get):
    mock_get.return_value = _resp({"items": [{
        "snippet": {"title": "T", "publishedAt": "2026-01-01T00:00:00Z"},
        "contentDetails": {"duration": "PT5M"},
        "statistics": {"viewCount": "10", "likeCount": "2", "commentCount": "1"},
    }]})
    stats = get_video_stats("https://youtu.be/abc", access_token="tok")
    assert (stats["video_id"], stats["views"], stats["likes"], stats["comments"]) == ("abc", 10, 2, 1)


@patch("youtube_tools.analytics.requests.get")
def test_get_video_stats_raises_when_missing(mock_get):
    mock_get.return_value = _resp({"items": []})
    with pytest.raises(ValueError):
        get_video_stats("nope", access_token="tok")


@patch("youtube_tools.analytics.requests.get")
def test_query_report_builds_dataframe_and_filter(mock_get):
    mock_get.return_value = _resp({
        "columnHeaders": [{"name": "day"}, {"name": "views"}],
        "rows": [["2026-01-01", 5], ["2026-01-02", 7]],
    })
    df = query_report("abc", "views", "day", end_date="2026-02-01", access_token="tok")
    assert list(df.columns) == ["day", "views"] and df["views"].sum() == 12
    assert mock_get.call_args.kwargs["params"]["filters"] == "video==abc"
