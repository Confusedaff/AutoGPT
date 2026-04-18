"""
improver.py -- AI Self-Improvement Engine
Primary:  Local Ollama (gemma4:e2b or any model you have pulled)
Fallback: Groq API (llama-3.3-70b-versatile) if Ollama is unavailable

Strategy: TWO-STEP approach to avoid JSON-wrapping failures with local models.
  Step 1 -- ask for ONLY the improved code inside a code fence
  Step 2 -- ask for ONLY the one-line changelog
This is far more reliable than asking local models to produce valid JSON
with a multi-thousand-character escaped string inside it.

Set LLM_PROVIDER=groq  in .env to force Groq.
Set OLLAMA_MODEL=gemma4:e2b (or llama3.2:latest, etc.) to choose model.
"""

import os
import re
import json
import time
import shutil
import py_compile
import tempfile
from datetime import date, datetime
from pathlib import Path

# ── Provider config ───────────────────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()   # "ollama" | "groq"
OLLAMA_URL   = os.getenv("OLLAMA_URL",   "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e2b")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.3-70b-versatile"

BACKEND_FILE  = "main.py"
FRONTEND_FILE = os.path.join("frontend", "index.html")
LOG_FILE      = "improvement_log.md"
BACKUP_DIR    = ".backups"


# ─────────────────────────────────────────────────────────────────────────────
#  LLM providers
# ─────────────────────────────────────────────────────────────────────────────

def ollama_chat(messages: list, max_tokens: int = 8192) -> str:
    """Call local Ollama. No rate limits, no key needed."""
    import requests
    payload = {
        "model":    OLLAMA_MODEL,
        "messages": messages,
        "stream":   False,
        "options":  {"num_predict": max_tokens, "temperature": 0.4},
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Ollama not reachable at {OLLAMA_URL}. "
            f"Run: ollama serve && ollama pull {OLLAMA_MODEL}"
        )


def groq_chat(messages: list, max_tokens: int = 8192) -> str:
    """Call Groq with retry/backoff."""
    import requests
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set.")
    for attempt in range(4):
        try:
            r = requests.post(
                GROQ_URL,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {GROQ_API_KEY}"},
                json={"model": GROQ_MODEL, "messages": messages,
                      "max_tokens": max_tokens, "temperature": 0.4},
                timeout=120,
            )
            if r.status_code == 429:
                wait = 30 * (2 ** attempt)
                print(f"  [groq] 429 -- retrying in {wait}s")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt == 3:
                raise
            wait = 15 * (2 ** attempt)
            print(f"  [groq] Error: {e} -- retrying in {wait}s")
            time.sleep(wait)
    raise RuntimeError("Groq failed after all retries")


def llm_chat(messages: list, max_tokens: int = 8192) -> str:
    """Route to correct provider, fall back to Groq if Ollama fails."""
    if LLM_PROVIDER == "groq":
        print(f"  [llm] Groq ({GROQ_MODEL})")
        return groq_chat(messages, max_tokens)
    print(f"  [llm] Ollama ({OLLAMA_MODEL})")
    try:
        return ollama_chat(messages, max_tokens)
    except RuntimeError as e:
        if GROQ_API_KEY:
            print(f"  [llm] Ollama failed ({e}) -- falling back to Groq")
            return groq_chat(messages, max_tokens)
        raise


# ─────────────────────────────────────────────────────────────────────────────
#  Code extraction helpers
# ─────────────────────────────────────────────────────────────────────────────

