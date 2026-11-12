"""Create a YouTube playlist and add the videos listed in an .xlsx column.

Usage: python scripts/create_playlist.py <input.xlsx> <url-column> <playlist-title> [privacy]
First run opens a browser for Google consent; the token is cached at YOUTUBE_TOKEN_JSON.
"""
import sys

from youtube_tools import add_videos_to_playlist, create_playlist, read_queries

if __name__ == "__main__":
    path, column, title = sys.argv[1:4]
    privacy = sys.argv[4] if len(sys.argv) > 4 else "private"
    urls = read_queries(path, column)
    playlist_id = create_playlist(title, privacy=privacy)
    print(f"Created playlist {playlist_id}: https://www.youtube.com/playlist?list={playlist_id}")
    results = add_videos_to_playlist(playlist_id, urls)
    for url, item_id in results.items():
        print(f"{'ok  ' if item_id else 'FAIL'} {url}")
    print(f"\n{sum(1 for v in results.values() if v)}/{len(results)} added")
