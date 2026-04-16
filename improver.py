"""
improver.py -- AI Self-Improvement Engine
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
from datetime import date, datetime
from pathlib import Path

GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
GROQ_URL      = "https://api.groq.com/openai/v1/chat/completions"
MODEL         = "llama-3.3-70b-versatile"   # Free on Groq
BACKEND_FILE  = "main.py"
FRONTEND_FILE = os.path.join("frontend", "index.html")
LOG_FILE      = "improvement_log.md"
BACKUP_DIR    = ".backups"


# ----------------------------------------------
#  Groq API Call  (uses requests -- avoids Cloudflare 403/1010)
# ----------------------------------------------

def groq_chat(messages: list, max_tokens: int = 8192) -> str:
    """Call Groq's free API with automatic retry/backoff. Returns the assistant message text."""
    import requests

    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set in environment / .env file.")

    max_retries = 4
    for attempt in range(max_retries):
        try:
            response = requests.post(
                GROQ_URL,
                headers={
                    "Content-Type":  "application/json",
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                },
                json={
                    "model":       MODEL,
                    "messages":    messages,
                    "max_tokens":  max_tokens,
                    "temperature": 0.7,
                },
                timeout=120,
            )
            if response.status_code == 429:
                wait = 30 * (2 ** attempt)   # 30s, 60s, 120s, 240s
                print(f"  [groq] 429 rate-limited -- retrying in {wait}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = 15 * (2 ** attempt)
            print(f"  [groq] Error: {e} -- retrying in {wait}s")
            time.sleep(wait)
    raise RuntimeError("Groq API failed after all retries")


# ----------------------------------------------
#  Backup
# ----------------------------------------------

def backup(filepath: str):
    """Save a timestamped backup before overwriting."""
    Path(BACKUP_DIR).mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name  = Path(filepath).name
    dest  = os.path.join(BACKUP_DIR, f"{stamp}_{name}")
    shutil.copy2(filepath, dest)
    print(f"  [backup] -> {dest}")


# ----------------------------------------------
#  Syntax Validation
# ----------------------------------------------

def validate_python(code: str) -> tuple[bool, str]:
    """Check Python syntax without saving."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as f:
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


# ----------------------------------------------
#  Strip markdown fences from LLM response
# ----------------------------------------------

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


def robust_json_parse(raw: str) -> dict:
    """
    Parse JSON from an LLM response robustly.

    LLMs sometimes embed literal control characters (newlines, tabs) inside
    JSON string values instead of escaping them as \\n / \\t, which makes
    json.loads raise 'Invalid control character'.  We fix this by scanning
    the raw text character-by-character and escaping any bare control chars
    that appear inside string literals.
    """
    # First attempt: fast path -- works if the model behaved
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Second attempt: sanitize bare control characters inside strings
    sanitized = []
    in_string  = False
    escape_next = False
    CTRL_ESCAPE = {
        '\n': '\\n', '\r': '\\r', '\t': '\\t',
        '\b': '\\b', '\f': '\\f',
    }
    for ch in raw:
        if escape_next:
            sanitized.append(ch)
            escape_next = False
        elif ch == '\\' and in_string:
            sanitized.append(ch)
            escape_next = True
        elif ch == '"':
            in_string = not in_string
            sanitized.append(ch)
        elif in_string and ch in CTRL_ESCAPE:
            sanitized.append(CTRL_ESCAPE[ch])
        else:
            sanitized.append(ch)

    try:
        return json.loads("".join(sanitized))
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse LLM JSON response: {e}\nRaw (first 500): {raw[:500]}")


# ----------------------------------------------
#  Improve Backend
# ----------------------------------------------

def improve_backend(log_history: str) -> dict:
    """Ask the LLM to improve main.py. Returns {improved_code, changelog}."""
    with open(BACKEND_FILE, "r", encoding="utf-8") as f:
        current = f.read()

    # Truncate both code and log to avoid 413 Payload Too Large
    # Snap at a line boundary so we never hand the LLM a broken mid-string file
    lines, length = [], 0
    for line in current.splitlines():
        if length + len(line) + 1 > 10000:
            break
        lines.append(line)
        length += len(line) + 1
    current      = "\n".join(lines)
    log_history  = log_history[-3000:]   # keep only the most recent history

    system = """You are an expert Python / Flask developer performing automated self-improvement.
You receive the current backend code and improvement history, then return ONLY a JSON object -- no prose, no markdown.
The JSON must have exactly two keys:
  "improved_code": the complete updated Python file as a string
  "changelog": one sentence describing the single improvement made

Rules:
- Make ONE meaningful improvement per run (new endpoint, better error handling, new analytics feature, caching, etc.)
- Do NOT break existing API contracts
- Keep Flask + SQLite (no external DB)
- The code must be valid Python 3.10+
- Do NOT add dummy data or test fixtures
- Return ONLY the raw JSON -- no backticks, no extra text"""

    user = f"""Current backend code:
{current}

Improvement history (do not repeat these):
{log_history}

Return JSON only."""

    raw = groq_chat([
        {"role": "system", "content": system},
        {"role": "user",   "content": user}
    ], max_tokens=8192)

    raw = strip_fences(raw, "json")
    return robust_json_parse(raw)


# ----------------------------------------------
#  Improve Frontend
# ----------------------------------------------

def improve_frontend(log_history: str) -> dict:
    """Ask the LLM to improve frontend/index.html. Returns {improved_code, changelog}."""
    with open(FRONTEND_FILE, "r", encoding="utf-8") as f:
        current = f.read()

    # Truncate both to avoid 413 Payload Too Large
    # Snap at a line boundary so we never hand the LLM a broken mid-string file
    lines, length = [], 0
    for line in current.splitlines():
        if length + len(line) + 1 > 8000:
            break
        lines.append(line)
        length += len(line) + 1
    current     = "\n".join(lines)
    log_history = log_history[-3000:]

    system = """You are an expert frontend developer performing automated self-improvement on a dark luxury finance tracker web app.
You receive the current HTML/CSS/JS single-file frontend and improvement history, then return ONLY a JSON object.
The JSON must have exactly two keys:
  "improved_code": the complete updated HTML file as a string
  "changelog": one sentence describing the single improvement made

Rules:
- Make ONE meaningful visual or UX improvement (new chart type, animation, feature, filter, dark mode toggle, etc.)
- Keep the dark luxury aesthetic with gold accents and DM Mono / Cormorant Garamond fonts
- Keep Chart.js from cdnjs -- no other CDN changes
- API base URL stays as empty string '' (same-origin)
- The file must be valid HTML5 with embedded CSS + JS
- Do NOT remove existing features
- Return ONLY the raw JSON -- no backticks, no extra text"""

    user = f"""Current frontend code (may be truncated for context):
{current}

Improvement history (do not repeat these):
{log_history}

Return JSON only."""

    raw = groq_chat([
        {"role": "system", "content": system},
        {"role": "user",   "content": user}
    ], max_tokens=8192)

    raw = strip_fences(raw, "json")
    return robust_json_parse(raw)


# ----------------------------------------------
#  Log  (all file I/O uses utf-8)
# ----------------------------------------------

def read_log() -> str:
    if not os.path.exists(LOG_FILE):
        return "(No previous improvements)"
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return f.read()


def append_log(target: str, changelog: str):
    today = date.today().isoformat()
    now   = datetime.now().strftime("%H:%M")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n### {today} {now} -- {target.upper()}\n{changelog}\n")
    print(f"  [log] Appended changelog for {target}")


# ----------------------------------------------
#  Main improve() function
# ----------------------------------------------

def improve(target: str = "both") -> list[str]:
    """
    Run improvement cycle.
    target: 'backend' | 'frontend' | 'both'
    Returns list of changelog strings.
    """
    changelogs  = []
    log_history = read_log()

    # -- Backend --
    if target in ("backend", "both"):
        print("\n[improver] Improving backend (main.py)...")
        try:
            result   = improve_backend(log_history)
            new_code = result["improved_code"]
            note     = result["changelog"]

            valid, err = validate_python(new_code)
            if not valid:
                print(f"  [!] Python syntax error -- skipping: {err}")
            else:
                backup(BACKEND_FILE)
                with open(BACKEND_FILE, "w", encoding="utf-8") as f:
                    f.write(new_code)
                append_log("backend", note)
                changelogs.append(f"[backend] {note}")
                print(f"  OK Backend improved: {note}")
        except Exception as e:
            print(f"  [!] Backend improvement failed: {e}")

        time.sleep(3)   # rate-limit courtesy

    # -- Frontend --
    if target in ("frontend", "both"):
        print("\n[improver] Improving frontend (index.html)...")
        try:
            result   = improve_frontend(log_history)
            new_code = result["improved_code"]
            note     = result["changelog"]

            valid, err = validate_html(new_code)
            if not valid:
                print(f"  [!] HTML validation error -- skipping: {err}")
            else:
                backup(FRONTEND_FILE)
                with open(FRONTEND_FILE, "w", encoding="utf-8") as f:
                    f.write(new_code)
                append_log("frontend", note)
                changelogs.append(f"[frontend] {note}")
                print(f"  OK Frontend improved: {note}")
        except Exception as e:
            print(f"  [!] Frontend improvement failed: {e}")

    return changelogs


if __name__ == "__main__":
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "both"
    results = improve(t)
    print("\nChangelogs:", results)