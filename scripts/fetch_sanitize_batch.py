import json
import sys

import pandas as pd
from kitai.batch import check_batch_job, download_batch_results, parse_chat_results
from openai import OpenAI

from youtube_tools import extract_sanitized_fields, merge_sanitized_results
from youtube_tools.config import get_openai_api_key

JOB_FILE = "data/richie_hawtin_sanitize_job.json"
OUTPUT_PATH = "data/Richie_Hawtin_tracklists_sanitized.xlsx"

_FAILED_STATUSES = {"failed", "expired", "cancelled"}


def main() -> int:
    with open(JOB_FILE, "r", encoding="utf-8") as f:
        job_record = json.load(f)

    job_id = job_record["job_id"]
    input_path = job_record["input_path"]

    client = OpenAI(api_key=get_openai_api_key())
    status = check_batch_job(client, job_id)
    print(f"Batch {job_id}: status={status['status']} counts={status['counts']}")

    if status["status"] in _FAILED_STATUSES:
        print(f"Batch job ended unsuccessfully: {status['status']}")
        return 1

    if not status["is_complete"]:
        print("Batch job is not complete yet. Nothing to do.")
        return 0

    results = download_batch_results(client, job_id)
    pairs = parse_chat_results(results, extractor_fn=extract_sanitized_fields)
    print(f"Parsed {len(pairs)}/{len(results)} sanitized row(s).")

    df = pd.read_excel(input_path)
    merged = merge_sanitized_results(df, pairs)
    merged.to_excel(OUTPUT_PATH, index=False)
    print(f"Saved sanitized tracklist to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
