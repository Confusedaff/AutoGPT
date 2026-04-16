"""
runner.py -- Persistent Daemon Scheduler + Git Auto-Commit
==========================================================
Start ONCE and leave running -- it loops forever, sleeping between days.

Key behaviours
--------------
* Picks a random commit count each day (1-20), biased so the count
  drifts up/down from the previous day's count (feels organic, not robotic).
* Spreads commits across a 6 PM - 11:30 PM window with random gaps.
* Hard monthly API budget: never exceeds MAX_CALLS_PER_MONTH Groq calls
  (tracked in .api_usage.json). Automatically skips days if budget is low.
* No restart needed -- just run `python runner.py` once and leave it.
* Pass --no-delay to fire the first batch immediately (for testing).
"""

import os
import sys
import time
import json
import random
import subprocess
from datetime import datetime, date, timedelta
from pathlib import Path

# -- Load .env --------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

from improver import improve


# ==============================================================================
#  CONFIG
# ==============================================================================

BRANCH         = os.getenv("GIT_BRANCH", "main")
REMOTE         = os.getenv("GIT_REMOTE", "origin")
IMPROVE_TARGET = os.getenv("IMPROVE_TARGET", "both")   # backend | frontend | both

# Commit count boundaries per day
MIN_COMMITS_PER_DAY = 1
MAX_COMMITS_PER_DAY = 20

# Window during which commits are spread (18:00 -> 23:30)
WINDOW_START_HOUR = 18        # 6 PM
WINDOW_END_HOUR   = 23        # commits must START before 11:30 PM
WINDOW_END_MINUTE = 30

# Groq API budget guard
# Groq free tier: 14 400 req/day -- we cap monthly to stay safe.
# Each improve("both") = 2 API calls. Each improve("backend"/"frontend") = 1.
# Default cap: 300 calls/month -> ~150 "both" runs -> ~5 per day safely.
# Feel free to raise this if you upgrade your Groq plan.
MAX_CALLS_PER_MONTH = int(os.getenv("MAX_GROQ_CALLS_MONTH", "300"))
CALLS_PER_COMMIT    = 2 if IMPROVE_TARGET == "both" else 1

USAGE_FILE = ".api_usage.json"


# ==============================================================================
#  API USAGE TRACKER
# ==============================================================================

def _load_usage() -> dict:
    try:
        if Path(USAGE_FILE).exists():
            return json.loads(Path(USAGE_FILE).read_text())
    except Exception:
        pass
    return {}


def _save_usage(data: dict):
    try:
        Path(USAGE_FILE).write_text(json.dumps(data, indent=2))
    except Exception as e:
        print(f"  [warn] Could not save API usage: {e}")


def calls_this_month() -> int:
    """Total Groq API calls logged this calendar month."""
    data  = _load_usage()
    month = date.today().strftime("%Y-%m")
    return data.get(month, 0)


def log_calls(n: int):
    """Increment this month's call counter by n."""
    data  = _load_usage()
    month = date.today().strftime("%Y-%m")
    data[month] = data.get(month, 0) + n
    _save_usage(data)


def remaining_budget() -> int:
    """How many more Groq calls we're allowed this month."""
    return max(0, MAX_CALLS_PER_MONTH - calls_this_month())


# ==============================================================================
#  DAILY COMMIT COUNT -- organic random walk
# ==============================================================================

_STATE_FILE = ".runner_state.json"


def _load_state() -> dict:
    try:
        if Path(_STATE_FILE).exists():
            return json.loads(Path(_STATE_FILE).read_text())
    except Exception:
        pass
    return {}


def _save_state(data: dict):
    try:
        Path(_STATE_FILE).write_text(json.dumps(data, indent=2))
    except Exception as e:
        print(f"  [warn] Could not save runner state: {e}")


