import pandas as pd
import pytest

from youtube_tools.sanitize_tracklist import (
    build_sanitize_items,
    extract_sanitized_fields,
    merge_sanitized_results,
)


def test_build_sanitize_items_uses_row_index_as_id():
    df = pd.DataFrame({"title": ["Cropstar [Pressure - PSR082]", "Enter Space Preview"]})

    items = build_sanitize_items(df)

    assert items == [
        {"id": "0", "content": "Cropstar [Pressure - PSR082]"},
        {"id": "1", "content": "Enter Space Preview"},
    ]


def test_build_sanitize_items_skips_missing_values():
    df = pd.DataFrame({"title": ["Cropstar", None, "  ", "Ayer"]})

    items = build_sanitize_items(df)

    assert [item["id"] for item in items] == ["0", "3"]


def test_extract_sanitized_fields_parses_plain_json():
    text = '{"title": "Cropstar", "remixer": null, "label": "Pressure"}'

    fields = extract_sanitized_fields(text)

    assert fields == {"title": "Cropstar", "remixer": None, "label": "Pressure"}


def test_extract_sanitized_fields_strips_markdown_fence():
    text = '```json\n{"title": "Tuned Hips", "remixer": "Matheo Velez", "label": "Medicine Musique"}\n```'

    fields = extract_sanitized_fields(text)

    assert fields == {
        "title": "Tuned Hips",
        "remixer": "Matheo Velez",
        "label": "Medicine Musique",
    }


def test_extract_sanitized_fields_raises_on_malformed_response():
    with pytest.raises(Exception):
        extract_sanitized_fields("not json at all")


def test_merge_sanitized_results_maps_pairs_back_by_row_index():
    df = pd.DataFrame({"title": ["Cropstar [Pressure - PSR082]", "Enter Space Preview"]})
    pairs = [
        ("custom_id_0", {"title": "Cropstar", "remixer": None, "label": "Pressure"}),
        ("custom_id_1", {"title": "Enter Space Preview", "remixer": None, "label": None}),
    ]

    merged = merge_sanitized_results(df, pairs)

    assert merged.loc[0, "sanitized_title"] == "Cropstar"
    assert merged.loc[0, "label"] == "Pressure"
    assert merged.loc[1, "sanitized_title"] == "Enter Space Preview"
    assert merged.loc[1, "label"] is None
    assert merged.loc[0, "title"] == "Cropstar [Pressure - PSR082]"


def test_merge_sanitized_results_leaves_unmatched_rows_none():
    df = pd.DataFrame({"title": ["Cropstar", "Ayer"]})
    pairs = [("custom_id_0", {"title": "Cropstar", "remixer": None, "label": None})]

    merged = merge_sanitized_results(df, pairs)

    assert merged.loc[1, "sanitized_title"] is None
