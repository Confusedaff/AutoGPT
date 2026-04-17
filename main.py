
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, date
import calendar

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

DB_PATH = "finance.db"

# ─────────────────────────────────────────────
#  Database Setup
# ─────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            type        TEXT    NOT NULL CHECK(type IN ('income','expense')),
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            description TEXT,
            date        TEXT    NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS budgets (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT    NOT NULL UNIQUE,
            limit_amount REAL NOT NULL,
            month    TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS savings_goals (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT  NOT NULL,
            target      REAL  NOT NULL,
            saved       REAL  DEFAULT 0,
            deadline    TEXT,
            created_at  TEXT  DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
#  Transactions
# ─────────────────────────────────────────────

@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    month  = request.args.get("month")   # YYYY-MM
    ttype  = request.args.get("type")
    limit  = request.args.get("limit", 100, type=int)
    offset = request.args.get("offset", 0, type=int)

    query  = "SELECT * FROM transactions WHERE 1=1"
    params = []

    if month:
        query += " AND strftime('%Y-%m', date) = ?"
        params.append(month)
    if ttype:
        query += " AND type = ?"
        params.append(ttype)

    query += " ORDER BY date DESC LIMIT ? OFFSET ?"
    params += [limit, offset]

    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/transactions", methods=["POST"])
def add_transaction():
    data = request.json
    required = ["type", "amount", "category", "date"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO transactions (type, amount, category, description, date) VALUES (?,?,?,?,?)",
        (data["type"], float(data["amount"]), data["category"],
         data.get("description", ""), data["date"])
    )
    conn.commit()
    row = conn.execute("SELECT * FROM transactions WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return jsonify(dict(row)), 201


@app.route("/api/transactions/<int:tid>", methods=["DELETE"])
def delete_transaction(tid):
    conn = get_db()
    conn.execute("DELETE FROM transactions WHERE id=?", (tid,))
    conn.commit()
    conn.close()
    return jsonify({"deleted": tid})


@app.route("/api/transactions/<int:tid>", methods=["PUT"])
def update_transaction(tid):
    data = request.json
    fields = {k: v for k, v in data.items() if k in ["type","amount","category","description","date"]}
    if not fields:
        return jsonify({"error": "No valid fields"}), 400

    set_clause = ", ".join(f"{k}=?" for k in fields)
    values     = list(fields.values()) + [tid]
    conn       = get_db()
    conn.execute(f"UPDATE transactions SET {set_clause} WHERE id=?", values)
    conn.commit()
    row = conn.execute("SELECT * FROM transactions WHERE id=?", (tid,)).fetchone()
    conn.close()
    return jsonify(dict(row))

# ─────────────────────────────────────────────
#  Summary & Analytics
# ─────────────────────────────────────────────

@app.route("/api/summary", methods=["GET"])
def get_summary():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    conn  = get_db()

    income = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='income' AND strftime('%Y-%m',date)=?",
        (month,)
    ).fetchone()[0]

    expenses = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='expense' AND strftime('%Y-%m',date)=?",
        (month,)
    ).fetchone()[0]

    by_category = conn.execute(
        """SELECT category, type, ROUND(SUM(amount),2) as total
           FROM transactions
           WHERE strftime('%Y-%m',date)=?
           GROUP BY category, type ORDER BY total DESC""",
        (month,)
    ).fetchall()

    daily = conn.execute(
        """SELECT date, type, ROUND(SUM(amount),2) as total
           FROM transactions
           WHERE strftime('%Y-%m',date)=?
           GROUP BY date, type ORDER BY date""",
        (month,)
    ).fetchall()

    conn.close()
    return jsonify({
        "month":       month,
        "income":      round(income, 2),
        "expenses":    round(expenses, 2),
        "net":         round(income - expenses, 2),
        "savings_rate": round((income - expenses) / income * 100, 1) if income > 0 else 0,
        "by_category": [dict(r) for r in by_category],
        "daily":       [dict(r) for r in daily],
    })

@app.route("/api/average_spending", methods=["GET"])
def get_average_spending():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    conn  = get_db()

    average_spending = conn.execute(
        "SELECT AVG(amount) FROM transactions WHERE type='expense' AND strftime('%Y-%m',date)=?",
        (month,)
    ).fetchone()[0]

    conn.close()
    return jsonify({
        "month":       month,
        "average_spending": round(average_spending, 2) if average_spending is not None else 0,
    })

@app.route("/api/trends", methods=["GET"])
def get_trends():
    conn  = get_db()
    rows  = conn.execute(
        """SELECT strftime('%Y-%m', date) as month,
                  ROUND(SUM(CASE WHEN type='income'  THEN amount ELSE 0 END), 2) as income,
                  ROUND(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END), 2) as expenses
           FROM transactions
           GROUP BY month
           ORDER BY month DESC
           LIMIT 12"""
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in reversed(rows)])

