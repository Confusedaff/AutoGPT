"""
improver.py — AI Self-Improvement Engine
Uses Groq's FREE API (llama-3.3-70b-versatile) to read and improve
both main.py (backend) and frontend/index.html, then logs changes.
"""

import os
import re
import json
import time
import shutil
import py_compile
import subprocess
import tempfile
import urllib.request
import urllib.error
from datetime import date, datetime
from pathlib import Path

GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
GROQ_URL      = "https://api.groq.com/openai/v1/chat/completions"
MODEL         = "llama-3.3-70b-versatile"   # Free on Groq
BACKEND_FILE  = "main.py"
FRONTEND_FILE = os.path.join("frontend", "index.html")
LOG_FILE      = "improvement_log.md"
BACKUP_DIR    = ".backups"


# ──────────────────────────────────────────────
#  Groq API Call
# ──────────────────────────────────────────────

def groq_chat(messages: list, max_tokens: int = 8192) -> str:
    """Call Groq's free API. Returns the assistant message text."""
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set in environment / .env file.")

    payload = json.dumps({
        "model":      MODEL,
        "messages":   messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }).encode()

    req = urllib.request.Request(
        GROQ_URL,
        data    = payload,
        headers = {
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}",
        },
        method = "POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode())
            return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"Groq API error {e.code}: {body}")


# ──────────────────────────────────────────────
#  Backup
# ──────────────────────────────────────────────

def backup(filepath: str):
    """Save a timestamped backup before overwriting."""
    Path(BACKUP_DIR).mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name  = Path(filepath).name
    dest  = os.path.join(BACKUP_DIR, f"{stamp}_{name}")
    shutil.copy2(filepath, dest)
    print(f"  [backup] → {dest}")


# ──────────────────────────────────────────────
#  Syntax Validation
# ──────────────────────────────────────────────

def validate_python(code: str) -> tuple[bool, str]:
    """Check Python syntax without saving."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write(code)
        tmp = f.name
    try:
        py_compile.compile(tmp, doraise=True)
        return True, ""
    except py_compile.PyCompileError as e:
        return False, str(e)
    finally:
        os.unlink(tmp)


def validate_html(code: str) -> tuple[bool, str]:
    """Basic HTML sanity checks."""
    checks = ["<!DOCTYPE html>", "<html", "</html>", "<body", "</body>"]
    for c in checks:
        if c.lower() not in code.lower():
            return False, f"Missing expected tag: {c}"
    return True, ""


# ──────────────────────────────────────────────
#  Strip markdown fences from LLM response
# ──────────────────────────────────────────────

def strip_fences(text: str, lang: str = "") -> str:
    """Remove ```lang ... ``` fences that the LLM may wrap code in."""
    pattern = rf"```{lang}\s*(.*?)```"
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # fallback: strip any triple-backtick fences
    text = re.sub(r"^```[a-z]*\n?", "", text.strip())
    text = re.sub(r"\n?```$", "", text.strip())
    return text.strip()


# ──────────────────────────────────────────────
#  Improve Backend
# ──────────────────────────────────────────────

def improve_backend(log_history: str) -> dict:
    """Ask the LLM to improve main.py. Returns {code, changelog}."""
    with open(BACKEND_FILE, "r") as f:
        current = f.read()

    system = """You are an expert Python / Flask developer performing automated self-improvement.
You receive the current backend code and improvement history, then return ONLY a JSON object — no prose, no markdown.
The JSON must have exactly two keys:
  "improved_code": the complete updated Python file as a string
  "changelog": one sentence describing the single improvement made

Rules:
- Make ONE meaningful improvement per run (new endpoint, better error handling, new analytics feature, caching, etc.)
- Do NOT break existing API contracts
- Keep Flask + SQLite (no external DB)
- The code must be valid Python 3.10+
- Do NOT add dummy data or test fixtures
- Return ONLY the raw JSON — no backticks, no extra text"""

    user = f"""Current backend code:
{current}

Improvement history (do not repeat these):
{log_history}

