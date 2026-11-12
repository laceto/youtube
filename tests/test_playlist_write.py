from unittest.mock import MagicMock, patch

import requests

from youtube_tools.api import (
    add_video_to_playlist,
    add_videos_to_playlist,
    create_playlist,
    extract_video_id,
)


def _mock_response(payload):
    mock_response = MagicMock()
    mock_response.json.return_value = payload
    mock_response.raise_for_status.return_value = None
    return mock_response


def test_extract_video_id_handles_watch_short_and_bare():
    assert extract_video_id("https://www.youtube.com/watch?v=abc123&list=PL1") == "abc123"
    assert extract_video_id("https://youtu.be/abc123?t=5") == "abc123"
    assert extract_video_id("https://www.youtube.com/shorts/abc123") == "abc123"
    assert extract_video_id("abc123") == "abc123"


@patch("youtube_tools.api.requests.post")
def test_create_playlist_posts_body_and_returns_id(mock_post):
    mock_post.return_value = _mock_response({"id": "PL999"})

    playlist_id = create_playlist("Mix", description="d", privacy="unlisted", access_token="tok")

    assert playlist_id == "PL999"
    kwargs = mock_post.call_args.kwargs
    assert kwargs["json"]["snippet"]["title"] == "Mix"
    assert kwargs["json"]["status"]["privacyStatus"] == "unlisted"
    assert kwargs["headers"] == {"Authorization": "Bearer tok"}


@patch("youtube_tools.api.requests.post")
def test_add_video_to_playlist_sends_video_id(mock_post):
    mock_post.return_value = _mock_response({"id": "item1"})

    item_id = add_video_to_playlist("PL999", "https://youtu.be/abc123", access_token="tok")

    assert item_id == "item1"
    body = mock_post.call_args.kwargs["json"]["snippet"]
    assert body["playlistId"] == "PL999"
    assert body["resourceId"]["videoId"] == "abc123"


@patch("youtube_tools.api.requests.post")
def test_add_videos_to_playlist_maps_failures_to_none(mock_post):
    ok = _mock_response({"id": "item1"})
    bad = MagicMock()
    bad.raise_for_status.side_effect = requests.HTTPError("403")
    mock_post.side_effect = [ok, bad]

    result = add_videos_to_playlist("PL999", ["a", "b"], access_token="tok")

    assert result == {"a": "item1", "b": None}
