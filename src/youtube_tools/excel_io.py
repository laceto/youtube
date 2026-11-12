import pandas as pd


def read_queries(path: str, column: str, n: int | None = None) -> list[str]:
    """Read search-query strings from a column of an Excel file, optionally limited to the first n rows."""
    df = pd.read_excel(path, usecols=[column])
    if n is not None:
        df = df.head(n)
    return df[column].dropna().astype(str).tolist()


def write_playlist_xlsx(rows: list[dict], path: str) -> None:
    """Write playlist rows (as returned by list_playlist_items) to an Excel file."""
    pd.DataFrame(rows).to_excel(path, index=False)
