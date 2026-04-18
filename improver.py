"""
improver.py -- AI Self-Improvement Engine
Primary:  Local Ollama (gemma4:e2b or any model you have pulled)
Fallback: Groq API (llama-3.3-70b-versatile) if Ollama is unavailable

Set LLM_PROVIDER=groq in .env to force Groq.
Set OLLAMA_MODEL=gemma4:e2b (or llama3.2:latest, etc.) to choose model.
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

# ── Provider config ──────────────────────────────────────────────────────────
LLM_PROVIDER   = os.getenv("LLM_PROVIDER", "ollama").lower()   # "ollama" | "groq"
OLLAMA_URL     = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "gemma4:e2b")        # change to llama3.2:latest etc.
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
GROQ_URL       = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL     = "llama-3.3-70b-versatile"

BACKEND_FILE   = "main.py"
FRONTEND_FILE  = os.path.join("frontend", "index.html")
LOG_FILE       = "improvement_log.md"
BACKUP_DIR     = ".backups"


# ─────────────────────────────────────────────────────────────────────────────
#  LLM Calls
# ─────────────────────────────────────────────────────────────────────────────

def ollama_chat(messages: list, max_tokens: int = 8192) -> str:
    """
    Call a local Ollama model. No rate limits, no API key.
    Ollama must be running: `ollama serve`
    Model must be pulled:   `ollama pull gemma4:e2b`
    """
    import requests

    payload = {
        "model":    OLLAMA_MODEL,
        "messages": messages,
        "stream":   False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.7,
        },
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
        resp.raise_for_status()
        data = resp.json()
        # Ollama /api/chat response: {"message": {"role": "assistant", "content": "..."}}
        return data["message"]["content"].strip()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Ollama is not running or not reachable at {OLLAMA_URL}.\n"
            "Start it with: ollama serve\n"
            f"Pull the model with: ollama pull {OLLAMA_MODEL}"
        )


def groq_chat(messages: list, max_tokens: int = 8192) -> str:
    """Call Groq's free API with automatic retry/backoff."""
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
                    "model":       GROQ_MODEL,
                    "messages":    messages,
                    "max_tokens":  max_tokens,
                    "temperature": 0.7,
                },
                timeout=120,
            )
            if response.status_code == 429:
                wait = 30 * (2 ** attempt)
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


def llm_chat(messages: list, max_tokens: int = 8192) -> str:
    """
    Route to the right provider.
    If Ollama is the primary but fails, automatically falls back to Groq.
    """
    if LLM_PROVIDER == "groq":
        print(f"  [llm] Using Groq ({GROQ_MODEL})")
        return groq_chat(messages, max_tokens)

    # Default: Ollama
    print(f"  [llm] Using Ollama ({OLLAMA_MODEL})")
    try:
        return ollama_chat(messages, max_tokens)
    except RuntimeError as e:
        if GROQ_API_KEY:
            print(f"  [llm] Ollama failed: {e}")
            print(f"  [llm] Falling back to Groq ({GROQ_MODEL})...")
            return groq_chat(messages, max_tokens)
        raise


# ─────────────────────────────────────────────────────────────────────────────
#  Backup
# ─────────────────────────────────────────────────────────────────────────────

def backup(filepath: str):
    """Save a timestamped backup before overwriting."""
    Path(BACKUP_DIR).mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name  = Path(filepath).name
    dest  = os.path.join(BACKUP_DIR, f"{stamp}_{name}")
    shutil.copy2(filepath, dest)
    print(f"  [backup] -> {dest}")


# ─────────────────────────────────────────────────────────────────────────────
#  Syntax Validation
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
#  Response Parsing Helpers
# ─────────────────────────────────────────────────────────────────────────────

def strip_fences(text: str, lang: str = "") -> str:
    """Remove ```lang ... ``` fences that the LLM may wrap code in."""
    pattern = rf"```{lang}\s*(.*?)```"
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    text = re.sub(r"^```[a-z]*\n?", "", text.strip())
    text = re.sub(r"\n?```$", "", text.strip())
    return text.strip()


def extract_json_object(text: str) -> str:
    """
    Find the first {...} JSON object in the text.
    Useful when a model emits a preamble before the JSON.
    """
    start = text.find("{")
    if start == -1:
        return text
    depth, in_str, escape = 0, False, False
    for i, ch in enumerate(text[start:], start):
        if escape:
            escape = False
            continue
        if ch == "\\" and in_str:
            escape = True
            continue
        if ch == '"':
            in_str = not in_str
        elif not in_str:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
    return text[start:]   # unterminated -- return what we have and let the parser complain


