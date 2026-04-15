# LEDGER — Self-Improving Personal Finance Tracker

A personal finance tracker that **automatically improves itself every day** using AI, and commits the changes to GitHub between 6–11 PM.

---

## ✦ Features

- **Flask + SQLite backend** — transactions, budgets, savings goals, analytics
- **Dark luxury web frontend** — Chart.js dashboards, real-time summaries
- **Groq AI improver** — uses free `llama-3.3-70b-versatile` to evolve the code daily
- **Auto GitHub commits** — pushes improvements at a random time between 6–11 PM

---

## ✦ Project Structure

```
finance-tracker/
├── main.py                # Flask backend (self-improving)
├── frontend/
│   └── index.html         # Web UI (self-improving)
├── improver.py            # Groq AI improvement engine
├── runner.py              # Scheduler + git auto-commit
├── improvement_log.md     # History of all AI improvements
├── requirements.txt
├── .env.example
├── .gitignore
├── setup_scheduler.bat    # Windows Task Scheduler setup
└── setup_cron.sh          # Linux/macOS cron setup
```

---

## ✦ Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd finance-tracker
pip install -r requirements.txt
```

### 2. Get Your FREE Groq API Key

1. Go to **[https://console.groq.com](https://console.groq.com)**
2. Sign up (free, no credit card)
3. Create an API key

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and paste your GROQ_API_KEY
```

### 4. Initialize Git

```bash
git init
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

> **GitHub Auth Tip:** Use a Personal Access Token or SSH key so the auto-commit can push without a password prompt.
> Settings → Developer settings → Personal access tokens → Fine-grained token with "Contents: Read & Write".

### 5. Run the App

```bash
python main.py
# → http://localhost:5000
```

### 6. Schedule Auto-Improvements

**Windows:**
```
Run setup_scheduler.bat as Administrator
```

**Linux / macOS:**
```bash
bash setup_cron.sh
```

---

## ✦ How It Works

```
Every day at 6 PM:
  runner.py wakes up
  → sleeps random 0–5 hours  (so commit lands 6–11 PM)
  → improver.py reads main.py + index.html
  → calls Groq API (FREE llama-3.3-70b)
  → receives improved code + changelog
  → validates (syntax check, HTML check)
  → backs up old file to .backups/
  → writes improved file
  → logs changelog to improvement_log.md
  → git add --all && git commit && git push
```

---

## ✦ Testing

Run immediately without delay:
```bash
python runner.py --no-delay
```

Test just the improver:
```bash
python improver.py backend     # improve only main.py
python improver.py frontend    # improve only index.html
python improver.py both        # improve both (default)
```

---

## ✦ Safety Features

| Feature | Details |
|---|---|
| Python syntax check | `py_compile` validates before saving |
| HTML sanity check | Checks for required tags |
| File backups | Every old version saved to `.backups/` |
| Improvement log | Full history in `improvement_log.md` |
| Rate limiting | 3s pause between backend + frontend calls |
| No prompt injection | System prompt is hard-coded |

---

## ✦ Groq Free Tier

- **Model:** `llama-3.3-70b-versatile`
- **Free limits:** 14,400 requests/day, 6,000 tokens/min
- **Cost:** $0
- **Sign up:** [https://console.groq.com](https://console.groq.com)

---

## ✦ Rollback

To revert to a previous version:
```bash
ls .backups/                          # see all backups
cp .backups/20240315_183042_main.py main.py   # restore backend
git checkout HEAD~1 -- main.py        # or via git history
```