def pick_commit_count(budget_remaining: int) -> int:
    """
    Pick today's commit count using a biased random walk from yesterday's count.
    The count drifts +/-30-50 % of the previous value, with a nudge toward the
    middle of the range so it doesn't pin at the extremes.

    Hard-capped by both MAX_COMMITS_PER_DAY and the remaining API budget.
    """
    state    = _load_state()
    prev     = state.get("last_commit_count", random.randint(1, 8))

    # Random walk: change by +/-1-3 commits, nudge toward midpoint (10)
    midpoint = (MIN_COMMITS_PER_DAY + MAX_COMMITS_PER_DAY) / 2
    nudge    = 1 if prev < midpoint else -1
    delta    = random.randint(-3, 3) + nudge
    raw      = prev + delta

    count = max(MIN_COMMITS_PER_DAY, min(MAX_COMMITS_PER_DAY, raw))

    # Never exceed what the API budget allows today
    budget_cap = budget_remaining // CALLS_PER_COMMIT
    count       = min(count, budget_cap)
    count       = max(0, count)   # could be 0 if budget exhausted

    return count


# ==============================================================================
#  GIT HELPERS
# ==============================================================================

def git(*args, check=True) -> subprocess.CompletedProcess:
    cmd = ["git"] + list(args)
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=check)


def has_changes() -> bool:
    return bool(git("status", "--porcelain").stdout.strip())


def commit_and_push(message: str):
    git("add", "--all")
    git("commit", "-m", message)
    result = git("push", REMOTE, BRANCH, check=False)
    if result.returncode != 0:
        print(f"  [!] Push failed -- attempting pull-rebase...")
        git("pull", "--rebase", REMOTE, BRANCH, check=False)
        git("push", REMOTE, BRANCH)


# ==============================================================================
#  SINGLE-COMMIT CYCLE
# ==============================================================================

def run_one_commit(commit_index: int, total: int) -> bool:
    """
    Run one improvement -> commit cycle.
    Returns True if a commit was made, False otherwise.
    """
    print(f"\n  -- Commit {commit_index}/{total} | {datetime.now():%H:%M:%S} --")

    # Pull latest before improving
    try:
        git("checkout", BRANCH, check=False)
        git("pull", "--rebase", REMOTE, BRANCH, check=False)
    except Exception as e:
        print(f"  [warn] Git pull failed: {e}")

    try:
        changelogs = improve(IMPROVE_TARGET)
        log_calls(CALLS_PER_COMMIT)
    except Exception as e:
        print(f"  [FATAL] Improver crashed: {e}")
        return False

    if not changelogs:
        print("  No improvements made -- skipping commit.")
        return False

    if not has_changes():
        print("  No file changes detected -- skipping commit.")
        return False

    today   = datetime.now().strftime("%Y-%m-%d")
    summary = "; ".join(changelogs)
    msg     = f"auto-improve {today} [{commit_index}/{total}]: {summary[:180]}"

    print(f"\n  Committing: {msg}")
    try:
        commit_and_push(msg)
        print("  * Pushed to GitHub!")
        return True
    except Exception as e:
        print(f"  [!] Git push failed: {e}")
        return False


# ==============================================================================
#  DAILY BATCH
# ==============================================================================

def run_daily_batch(no_delay: bool = False):
    """
    Execute today's batch of commits spread across the 6-11:30 PM window.
    """
    budget = remaining_budget()
    print(f"\n  API budget remaining this month: {budget} calls")

    commit_count = pick_commit_count(budget)

    if commit_count == 0:
        print("  (!) API budget exhausted for this month -- skipping today.")
        return

    print(f"  Today's commit target: {commit_count} commits")

    # Build sorted random timestamps within [18:00, 23:30]
    window_start = datetime.now().replace(
        hour=WINDOW_START_HOUR, minute=0, second=0, microsecond=0
    )
    window_end = datetime.now().replace(
        hour=WINDOW_END_HOUR, minute=WINDOW_END_MINUTE, second=0, microsecond=0
    )
    window_secs = int((window_end - window_start).total_seconds())

    # Pick commit_count random offsets within the window
    offsets = sorted(random.sample(range(0, window_secs), min(commit_count, window_secs)))
    fire_times = [window_start + timedelta(seconds=s) for s in offsets]

    print(f"  Scheduled fire times: {[t.strftime('%H:%M') for t in fire_times]}")

    if no_delay:
        # For testing: fire all commits back-to-back right now
        for i, _ in enumerate(fire_times, 1):
            run_one_commit(i, commit_count)
            if i < commit_count:
                print("  Waiting 90s between commits (Groq rate limit)...")
                time.sleep(90)   # Groq free tier: ~1 req/min sustained; extra buffer avoids cascading 429s
        _save_state({"last_commit_count": commit_count, "last_run_date": str(date.today())})
        return

    commits_made = 0
    for i, fire_at in enumerate(fire_times, 1):
        now = datetime.now()
        if fire_at > now:
            wait = (fire_at - now).total_seconds()
            h, remainder = divmod(int(wait), 3600)
            m = remainder // 60
            print(f"\n  Waiting {h}h {m}m until {fire_at:%H:%M} for commit {i}/{commit_count}...")
            time.sleep(wait)

        success = run_one_commit(i, commit_count)
        if success:
            commits_made += 1

    print(f"\n  * Day complete -- {commits_made}/{commit_count} commits pushed.")
    _save_state({"last_commit_count": commit_count, "last_run_date": str(date.today())})