def extract_code_fence(text: str, lang: str = "") -> str:
    """
    Pull the first fenced code block out of an LLM response.
    Tries  ```lang ... ```  first, then any  ``` ... ```.
    Falls back to stripping fence lines and returning the body.
    """
    if lang:
        m = re.search(rf"```{lang}\s*\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip()
    m = re.search(r"```[a-z]*\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # No fences -- strip any stray backtick lines
    lines = [l for l in text.splitlines() if not l.strip().startswith("```")]
    return "\n".join(lines).strip()


def extract_first_sentence(text: str) -> str:
    """Return the first meaningful line as the changelog entry."""
    for line in text.splitlines():
        line = line.strip(" \t\r\n*-#`")
        if line and len(line) > 5:
            return line[:300]
    return text.strip()[:300]


# ─────────────────────────────────────────────────────────────────────────────
#  Validation & backup
# ─────────────────────────────────────────────────────────────────────────────

def backup(filepath: str):
    Path(BACKUP_DIR).mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest  = os.path.join(BACKUP_DIR, f"{stamp}_{Path(filepath).name}")
    shutil.copy2(filepath, dest)
    print(f"  [backup] -> {dest}")


def validate_python(code: str) -> tuple[bool, str]:
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False,
                                     mode="w", encoding="utf-8") as f:
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
    for tag in ["<!DOCTYPE html>", "<html", "</html>", "<body", "</body>"]:
        if tag.lower() not in code.lower():
            return False, f"Missing tag: {tag}"
    return True, ""


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
#  Two-step improvement: code first, changelog second
# ─────────────────────────────────────────────────────────────────────────────

def two_step_improve(
    current_code: str,
    log_history:  str,
    file_type:    str,
    system_code:  str,
    max_tokens:   int = 8192,
) -> dict:
    """
    Step 1: get improved code inside a fenced block (no JSON wrapper).
    Step 2: get a one-line changelog in a follow-up message.
    Returns {"improved_code": str, "changelog": str}
    """
    # ── Step 1: improved code ─────────────────────────────────────────────────
    user_code = (
        f"Current code:\n```{file_type}\n{current_code}\n```\n\n"
        f"Previous improvements (do not repeat):\n{log_history}\n\n"
        f"Return the complete improved {file_type} file inside a single "
        f"```{file_type} ... ``` block. No explanation, no extra text."
    )
    raw_code = llm_chat(
        [{"role": "system", "content": system_code},
         {"role": "user",   "content": user_code}],
        max_tokens=max_tokens,
    )
    improved_code = extract_code_fence(raw_code, file_type)

    # ── Step 2: changelog ─────────────────────────────────────────────────────
    user_log = (
        "In ONE sentence (max 20 words), describe the single improvement you just made. "
        "No bullet points, no preamble. Sentence only."
    )
    raw_log = llm_chat(
        [{"role": "system",    "content": "You are a concise technical writer."},
         {"role": "user",      "content": user_code},
         {"role": "assistant", "content": raw_code},
         {"role": "user",      "content": user_log}],
        max_tokens=80,
    )
    changelog = extract_first_sentence(raw_log)

    return {"improved_code": improved_code, "changelog": changelog}


# ─────────────────────────────────────────────────────────────────────────────
#  Improve Backend
# ─────────────────────────────────────────────────────────────────────────────

def improve_backend(log_history: str) -> dict:
    with open(BACKEND_FILE, "r", encoding="utf-8") as f:
        current = f.read()

    lines, length = [], 0
    for line in current.splitlines():
        if length + len(line) + 1 > 10_000:
            break
        lines.append(line)
        length += len(line) + 1
    current     = "\n".join(lines)
    log_history = log_history[-3000:]

    system_code = (
        "You are an expert Python / Flask developer.\n"
        "Make ONE meaningful improvement to the Flask backend "
        "(new endpoint, better error handling, analytics, input validation, caching, etc.).\n"
        "Rules:\n"
        "- Do NOT break existing API contracts\n"
        "- Keep Flask + SQLite only (no external DB)\n"
        "- Valid Python 3.10+\n"
        "- No dummy or test data\n"
        "- Return the COMPLETE updated Python file in a ```python ... ``` block. Nothing else."
    )
    return two_step_improve(current, log_history, "python", system_code)


# ─────────────────────────────────────────────────────────────────────────────
#  Improve Frontend
# ─────────────────────────────────────────────────────────────────────────────

def improve_frontend(log_history: str) -> dict:
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

    system_code = (
        "You are an expert frontend developer improving a dark luxury finance tracker.\n"
        "Make ONE meaningful visual or UX improvement "
        "(new chart, animation, filter, summary card, tooltip, responsive fix, etc.).\n"
        "Rules:\n"
        "- Dark luxury aesthetic: background #1a1a1a, gold #ffd700 accents, "
        "DM Mono / Cormorant Garamond fonts\n"
        "- Chart.js from cdnjs only -- no new CDN libraries\n"
        "- API base URL stays '' (same-origin)\n"
        "- Valid HTML5 with all CSS + JS embedded in one file\n"
        "- Do NOT remove any existing features\n"
        "- Return the COMPLETE updated HTML file in a ```html ... ``` block. Nothing else."
    )
    return two_step_improve(current, log_history, "html", system_code)


# ─────────────────────────────────────────────────────────────────────────────
#  Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def improve(target: str = "both") -> list[str]:
    """
    Run improvement cycle.
    target: 'backend' | 'frontend' | 'both'
    Returns list of changelog strings.
    """
    changelogs  = []
    log_history = read_log()

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
                print(f"  OK: {note}")
        except Exception as e:
            print(f"  [!] Backend improvement failed: {e}")

        if LLM_PROVIDER == "groq":
            time.sleep(3)

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
                print(f"  OK: {note}")
        except Exception as e:
            print(f"  [!] Frontend improvement failed: {e}")

    return changelogs


if __name__ == "__main__":
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "both"
    results = improve(t)
    print("\nChangelogs:", results)