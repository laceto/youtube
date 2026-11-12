from datetime import date
from pathlib import Path

import pandas as pd

from youtube_tools.beatport import parse_beatport_text, read_beatport_playlist

SAMPLE_PATH = Path(__file__).resolve().parents[1] / "data" / "beatport" / "info_beatport.txt"


def test_parse_beatport_text_parses_original_mix_track():
    df = read_beatport_playlist(SAMPLE_PATH)
    row = df.iloc[0]

    assert row["release"] == "Even You EP"
    assert row["track_number"] == 1
    assert row["title"] == "Golden Party"
    assert row["mix_type"] == "Original Mix"
    assert row["artists"] == "LondonGround, BizZa"
    assert row["label"] == "Cecille"
    assert pd.isna(row["remixer"])
    assert row["genre"] == "Deep House"
    assert row["bpm"] == 128
    assert row["key"] == "Bb Major"
    assert row["published_date"] == date(2026, 5, 1)
    assert row["price"] == "€1.39"


def test_parse_beatport_text_parses_remix_track_with_remixer_line():
    df = read_beatport_playlist(SAMPLE_PATH)
    row = df[df["track_number"] == 3].iloc[0]

    assert row["release"] == "Restrained / Consumed Remix"
    assert row["title"] == "Consumed Edit-Select"
    assert row["mix_type"] == "Remix"
    assert row["artists"] == "Gary Beck"
    assert row["label"] == "Edit Select"
    assert row["remixer"] == "Edit Select"
    assert row["bpm"] == 125
    assert row["key"] == "F Major"
    assert row["published_date"] == date(2009, 3, 9)


def test_parse_beatport_text_returns_one_row_per_track():
    df = read_beatport_playlist(SAMPLE_PATH)

    assert len(df) == 18
    assert df["track_number"].tolist() == list(range(1, 19))


def test_parse_beatport_text_skips_header_preamble():
    text = "\n".join(
        [
            "",
            "Titolo / Artisti",
            "Etichetta / Remixer",
            "Genere / BPM & Chiave",
            "Pubblicato",
            " ",
            "Some EP",
            "1",
            "",
            "",
            "",
            "Track Name Original Mix",
            "Some Artist",
            "Some Label",
            "House",
            "120 BPM - A Minor",
            "2020-01-01",
            "€1.39",
        ]
    )

    df = parse_beatport_text(text)

    assert len(df) == 1
    assert df.iloc[0]["title"] == "Track Name"


def test_parse_beatport_text_handles_missing_first_release_title():
    text = "1\nTropic Original Mix\nGaga, Mateo & Spirit\nSode Records\nMinimal / Deep Tech\n128 BPM - E Major\n2012-07-23\n€1.39\nRawgenic EP\n2\nNincompoop Original Mix\nmonokompatibel\nTrapez Ltd\nTech House\n125 BPM - Gb Major\n2021-09-24\n€1.39\n"
    df = parse_beatport_text(text)

    assert len(df) == 2
    assert pd.isna(df.iloc[0]["release"])
    assert df.iloc[0]["title"] == "Tropic"
    assert df.iloc[1]["release"] == "Rawgenic EP"
    assert df.iloc[1]["track_number"] == 2


def test_parse_beatport_text_handles_missing_price_and_extra_remixer_line():
    text = (
        "Rhumba Macumba\n59\nRhumba Macumba Rhumba Mix\nBrothers' Vibe\nJersey Underground Recordings\nHouse\n126 BPM - C Minor\n2002-07-01\n"
        "Closed Circuit Dreams\n60\nFalse Memory Original Mix\nSomeone\nSome Label\nSome Remixer\nTechno\n128 BPM - A Minor\n2010-01-01\n€1.39\n"
    )
    df = parse_beatport_text(text)

    assert len(df) == 2
    assert pd.isna(df.iloc[0]["price"])
    assert df.iloc[1]["release"] == "Closed Circuit Dreams"
    assert df.iloc[1]["remixer"] == "Some Remixer"
    assert df.iloc[1]["price"] == "€1.39"


NEW_FORMAT_SAMPLE = """#
Titolo  Artista  Remixer
Etichetta  Genere  Sottogenere
Uscita
BPM
Chiave
Tempo
1
Tacky Wake Up

Tacky Wake Up Marek Hemmann Remix
Sweet N Candy  Marek Hemmann
Play My Track Recordings
Minimal / Deep Tech  Minimal House
Apr 11, 2013
129
C Maj
6:15

€1.39
2
Esclusivo
Beyond Borders

Beyond Borders Original mix
Nicole Moudaber
WTF! Music
Deep House
Oct 16, 2026
126
F Min
8:09

Nel carrello
3
Stripped

Stripped Original Mix
Click Box
Items & Things
Tech House
Sep 03, 2008
123
Ab Maj
5:20
"""


def test_parse_new_table_format():
    df = parse_beatport_text(NEW_FORMAT_SAMPLE)

    assert list(df["track_number"]) == [1, 2, 3]
    first = df.iloc[0]
    assert first["title"] == "Tacky Wake Up Marek Hemmann"
    assert first["mix_type"] == "Remix"
    assert first["artists"] == "Sweet N Candy"
    assert first["remixer"] == "Marek Hemmann"
    assert first["genre"] == "Minimal / Deep Tech"
    assert first["subgenre"] == "Minimal House"
    assert first["published_date"] == date(2013, 4, 11)
    assert (first["bpm"], first["key"], first["length"], first["price"]) == (129, "C Maj", "6:15", "€1.39")
    assert df.iloc[1]["title"] == "Beyond Borders Original mix"  # lowercase 'mix' is not a recognised suffix
    assert df.iloc[1]["price"] == "Nel carrello"
    assert pd.isna(df.iloc[2]["price"])