# ==============================================================================
#  MAIN LOOP -- runs forever, wakes at 6 PM each day
# ==============================================================================

def seconds_until_next_window() -> float:
    """Seconds until 6 PM today (or tomorrow if already past 11:30 PM)."""
    now   = datetime.now()
    today_start = now.replace(hour=WINDOW_START_HOUR, minute=0, second=0, microsecond=0)
    today_end   = now.replace(hour=WINDOW_END_HOUR,   minute=WINDOW_END_MINUTE, second=0, microsecond=0)

    if now < today_start:
        return (today_start - now).total_seconds()
    elif now <= today_end:
        return 0   # we're inside the window right now
    else:
        # Past the window -- sleep until 6 PM tomorrow
        tomorrow_start = today_start + timedelta(days=1)
        return (tomorrow_start - now).total_seconds()


def main():
    no_delay = "--no-delay" in sys.argv or os.getenv("SKIP_DELAY", "").lower() == "true"

    print("\n" + "=" * 58)
    print("  LEDGER Auto-Improver DAEMON -- started")
    print(f"  {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"  Target: {IMPROVE_TARGET}  |  Max commits/day: {MAX_COMMITS_PER_DAY}")
    print(f"  Monthly API cap: {MAX_CALLS_PER_MONTH} calls")
    print("  Press Ctrl+C to stop.")
    print("=" * 58)

    if no_delay:
        print("\n  --no-delay: firing first batch immediately...")
        run_daily_batch(no_delay=True)
        print("\n  Test run complete. Exiting.")
        return

    # -- Infinite daily loop ------------------------------------------------
    last_run_date = _load_state().get("last_run_date")

    while True:
        today_str = str(date.today())

        # Already ran today? Sleep until tomorrow's window.
        if last_run_date == today_str:
            wait = seconds_until_next_window()
            if wait == 0:
                # Edge case: still inside window but already ran -- sleep to tomorrow
                wait = seconds_until_next_window() + 60  # force past window end
                tomorrow = datetime.now() + timedelta(seconds=wait)
                h, rem = divmod(int(wait), 3600)
                m = rem // 60
                print(f"\n  Already ran today. Sleeping {h}h {m}m until {tomorrow:%Y-%m-%d %H:%M}...")
                time.sleep(wait)
                last_run_date = None
                continue

        wait = seconds_until_next_window()
        if wait > 0:
            wake_at = datetime.now() + timedelta(seconds=wait)
            h, rem  = divmod(int(wait), 3600)
            m        = rem // 60
            print(f"\n  Sleeping {h}h {m}m until window opens at {wake_at:%Y-%m-%d %H:%M}...")
            time.sleep(wait)

        # Run today's batch
        print(f"\n{'='*58}")
        print(f"  Starting daily batch -- {datetime.now():%Y-%m-%d %H:%M:%S}")
        print(f"{'='*58}")
        run_daily_batch(no_delay=False)
        last_run_date = today_str

        # Sleep a short buffer before looping, so we don't accidentally double-fire
        time.sleep(60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Daemon stopped by user. Goodbye.\n")