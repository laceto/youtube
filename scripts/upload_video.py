"""Upload a video file to your YouTube channel.

Usage: python scripts/upload_video.py <file> <title> [description] [privacy]
privacy: private (default) | unlisted | public
First run may open a browser for Google consent; the token is cached at YOUTUBE_TOKEN_JSON.
"""
import sys

from youtube_tools import upload_video

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    path, title = sys.argv[1:3]
    description = sys.argv[3] if len(sys.argv) > 3 else ""
    privacy = sys.argv[4] if len(sys.argv) > 4 else "private"
    video_id = upload_video(path, title, description, privacy)
    print(f"Uploaded: https://www.youtube.com/watch?v={video_id} ({privacy})")
