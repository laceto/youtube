import pandas as pd

from youtube_tools import read_queries, search_video_urls

INPUT_PATH = "data/Richie_Hawtin_tracklists.xlsx"
QUERY_COLUMN = "raw"
OUTPUT_PATH = "data/Richie_Hawtin_tracklists_first10_urls.csv"


def main() -> None:
    queries = read_queries(INPUT_PATH, QUERY_COLUMN, n=10)
    results = search_video_urls(queries)

    df = pd.DataFrame(
        {"query": list(results.keys()), "youtube_url": list(results.values())}
    )
    df.to_csv(OUTPUT_PATH, index=False)
    print(df.to_string(index=False))
    print(f"\nSaved {len(df)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
