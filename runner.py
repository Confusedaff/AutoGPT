"""
runner.py — Scheduler + Git Auto-Commit
Triggered daily by Task Scheduler / cron at 6 PM.
Sleeps a random offset (0–5 h) so commits land between 18:00–23:00.
Runs the improver, then commits + pushes all changes to GitHub.
"""

import os
import sys
import time
import random
import subprocess
from datetime import datetime
from pathlib import Path

# Load .env if python-dotenv is installed, otherwise read manually
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


# ──────────────────────────────────────────────
#  Config
# ──────────────────────────────────────────────

RANDOM_DELAY_MAX = 5 * 3600   # up to 5 hours after 6 PM = max 11 PM
BRANCH           = os.getenv("GIT_BRANCH", "main")
REMOTE           = os.getenv("GIT_REMOTE", "origin")
IMPROVE_TARGET   = os.getenv("IMPROVE_TARGET", "both")  # backend | frontend | both


# ──────────────────────────────────────────────
#  Git helpers
# ──────────────────────────────────────────────

def git(*args, check=True) -> subprocess.CompletedProcess:
    cmd = ["git"] + list(args)
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def has_changes() -> bool:
    result = git("status", "--porcelain")
    return bool(result.stdout.strip())


def commit_and_push(message: str):
    git("add", "--all")
    git("commit", "-m", message)
    result = git("push", REMOTE, BRANCH, check=False)
    if result.returncode != 0:
        print(f"  [!] Push failed:\n{result.stderr}")
        print("  Attempting pull-rebase and retry…")
        git("pull", "--rebase", REMOTE, BRANCH, check=False)
        git("push", REMOTE, BRANCH)


# ──────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────

def main():
    print(f"\n{'='*58}")
    print(f"  LEDGER Auto-Improver — {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"{'='*58}")

    # ── Random delay so commit lands anywhere 6 PM – 11 PM ──
    skip_delay = "--no-delay" in sys.argv or os.getenv("SKIP_DELAY", "").lower() == "true"
    if not skip_delay:
        delay = random.randint(0, RANDOM_DELAY_MAX)
        h, m  = divmod(delay // 60, 60)
        print(f"\n  Sleeping {h}h {m}m before running…")
        time.sleep(delay)

    print(f"\n  Start time: {datetime.now():%H:%M:%S}")

    # ── Ensure we're on the right branch ──
    try:
        git("checkout", BRANCH, check=False)
        git("pull", "--rebase", REMOTE, BRANCH, check=False)
    except Exception as e:
        print(f"  [warn] Git pull failed: {e}")

    # ── Run the improver ──
    print(f"\n  Running improver (target={IMPROVE_TARGET})…")
    try:
        changelogs = improve(IMPROVE_TARGET)
    except Exception as e:
        print(f"\n  [FATAL] Improver crashed: {e}")
        changelogs = []

    # ── Commit ──
    if not changelogs:
        print("\n  No improvements made — nothing to commit.")
        return

    if not has_changes():
        print("\n  No file changes detected — skipping commit.")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    summary = "; ".join(changelogs)
    commit_msg = f"auto-improve {today}: {summary[:200]}"

    print(f"\n  Committing: {commit_msg}")
    try:
        commit_and_push(commit_msg)
        print("\n  ✦ Successfully pushed to GitHub!")
    except Exception as e:
        print(f"\n  [!] Git commit/push failed: {e}")

    print(f"\n  Done at {datetime.now():%H:%M:%S}\n")


if __name__ == "__main__":
    main()
