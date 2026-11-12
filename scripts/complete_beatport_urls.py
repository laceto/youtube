import argparse

import pandas as pd

from youtube_tools import search_video
from youtube_tools.resolve import resolve_matches


def main() -> None:
    parser = argparse.ArgumentParser(description="Fill missing youtube_url rows of a resolved Beatport xlsx in place.")
    parser.add_argument("path")
    path = parser.parse_args().path

    df = pd.read_excel(path)
    # reuse already-resolved rows as the cache so only the blanks hit the API
    done = df[df["youtube_url"].notna()]
    cache = {r["query"]: {"title": r["youtube_title"], "url": r["youtube_url"]} for _, r in done.iterrows()}
    results, error = resolve_matches(df["query"].tolist(), cache, search_video)

    missing = df["youtube_url"].isna()
    df.loc[missing, "youtube_title"] = df.loc[missing, "query"].map(lambda q: (results.get(q) or {}).get("title"))
    df.loc[missing, "youtube_url"] = df.loc[missing, "query"].map(lambda q: (results.get(q) or {}).get("url"))
    df.to_excel(path, index=False)
    print(f"{df['youtube_url'].notna().sum()}/{len(df)} rows have a URL; saved to {path}")
    if error:
        print(f"STOPPED EARLY: {error}")


if __name__ == "__main__":
    main()
