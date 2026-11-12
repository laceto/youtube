import re
from datetime import date, datetime
from pathlib import Path

import pandas as pd

_HEADER_LINES = [
    "Titolo / Artisti",
    "Etichetta / Remixer",
    "Genere / BPM & Chiave",
    "Pubblicato",
]

_MIX_SUFFIX_PATTERN = re.compile(r"^(.*?)\s+(Original Mix|Remix)$")
_BPM_KEY_PATTERN = re.compile(r"^(\d+)\s*BPM\s*-\s*(.+)$")


def _split_mix_name(title_line: str) -> tuple[str, str | None]:
    """Split 'Golden Party Original Mix' into ('Golden Party', 'Original Mix')."""
    match = _MIX_SUFFIX_PATTERN.match(title_line)
    if not match:
        return title_line, None
    return match.group(1), match.group(2)


def _split_bpm_key(bpm_key_line: str) -> tuple[int, str]:
    """Split '128 BPM - Bb Major' into (128, 'Bb Major')."""
    match = _BPM_KEY_PATTERN.match(bpm_key_line)
    if not match:
        raise ValueError(f"bpm/key line does not match expected format: {bpm_key_line!r}")
    return int(match.group(1)), match.group(2)


_NEW_HEADER = ["#", "Titolo  Artista  Remixer", "Etichetta  Genere  Sottogenere", "Uscita", "BPM", "Chiave", "Tempo"]
_NEW_DATE_PATTERN = re.compile(r"^[A-Z][a-z]{2} \d{2}, \d{4}$")
_COL_SPLIT = re.compile(r"\s{2,}")


def _parse_new_format(lines: list[str]) -> pd.DataFrame:
    """Parse the newer Italian table dump (header '#', 'Titolo Artista Remixer', ...).

    Per track (non-blank lines): rank, [Esclusivo badge], title, mix line, "artists  remixer",
    label, "genre  subgenre", "Mon DD, YYYY", bpm, key, length, price or "Nel carrello".
    The price line may be absent entirely (next rank follows the length).
    """
    idx = len(_NEW_HEADER) if lines[: len(_NEW_HEADER)] == _NEW_HEADER else 0
    records = []
    while idx < len(lines):
        expected = len(records) + 1
        if lines[idx] != str(expected):
            raise ValueError(f"expected rank {expected}, got {lines[idx]!r}")
        date_idx = next(i for i in range(idx + 1, len(lines)) if _NEW_DATE_PATTERN.match(lines[i]))
        head = lines[idx + 1 : date_idx]
        if len(head) not in (5, 6):
            raise ValueError(f"unexpected lines before date for track {expected}: {head!r}")
        title_line, mix_line, artists_line, label, genre_line = head[-5:]

        artists, *rest = _COL_SPLIT.split(artists_line)
        remixer = rest[0] if rest else None
        genre, *subs = _COL_SPLIT.split(genre_line)
        subgenre = subs[0] if subs else None

        published_date = datetime.strptime(lines[date_idx], "%b %d, %Y").date()
        bpm = int(lines[date_idx + 1])
        key = lines[date_idx + 2]
        length = lines[date_idx + 3]
        price_missing = date_idx + 4 >= len(lines) or lines[date_idx + 4] == str(expected + 1)
        price = None if price_missing else lines[date_idx + 4]
        idx = date_idx + (4 if price_missing else 5)

        title, mix_type = _split_mix_name(mix_line)
        records.append(
            {
                "release": title_line,
                "track_number": expected,
                "title": title,
                "mix_type": mix_type,
                "artists": artists,
                "label": label,
                "remixer": remixer,
                "genre": genre,
                "subgenre": subgenre,
                "bpm": bpm,
                "key": key,
                "length": length,
                "published_date": published_date,
                "price": price,
            }
        )
    return pd.DataFrame(records)


def parse_beatport_text(text: str) -> pd.DataFrame:
    """Parse a Beatport playlist text dump (as pasted from the playlist page) into a DataFrame.

    Each track is a fixed run of non-blank lines: release title, playlist index, track
    title+mix, artists, label, an optional remixer line, genre, "<bpm> BPM - <key>", published date, price.
    The newer table layout (starting with a '#' header line) is handled by `_parse_new_format`.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if lines and lines[0] == "#":
        return _parse_new_format(lines)

    idx = len(_HEADER_LINES) if lines[: len(_HEADER_LINES)] == _HEADER_LINES else 0

    records = []
    while idx < len(lines):
        if lines[idx].isdigit():
            # Partial paste: the first track's release title was cut off, rank comes first.
            release = None
        else:
            release = lines[idx]
            idx += 1
        track_number = int(lines[idx])
        title_line = lines[idx + 1]
        artists = lines[idx + 2]
        label = lines[idx + 3]
        idx += 4

        # Anchor on the BPM line: genre is right before it, an optional remixer line before that.
        bpm_idx = next(i for i in range(idx, len(lines)) if _BPM_KEY_PATTERN.match(lines[i]))
        remixer = lines[idx] if bpm_idx - idx == 2 else None
        if bpm_idx - idx > 2:
            raise ValueError(f"unexpected lines between label and BPM for track {track_number}: {lines[idx:bpm_idx]!r}")
        genre = lines[bpm_idx - 1]
        bpm, key = _split_bpm_key(lines[bpm_idx])
        published_date = datetime.strptime(lines[bpm_idx + 1], "%Y-%m-%d").date()
        # A track with no price line is followed directly by the next rank (release comes first otherwise).
        price_missing = bpm_idx + 3 < len(lines) and lines[bpm_idx + 3].isdigit()
        price = None if price_missing else lines[bpm_idx + 2]
        idx = bpm_idx + 2 if price_missing else bpm_idx + 3

        title, mix_type = _split_mix_name(title_line)

        records.append(
            {
                "release": release,
                "track_number": track_number,
                "title": title,
                "mix_type": mix_type,
                "artists": artists,
                "label": label,
                "remixer": remixer,
                "genre": genre,
                "bpm": bpm,
                "key": key,
                "published_date": published_date,
                "price": price,
            }
        )

    return pd.DataFrame(records)


def read_beatport_playlist(path: str | Path) -> pd.DataFrame:
    """Read and parse a Beatport playlist text dump from `path`."""
    text = Path(path).read_text(encoding="utf-8")
    return parse_beatport_text(text)


def build_search_query(row) -> str:
    """Build a YouTube search query string like 'Artists - Title (Mix Type)' from a parsed track row."""
    query = f"{row['artists']} - {row['title']}"
    mix_type = row["mix_type"]
    if pd.notna(mix_type):
        query += f" ({mix_type})"
    return query
