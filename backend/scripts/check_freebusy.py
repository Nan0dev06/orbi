"""PHASE 1 PROOF: live freebusy across all connected accounts + intersection.

    python backend/scripts/check_freebusy.py [--days 7] [--duration 60]
                                             [--tz Asia/Beirut]
                                             [--earliest 9] [--latest 22]

For every token in backend/.tokens/ this fetches LIVE busy blocks (freebusy
only — no titles ever), then prints the common free slots. "Now" is captured
once at the top so the whole run reasons from a single instant.
"""
import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # -> backend/

from app.auth.google import list_connected_accounts, load_credentials
from app.tools.freebusy import query_busy
from app.tools.slots import find_common_slots


def fmt(dt: datetime, tz: ZoneInfo) -> str:
    return dt.astimezone(tz).strftime("%a %d %b %H:%M")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--days", type=int, default=7, help="look-ahead window in days")
    p.add_argument("--duration", type=int, default=60, help="required slot length, minutes")
    p.add_argument("--tz", default="Asia/Beirut", help="timezone for display + hours filter")
    p.add_argument("--earliest", type=int, default=9, help="earliest local hour")
    p.add_argument("--latest", type=int, default=22, help="latest local hour")
    args = p.parse_args()

    tz = ZoneInfo(args.tz)
    token_files = list_connected_accounts()
    if not token_files:
        sys.exit(
            "No connected accounts. Run:  python backend/scripts/connect_account.py\n"
            "(once per test account)"
        )

    # single "now" for the whole run — everything downstream is relative to it
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=args.days)
    print(f"Now (UTC):     {now.isoformat(timespec='seconds')}")
    print(f"Now ({args.tz}): {now.astimezone(tz).strftime('%a %d %b %H:%M')}")
    print(f"Window:        next {args.days} days | need {args.duration} min "
          f"| {args.earliest:02d}:00-{args.latest:02d}:00 {args.tz}\n")

    busy_by_member: dict[str, list] = {}
    for path in token_files:
        email = path.stem
        print(f"[freebusy] querying {email} ...", flush=True)
        creds = load_credentials(path)  # transparently refreshes if expired
        busy = query_busy(creds, now, window_end)
        busy_by_member[email] = busy
        for s, e in busy:
            print(f"           busy {fmt(s, tz)} -> {fmt(e, tz)}")
        if not busy:
            print("           (no busy blocks in window)")

    print(f"\n[intersect] {len(busy_by_member)} members")
    slots = find_common_slots(
        busy_by_member, now, window_end,
        duration_minutes=args.duration, tz_name=args.tz,
        earliest_hour=args.earliest, latest_hour=args.latest,
    )

    if not slots:
        print(f"\nNo common {args.duration}-minute slot in the next {args.days} days "
              f"within {args.earliest:02d}:00-{args.latest:02d}:00 {args.tz}.")
        return

    print(f"\nCommon free slots (shown in {args.tz}):")
    for s, e in slots:
        mins = int((e - s).total_seconds() // 60)
        print(f"  {fmt(s, tz)} -> {fmt(e, tz)}  ({mins} min)")


if __name__ == "__main__":
    main()
