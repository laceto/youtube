"""List the videos of a public YouTube playlist and save them to an .xlsx file.

Usage: python scripts/list_playlist.py <playlist-url-or-id> [output.xlsx]
"""
import sys

from youtube_tools import list_playlist_items, write_playlist_xlsx

if __name__ == "__main__":
    playlist = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "data/playlist.xlsx"
    rows = list_playlist_items(playlist)
    write_playlist_xlsx(rows, out)
    for r in rows:
        print(f"{r['position']:>3}  {r['title']}  {r['url']}")
    print(f"\n{len(rows)} videos -> {out}")
