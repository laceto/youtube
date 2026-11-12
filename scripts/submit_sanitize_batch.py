import json
from datetime import datetime, timezone

import pandas as pd
from kitai.batch import build_chat_tasks, submit_batch_job
from openai import OpenAI

from youtube_tools import SANITIZE_SYSTEM_PROMPT, build_sanitize_items
from youtube_tools.config import get_openai_api_key

INPUT_PATH = "data/Richie_Hawtin_tracklists.xlsx"
TITLE_COLUMN = "title"
CHAT_MODEL = "gpt-4o-mini"
JOB_FILE = "data/richie_hawtin_sanitize_job.json"


def main() -> None:
    df = pd.read_excel(INPUT_PATH)
    items = build_sanitize_items(df, column=TITLE_COLUMN)
    print(f"Built {len(items)} sanitize task(s) from {len(df)} row(s).")

    tasks = build_chat_tasks(items, system_prompt=SANITIZE_SYSTEM_PROMPT, model=CHAT_MODEL)

    client = OpenAI(api_key=get_openai_api_key())
    job_id = submit_batch_job(
        client,
        tasks,
        endpoint="/v1/chat/completions",
        metadata={"description": "richie_hawtin_title_sanitize"},
    )

    job_record = {
        "job_id": job_id,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "input_path": INPUT_PATH,
        "row_count": len(items),
    }
    with open(JOB_FILE, "w", encoding="utf-8") as f:
        json.dump(job_record, f, indent=2)

    print(f"Submitted batch job: {job_id}")
    print(f"Saved job record to {JOB_FILE}")


if __name__ == "__main__":
    main()
