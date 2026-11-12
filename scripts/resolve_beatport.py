import argparse
from pathlib import Path

import pandas as pd

from youtube_tools import build_search_query, read_beatport_playlist, search_video
from youtube_tools.resolve import resolve_matches

CACHE_PATH = "data/beatport/youtube_matches.xlsx"
UNITS_PER_SEARCH = 100


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add YouTube title/URL to a parsed Beatport dump.")
    parser.add_argument("input", help="e.g. data/beatport/info_beatport_20261009.txt")
    parser.add_argument("--limit", type=int, default=None, help="only resolve the first N tracks")
    parser.add_argument("--dry-run", action="store_true", help="only count the searches needed")
    return parser.parse_args()


def load_cache(path: str) -> dict[str, dict[str, str | None]]:
    if not Path(path).exists():
        return {}
    df = pd.read_excel(path)
    return {
        row["query"]: {"title": row["youtube_title"], "url": row["youtube_url"]}
        for _, row in df.iterrows()
        if pd.notna(row["youtube_url"])
    }


def main() -> None:
    args = parse_args()
    tracks = read_beatport_playlist(args.input)
    if args.limit:
        tracks = tracks.head(args.limit).copy()
    tracks["query"] = tracks.apply(build_search_query, axis=1)

    cache = load_cache(CACHE_PATH)
    misses = [q for q in tracks["query"] if q not in cache]
    print(f"{len(tracks)} tracks, {len(tracks) - len(misses)} cached, {len(misses)} to search "
          f"(~{len(misses) * UNITS_PER_SEARCH} quota units)")
    if args.dry_run:
        return

    results, error = resolve_matches(tracks["query"].tolist(), cache, search_video)
    tracks["youtube_title"] = tracks["query"].map(lambda q: (results.get(q) or {}).get("title"))
    tracks["youtube_url"] = tracks["query"].map(lambda q: (results.get(q) or {}).get("url"))

    suffix = f"_first{args.limit}" if args.limit else ""
    output = str(Path(args.input).with_suffix("")) + f"{suffix}_youtube.xlsx"
    tracks.to_excel(output, index=False)
    print(f"Saved {len(tracks)} rows ({tracks['youtube_url'].notna().sum()} with a URL) to {output}")
    if error:
        print(f"STOPPED EARLY: {error}")


if __name__ == "__main__":
    main()
