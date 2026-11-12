from unittest.mock import MagicMock, patch

import pytest

from youtube_tools.api import upload_video


def _resp(payload=None, headers=None):
    m = MagicMock()
    m.json.return_value = payload or {}
    m.headers = headers or {}
    m.raise_for_status.return_value = None
    return m


@patch("youtube_tools.api.requests.put")
@patch("youtube_tools.api.requests.post")
def test_upload_video_starts_session_then_puts_file(mock_post, mock_put, tmp_path):
    f = tmp_path / "mix.mp4"
    f.write_bytes(b"12345")
    mock_post.return_value = _resp(headers={"Location": "https://upload/session"})
    mock_put.return_value = _resp({"id": "vid123"})

    vid = upload_video(str(f), "Mix", description="d", privacy="unlisted", access_token="tok")

    assert vid == "vid123"
    post_kwargs = mock_post.call_args.kwargs
    assert post_kwargs["params"]["uploadType"] == "resumable"
    assert post_kwargs["json"]["snippet"]["title"] == "Mix"
    assert post_kwargs["json"]["status"]["privacyStatus"] == "unlisted"
    assert post_kwargs["headers"]["Authorization"] == "Bearer tok"
    assert post_kwargs["headers"]["X-Upload-Content-Length"] == "5"
    assert mock_put.call_args.args[0] == "https://upload/session"


def test_upload_video_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        upload_video(str(tmp_path / "nope.mp4"), "t", access_token="tok")
