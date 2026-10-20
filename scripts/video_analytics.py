"""Build an analytics report for one of your uploaded videos and save it to .xlsx.

Usage:
    python scripts/video_analytics.py --list                 # show your recent uploads
    python scripts/video_analytics.py [video-url-or-id]      # default: latest upload
"""
import sys

from youtube_tools.analytics import build_video_report, list_my_uploads, write_report_xlsx

if __name__ == "__main__":
    args = sys.argv[1:]
    uploads = list_my_uploads()
    if args and args[0] == "--list":
        for u in uploads:
            print(f"{u['video_id']}  {u['published_at'][:10]}  {u['title']}")
        sys.exit(0)
    if not args and not uploads:
        sys.exit("No uploads found on this channel.")
    video = args[0] if args else uploads[0]["video_id"]
    report = build_video_report(video)
    out = f"data/analytics_{report['summary'].loc[0, 'video_id']}.xlsx"
    write_report_xlsx(report, out)
    print(report["summary"].T.to_string(header=False))
    print("\n", report["totals"].T.to_string(header=False))
    print(f"\n-> {out}")
