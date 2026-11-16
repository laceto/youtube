# youtube-tools

Look up YouTube video URLs from a list of search queries, via the YouTube Data API v3.

## Setup

1. Get a YouTube Data API v3 key (see "YouTube API prerequisites" below).
2. Copy `.env.example` to `.env` and set `YOUTUBE_API_KEY`.
3. Install:

```bash
python -m venv venv
venv\Scripts\activate       # Windows
pip install -e ".[dev]"
```

## Usage

```python
from youtube_tools import search_video_urls

queries = ["never gonna give you up", "lofi hip hop radio"]
urls = search_video_urls(queries)
# {"never gonna give you up": "https://www.youtube.com/watch?v=...", ...}
```

## Tests

```bash
pytest
```

## YouTube API prerequisites

1. A Google Cloud project (console.cloud.google.com).
2. Enable the **YouTube Data API v3** for that project.
3. Create credentials: an **API key** is enough for read-only search (this package's use case).
   OAuth client credentials are only needed if you act on behalf of a user (uploading videos,
   managing playlists, reading private data).
4. Keep the key out of source control — it goes in `.env`, which is gitignored.
5. Be aware of quota: the default quota is 10,000 units/day, and a `search.list` call costs
   100 units — so ~100 lookups/day on the free quota. Request a quota increase in Cloud Console
   if you need more.

## Resolving Beatport dumps to YouTube links

`scripts/resolve_beatport.py <info_beatport_YYYYMMDD.txt>` parses a pasted Beatport dump, builds an
`Artists - Title (Mix)` query per track, and adds the top YouTube match (`youtube_title`,
`youtube_url`), writing `<input>_youtube.xlsx`. Options: `--dry-run` (count searches only),
`--limit N` (first N tracks), `--max-searches N` (search at most N uncached tracks, so a run
stays inside the daily quota).

Matches are cached in `data/beatport/youtube_matches.xlsx` (written after every run, also on a
quota error), so re-runs only pay for uncached tracks. At 100 units per search the free quota
covers ~100 searches/day; larger dumps resume the next day.

Workflow `resolve-beatport.yml` automates that: daily at 09:00 UTC (after the quota reset) and on
manual dispatch (input: dump path), it runs with `--max-searches 100` and commits the results.
Once every track is cached the run is a no-op. The dump path defaults to
`data/beatport/info_beatport_20261116.txt` - edit `INPUT` in the workflow for a new dump.
Requires the `YOUTUBE_API_KEY` repo secret.

## Sanitizing the Richie Hawtin tracklist (OpenAI Batch API)

`data/Richie_Hawtin_tracklists.xlsx` has a messy `title` column (e.g.
`"Tuned Hips (Matheo Velez Remix) [Medicine Musique - MED035]"`). It's split into clean
`sanitized_title` / `remixer` / `label` columns via an LLM, run through the
[OpenAI Batch API](https://platform.openai.com/docs/guides/batch) (50% cheaper than sync calls)
using [`kitai.batch`](https://github.com/laceto/kitai).

Batch jobs can take up to 24h, so this is split into two scripts / GitHub Actions workflows:

- **Submit** (`scripts/submit_sanitize_batch.py`, workflow `sanitize-submit.yml`, manual
  dispatch): builds one chat task per row and submits the batch job, saving the job id to
  `data/richie_hawtin_sanitize_job.json`.
- **Fetch** (`scripts/fetch_sanitize_batch.py`, workflow `sanitize-fetch.yml`, manual dispatch
  or scheduled every 2h): checks the job status; once complete, downloads and parses the
  results and writes `data/Richie_Hawtin_tracklists_sanitized.xlsx`. If the job isn't done yet,
  it exits cleanly and the next scheduled run retries.

Requires an `OPENAI_API_KEY` (set in `.env` locally, or as a repo secret named
`OPENAI_API_KEY` for the GitHub Actions workflows).

Note: `kitai` pulls in a fairly heavy dependency stack (langchain, langchain-community,
faiss-cpu) even though only `kitai.batch` is used here — that's inherent to installing it as
a single package from its git repo.
