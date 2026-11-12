import json

import pandas as pd

SYSTEM_PROMPT = """You are a music metadata parser for a DJ tracklist of techno, minimal, \
tech house, and house records (Richie Hawtin sets).

Each input is a raw, messy track title string exactly as scraped from a tracklist site. \
It may pack together the clean track title, an optional remixer/edit credit, and an \
optional record label with catalog number, for example:
- "Cropstar [Pressure - PSR082]"
- "Tuned Hips (Matheo Velez Remix) [Medicine Musique - MED035]"
- "Enter Space Preview"

Split it into exactly three fields and respond with ONLY a single-line JSON object, no \
markdown code fences, no commentary:
{"title": "<clean track title, no remix/label info>", "remixer": "<remixer or editor name, or null if none>", "label": "<record label name only, no catalog number, or null if none>"}

Rules:
- Strip bracketed "[Label - CatalogNumber]" and parenthetical "(Remixer Name Remix)" / \
"(Remixer Name Edit)" segments out of the title.
- "label" is the label name only (e.g. "Medicine Musique"), never the catalog number \
(e.g. "MED035").
- If there is no remixer credit, remixer must be null (not "Original Mix").
- If there is no bracketed label info, label must be null.
- Never invent information that isn't present in the input."""


def build_sanitize_items(df: pd.DataFrame, column: str = "title") -> list[dict]:
    """Build kitai chat-batch items ({"id", "content"}) from a DataFrame column, keyed by row index."""
    return [
        {"id": str(idx), "content": str(value)}
        for idx, value in df[column].items()
        if pd.notna(value) and str(value).strip()
    ]


def extract_sanitized_fields(text: str) -> dict:
    """Parse a model response into {"title", "remixer", "label"}, raising on malformed output."""
    cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(cleaned)
    if not isinstance(data, dict) or "title" not in data:
        raise ValueError(f"Malformed sanitize response: {text!r}")
    return {
        "title": data.get("title"),
        "remixer": data.get("remixer"),
        "label": data.get("label"),
    }


def merge_sanitized_results(df: pd.DataFrame, pairs: list[tuple[str, dict]]) -> pd.DataFrame:
    """Merge (custom_id, fields) pairs from parse_chat_results back onto `df` by row index.

    Adds "sanitized_title", "remixer", "label" columns; rows with no result stay None.
    """
    result = df.copy()
    result["sanitized_title"] = None
    result["remixer"] = None
    result["label"] = None

    for custom_id, fields in pairs:
        idx = int(custom_id.removeprefix("custom_id_"))
        result.loc[idx, "sanitized_title"] = fields.get("title")
        result.loc[idx, "remixer"] = fields.get("remixer")
        result.loc[idx, "label"] = fields.get("label")

    return result