Return JSON only."""

    raw = groq_chat([
        {"role": "system", "content": system},
        {"role": "user",   "content": user}
    ], max_tokens=8192)

    # Strip any accidental markdown fences
    raw = strip_fences(raw, "json")

    result = json.loads(raw)
    return result


# ──────────────────────────────────────────────
#  Improve Frontend
# ──────────────────────────────────────────────

def improve_frontend(log_history: str) -> dict:
    """Ask the LLM to improve frontend/index.html. Returns {code, changelog}."""
    with open(FRONTEND_FILE, "r") as f:
        current = f.read()

    system = """You are an expert frontend developer performing automated self-improvement on a dark luxury finance tracker web app.
You receive the current HTML/CSS/JS single-file frontend and improvement history, then return ONLY a JSON object.
The JSON must have exactly two keys:
  "improved_code": the complete updated HTML file as a string
  "changelog": one sentence describing the single improvement made

Rules:
- Make ONE meaningful visual or UX improvement (new chart type, animation, feature, filter, dark mode toggle, etc.)
- Keep the dark luxury aesthetic with gold accents and DM Mono / Cormorant Garamond fonts
- Keep Chart.js from cdnjs — no other CDN changes
- API base URL stays as empty string '' (same-origin)
- The file must be valid HTML5 with embedded CSS + JS
- Do NOT remove existing features
- Return ONLY the raw JSON — no backticks, no extra text"""

    user = f"""Current frontend code (may be truncated for context):
{current[:18000]}

Improvement history (do not repeat these):
{log_history}

Return JSON only."""

    raw = groq_chat([
        {"role": "system", "content": system},
        {"role": "user",   "content": user}
    ], max_tokens=8192)

    raw = strip_fences(raw, "json")
    result = json.loads(raw)
    return result


# ──────────────────────────────────────────────
#  Log
# ──────────────────────────────────────────────

def read_log() -> str:
    if not os.path.exists(LOG_FILE):
        return "(No previous improvements)"
    with open(LOG_FILE, "r") as f:
        return f.read()


def append_log(target: str, changelog: str):
    today = date.today().isoformat()
    now   = datetime.now().strftime("%H:%M")
    with open(LOG_FILE, "a") as f:
        f.write(f"\n### {today} {now} — {target.upper()}\n{changelog}\n")
    print(f"  [log] Appended changelog for {target}")


# ──────────────────────────────────────────────
#  Main improve() function
# ──────────────────────────────────────────────

def improve(target: str = "both") -> list[str]:
    """
    Run improvement cycle.
    target: 'backend' | 'frontend' | 'both'
    Returns list of changelog strings.
    """
    changelogs = []
    log_history = read_log()

    # ── Backend ──
    if target in ("backend", "both"):
        print("\n[improver] Improving backend (main.py)…")
        try:
            result   = improve_backend(log_history)
            new_code = result["improved_code"]
            note     = result["changelog"]

            valid, err = validate_python(new_code)
            if not valid:
                print(f"  [!] Python syntax error — skipping: {err}")
            else:
                backup(BACKEND_FILE)
                with open(BACKEND_FILE, "w") as f:
                    f.write(new_code)
                append_log("backend", note)
                changelogs.append(f"[backend] {note}")
                print(f"  ✓ Backend improved: {note}")
        except Exception as e:
            print(f"  [!] Backend improvement failed: {e}")

        time.sleep(3)   # rate-limit courtesy

    # ── Frontend ──
    if target in ("frontend", "both"):
        print("\n[improver] Improving frontend (index.html)…")
        try:
            result   = improve_frontend(log_history)
            new_code = result["improved_code"]
            note     = result["changelog"]

            valid, err = validate_html(new_code)
            if not valid:
                print(f"  [!] HTML validation error — skipping: {err}")
            else:
                backup(FRONTEND_FILE)
                with open(FRONTEND_FILE, "w") as f:
                    f.write(new_code)
                append_log("frontend", note)
                changelogs.append(f"[frontend] {note}")
                print(f"  ✓ Frontend improved: {note}")
        except Exception as e:
            print(f"  [!] Frontend improvement failed: {e}")

    return changelogs


if __name__ == "__main__":
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "both"
    results = improve(t)
    print("\nChangelogs:", results)