# ─────────────────────────────────────────────
#  Budgets
# ─────────────────────────────────────────----

@app.route("/api/budgets", methods=["GET"])
def get_budgets():
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    conn  = get_db()
    rows  = conn.execute("SELECT * FROM budgets WHERE month=?", (month,)).fetchall()

    result = []
    for r in rows:
        spent = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE category=? AND type='expense' AND strftime('%Y-%m',date)=?",
            (r["category"], month)
        ).fetchone()[0]
        result.append({**dict(r), "spent": round(spent, 2), "remaining": round(r["limit_amount"] - spent, 2)})

    conn.close()
    return jsonify(result)


@app.route("/api/budgets", methods=["POST"])
def set_budget():
    data  = request.json
    month = data.get("month", datetime.now().strftime("%Y-%m"))
    conn  = get_db()
    conn.execute(
        "INSERT INTO budgets (category, limit_amount, month) VALUES (?,?,?) ON CONFLICT(category) DO UPDATE SET limit_amount=excluded.limit_amount",
        (data["category"], float(data["limit_amount"]), month)
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True}), 201

# ─────────────────────────────────────────────
#  Savings Goals
# ─────────────────────────────────────────----

@app.route("/api/goals", methods=["GET"])
def get_goals():
    conn = get_db()
    rows = conn.execute("SELECT * FROM savings_goals ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/goals", methods=["POST"])
def add_goal():
    data = request.json
    conn = get_db()
    cur  = conn.execute(
        "INSERT INTO savings_goals (name, target, saved, deadline) VALUES (?,?,?,?)",
        (data["name"], float(data["target"]), float(data.get("saved", 0)), data.get("deadline"))
    )
    conn.commit()
    row = conn.execute("SELECT * FROM savings_goals WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return jsonify(dict(row)), 201


@app.route("/api/goals/<int:gid>", methods=["PUT"])
def update_goal(gid):
    data = request.json
    conn = get_db()
    conn.execute("UPDATE savings_goals SET saved=? WHERE id=?", (float(data["saved"]), gid))
    conn.commit()
    row  = conn.execute("SELECT * FROM savings_goals WHERE id=?", (gid,)).fetchone()
    conn.close()
    return jsonify(dict(row))


@app.route("/api/goals/<int:gid>", methods=["DELETE"])
def delete_goal(gid):
    conn = get_db()
    conn.execute("DELETE FROM savings_goals WHERE id=?", (gid,))
    conn.commit()
    conn.close()
    return jsonify({"deleted": gid})

# ─────────────────────────────────────────────
#  Error Handling
# ─────────────────────────────────────────----

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({"error": "Internal server error"}), 500

# ─────────────────────────────────────────────
#  Serve Frontend
# ─────────────────────────────────────────----

@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")

# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────----

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    print(f" Finance Tracker running at http://localhost:{port}")
    app.run(debug=True, port=port)