def robust_json_parse(raw: str) -> dict:
    """
    Parse JSON from an LLM response robustly.
    Handles: preamble text, markdown fences, bare control characters in strings.
    """
    # Step 1: fast path
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Step 2: extract the JSON object if the model added preamble/postamble
    candidate = extract_json_object(raw)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Step 3: sanitize bare control characters inside JSON strings
    sanitized = []
    in_string  = False
    escape_next = False
    CTRL_ESCAPE = {"\n": "\\n", "\r": "\\r", "\t": "\\t", "\b": "\\b", "\f": "\\f"}
    for ch in candidate:
        if escape_next:
            sanitized.append(ch)
            escape_next = False
        elif ch == "\\" and in_string:
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
        raise ValueError(
            f"Could not parse LLM JSON response: {e}\n"
            f"Raw (first 500 chars): {raw[:500]}"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Improve Backend
# ─────────────────────────────────────────────────────────────────────────────

def improve_backend(log_history: str) -> dict:
    """Ask the LLM to improve main.py. Returns {improved_code, changelog}."""
    with open(BACKEND_FILE, "r", encoding="utf-8") as f:
        current = f.read()

    # Truncate to avoid context-window overflows (important for smaller local models)
    lines, length = [], 0
    for line in current.splitlines():
        if length + len(line) + 1 > 10_000:
            break
        lines.append(line)
        length += len(line) + 1
    current     = "\n".join(lines)
    log_history = log_history[-3000:]

    system = (
        "You are an expert Python / Flask developer performing automated self-improvement.\n"
        "You receive the current backend code and improvement history, then return ONLY a JSON object -- no prose, no markdown.\n"
        'The JSON must have exactly two keys:\n'
        '  "improved_code": the complete updated Python file as a string\n'
        '  "changelog": one sentence describing the single improvement made\n\n'
        "Rules:\n"
        "- Make ONE meaningful improvement per run (new endpoint, better error handling, new analytics feature, caching, etc.)\n"
        "- Do NOT break existing API contracts\n"
        "- Keep Flask + SQLite (no external DB)\n"
        "- The code must be valid Python 3.10+\n"
        "- Do NOT add dummy data or test fixtures\n"
        "- Return ONLY the raw JSON -- no backticks, no extra text"
    )

    user = (
        f"Current backend code:\n{current}\n\n"
        f"Improvement history (do not repeat these):\n{log_history}\n\n"
        "Return JSON only."
    )

    raw = llm_chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=8192,
    )
    raw = strip_fences(raw, "json")
    return robust_json_parse(raw)


# ─────────────────────────────────────────────────────────────────────────────
#  Improve Frontend
# ─────────────────────────────────────────────────────────────────────────────

def improve_frontend(log_history: str) -> dict:
    """Ask the LLM to improve frontend/index.html. Returns {improved_code, changelog}."""
    with open(FRONTEND_FILE, "r", encoding="utf-8") as f:
        current = f.read()

    lines, length = [], 0
    for line in current.splitlines():
        if length + len(line) + 1 > 8_000:
            break
        lines.append(line)
        length += len(line) + 1
    current     = "\n".join(lines)
    log_history = log_history[-3000:]

    system = (
        "You are an expert frontend developer performing automated self-improvement on a dark luxury finance tracker web app.\n"
        "You receive the current HTML/CSS/JS single-file frontend and improvement history, then return ONLY a JSON object.\n"
        'The JSON must have exactly two keys:\n'
        '  "improved_code": the complete updated HTML file as a string\n'
        '  "changelog": one sentence describing the single improvement made\n\n'
        "Rules:\n"
        "- Make ONE meaningful visual or UX improvement (new chart type, animation, feature, filter, dark mode toggle, etc.)\n"
        "- Keep the dark luxury aesthetic with gold accents and DM Mono / Cormorant Garamond fonts\n"
        "- Keep Chart.js from cdnjs -- no other CDN changes\n"
        "- API base URL stays as empty string '' (same-origin)\n"
        "- The file must be valid HTML5 with embedded CSS + JS\n"
        "- Do NOT remove existing features\n"
        "- Return ONLY the raw JSON -- no backticks, no extra text"
    )

    user = (
        f"Current frontend code (may be truncated for context):\n{current}\n\n"
        f"Improvement history (do not repeat these):\n{log_history}\n\n"
        "Return JSON only."
    )

    raw = llm_chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=8192,
    )
    raw = strip_fences(raw, "json")
    return robust_json_parse(raw)


# ─────────────────────────────────────────────────────────────────────────────
#  Log helpers
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
#  Main improve() entry point
# ─────────────────────────────────────────────────────────────────────────────

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

        # Small pause -- only needed for Groq rate limits; harmless for Ollama
        if LLM_PROVIDER == "groq":
            time.sleep(3)

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