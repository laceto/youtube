import re
from datetime import date

import pandas as pd

_DATE_PATTERN = re.compile(r"^(\d{4})(?:-(\d{2})-(\d{2}))?\s*-\s*")


def parse_mix_date(mix_title: str) -> date:
    """Parse the leading date out of a mix_title like '2013-07-18 - ...' or '1995 - ...'."""
    match = _DATE_PATTERN.match(mix_title)
    if not match:
        raise ValueError(f"mix_title has no leading date: {mix_title!r}")
    year = int(match.group(1))
    month = int(match.group(2)) if match.group(2) else 1
    day = int(match.group(3)) if match.group(3) else 1
    return date(year, month, day)


def filter_by_date_range(df: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    """Return only rows whose mix_title date falls within [start, end]."""
    mix_dates = df["mix_title"].apply(parse_mix_date)
    return df[(mix_dates >= start) & (mix_dates <= end)]


def unique_tracks(df: pd.DataFrame, column: str = "raw") -> list[str]:
    """Return the deduplicated, order-preserved list of track strings from `column`."""
    return df[column].dropna().astype(str).drop_duplicates().tolist()
