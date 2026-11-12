from unittest.mock import MagicMock, patch

from youtube_tools.api import search_video, search_video_url, search_video_urls

FAKE_SEARCH_RESPONSE = {
    "items": [
        {"id": {"videoId": "dQw4w9WgXcQ"}},
    ]
}

FAKE_SEARCH_RESPONSE_WITH_SNIPPET = {
    "items": [
        {
            "id": {"videoId": "dQw4w9WgXcQ"},
            "snippet": {"title": "Rick Astley - Never Gonna Give You Up"},
        },
    ]
}

FAKE_EMPTY_RESPONSE = {"items": []}


def _mock_response(payload):
    mock_response = MagicMock()
    mock_response.json.return_value = payload
    mock_response.raise_for_status.return_value = None
    return mock_response


@patch("youtube_tools.api.requests.get")
def test_search_video_url_returns_url(mock_get):
    mock_get.return_value = _mock_response(FAKE_SEARCH_RESPONSE)

    url = search_video_url("never gonna give you up", api_key="fake-key")

    assert url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


@patch("youtube_tools.api.requests.get")
def test_search_video_url_returns_none_when_no_results(mock_get):
    mock_get.return_value = _mock_response(FAKE_EMPTY_RESPONSE)

    url = search_video_url("asdkjhaskjdhaksjdh", api_key="fake-key")

    assert url is None


@patch("youtube_tools.api.requests.get")
def test_search_video_urls_maps_each_query(mock_get):
    mock_get.return_value = _mock_response(FAKE_SEARCH_RESPONSE)

    results = search_video_urls(["query one", "query two"], api_key="fake-key")

    assert results == {
        "query one": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "query two": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    }
    assert mock_get.call_count == 2


@patch("youtube_tools.api.requests.get")
def test_search_video_returns_title_and_url(mock_get):
    mock_get.return_value = _mock_response(FAKE_SEARCH_RESPONSE_WITH_SNIPPET)

    result = search_video("never gonna give you up", api_key="fake-key")

    assert result == {
        "title": "Rick Astley - Never Gonna Give You Up",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    }


@patch("youtube_tools.api.requests.get")
def test_search_video_returns_none_when_no_results(mock_get):
    mock_get.return_value = _mock_response(FAKE_EMPTY_RESPONSE)

    result = search_video("asdkjhaskjdhaksjdh", api_key="fake-key")

    assert result is None


def test_extract_playlist_id_from_url_and_bare_id():
    from youtube_tools.api import extract_playlist_id

    assert extract_playlist_id("https://www.youtube.com/playlist?list=PLabc123") == "PLabc123"
    assert extract_playlist_id("PLabc123") == "PLabc123"


@patch("youtube_tools.api.requests.get")
def test_list_playlist_items_paginates(mock_get):
    from youtube_tools.api import list_playlist_items

    def page(vid, token):
        payload = {"items": [{"snippet": {"position": 0, "title": vid, "videoOwnerChannelTitle": "c",
                                          "publishedAt": "2026-01-01T00:00:00Z",
                                          "resourceId": {"videoId": vid}}}]}
        if token:
            payload["nextPageToken"] = token
        return _mock_response(payload)

    mock_get.side_effect = [page("v1", "t2"), page("v2", None)]

    rows = list_playlist_items("PLabc", api_key="fake-key")

    assert [r["url"] for r in rows] == [
        "https://www.youtube.com/watch?v=v1",
        "https://www.youtube.com/watch?v=v2",
    ]
    assert mock_get.call_args_list[1].kwargs["params"]["pageToken"] == "t2"
