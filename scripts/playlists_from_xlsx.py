"""Resolve tracks to YouTube videos, then create one private playlist per group and add them.

Input xlsx needs a playlist-name column and a search-query column (default: Playlist_name, ToSearch).
Stage 1 (always): search each query (100 quota units each, cached) -> <input>_matches.xlsx.
Stage 2 (with --create): create each playlist (50 units) and add its matched videos (50 units each).

Usage: python scripts/playlists_from_xlsx.py data/bassline_top10.xlsx [--create] [--dry-run]
"""
import argparse
from pathlib import Path

import pandas as pd

from youtube_tools import add_videos_to_playlist, create_playlist, search_video
from youtube_tools.resolve import resolve_matches

UNITS_SEARCH, UNITS_WRITE = 100, 50


def create_from_matches(matches: pd.DataFrame, name_col: str) -> None:
    """Create one private playlist per name and add its rows that have a youtube_url."""
    for name, group in matches.dropna(subset=["youtube_url"]).groupby(name_col, sort=False):
        playlist_id = create_playlist(str(name), privacy="private")
        added = add_videos_to_playlist(playlist_id, group["youtube_url"].tolist())
        print(f"{name}: {sum(1 for v in added.values() if v)}/{len(added)} added "
              f"https://www.youtube.com/playlist?list={playlist_id}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--name-col", default="Playlist_name")
    parser.add_argument("--query-col", default="ToSearch")
    parser.add_argument("--create", action="store_true", help="create playlists from the matches file")
    parser.add_argument("--dry-run", action="store_true", help="only print the quota estimate")
    args = parser.parse_args()

    src = pd.read_excel(args.input, sheet_name=0)[[args.name_col, args.query_col]].dropna()
    matches_path = Path(args.input).with_name(Path(args.input).stem + "_matches.xlsx")

    if args.create and matches_path.exists() and not args.dry_run:
        # Use the reviewed matches file as-is (blank a youtube_url cell to skip a track); no searching.
        create_from_matches(pd.read_excel(matches_path), args.name_col)
        return

    cache: dict[str, dict] = {}
    if matches_path.exists():
        old = pd.read_excel(matches_path)
        cache = {r[args.query_col]: {"title": r["youtube_title"], "url": r["youtube_url"]}
                 for _, r in old.iterrows() if pd.notna(r["youtube_url"])}

    queries = src[args.query_col].astype(str).tolist()
    misses = [q for q in queries if q not in cache]
    n_playlists = src[args.name_col].nunique()
    est = len(misses) * UNITS_SEARCH + (n_playlists + len(queries)) * UNITS_WRITE * args.create
    print(f"{len(queries)} tracks, {len(misses)} to search, {n_playlists} playlists -> ~{est} quota units")
    if args.dry_run:
        return

    results, error = resolve_matches(queries, cache, search_video)
    src["youtube_title"] = src[args.query_col].map(lambda q: (results.get(q) or {}).get("title"))
    src["youtube_url"] = src[args.query_col].map(lambda q: (results.get(q) or {}).get("url"))
    src.to_excel(matches_path, index=False)
    print(f"matches -> {matches_path} ({src['youtube_url'].notna().sum()}/{len(src)} resolved)")
    if error:
        print(f"STOPPED: {error}")
        return
    if not args.create:
        print("Review the matches file, then re-run with --create.")
        return

    create_from_matches(src, args.name_col)


if __name__ == "__main__":
    main()
