import argparse
from datetime import date

import pandas as pd

from youtube_tools import filter_by_date_range, unique_tracks

INPUT_PATH = "data/Richie_Hawtin_tracklists.xlsx"
UNITS_PER_SEARCH = 100
DAILY_QUOTA = 10_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filter DJ sets by date range, dedupe tracks, and estimate YouTube search quota."
    )
    parser.add_argument("--start", type=date.fromisoformat, default=date(2004, 1, 1), help="YYYY-MM-DD")
    parser.add_argument("--end", type=date.fromisoformat, default=date.today(), help="YYYY-MM-DD")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    df = pd.read_excel(INPUT_PATH)
    print(f"Total rows: {len(df)}")

    filtered = filter_by_date_range(df, args.start, args.end)
    print(f"Rows in [{args.start} .. {args.end}]: {len(filtered)}")
    print(f"Unique mix_titles (DJ sets) in range: {filtered['mix_title'].nunique()}")

    tracks = unique_tracks(filtered)
    print(f"Unique tracks: {len(tracks)}")

    units_needed = len(tracks) * UNITS_PER_SEARCH
    days_needed = -(-units_needed // DAILY_QUOTA)  # ceil division
    print()
    print(f"Quota estimate: {len(tracks)} tracks x {UNITS_PER_SEARCH} units = {units_needed} units")
    print(f"At the default {DAILY_QUOTA} units/day quota: ~{days_needed} day(s) to resolve all of them")


if __name__ == "__main__":
    main()
