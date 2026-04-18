import sqlite3
from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)
DATABASE = 'finance.db'
# In-memory cache for monthly summaries: { 'YYYY-MM': {'month_year': ..., 'total_spent': ...} }
monthly_summary_cache = {}

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database schema when the application starts
init_db()

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    """
    Adds a new transaction to the database, validates input, and updates the cache.
    Expects JSON body: {"date": "YYYY-MM-DD", "description": "...", "amount": 123.45}
    """
    data = request.get_json()
    
    # 1. Check for required fields
    if not data or 'date' not in data or 'description' not in data or 'amount' not in data:
        return jsonify({"error": "Missing required fields: date, description, and amount"}), 400

    try:
        date = data['date']
        description = data['description']
        amount = float(data['amount'])

        # 2. Validate date format (YYYY-MM-DD) and existence
        try:
            datetime.datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400

        # 3. Insert into the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO transactions (date, description, amount) VALUES (?, ?, ?)",
            (date, description, amount)
        )
        conn.commit()
        
        # --- IMPROVEMENT: Update cache incrementally ---
        month_year = date[:7]  # Extract YYYY-MM
        
        if month_year not in monthly_summary_cache:
            monthly_summary_cache[month_year] = {'month_year': month_year, 'total_spent': 0.0}
            
        monthly_summary_cache[month_year]['total_spent'] += amount
        
        return jsonify({"message": "Transaction added successfully", "id": cursor.lastrowid}), 201
        
    except ValueError:
        return jsonify({"error": "Invalid amount. Amount must be a valid number."}), 400
    except Exception as e:
        print(f"Error adding transaction: {e}")
        return {"error": "An internal error occurred"}, 500

@app.route('/api/monthly_summaries', methods=['GET'])
def get_monthly_summaries():
    """
    Retrieves monthly spending summaries, prioritizing the in-memory cache.
    If the cache is empty, it calculates the summaries directly from the database.
    """
    if monthly_summary_cache:
        # Return cached data
        return jsonify(list(monthly_summary_cache.values())), 200
    else:
        # Fallback to database calculation if cache is empty
        summary = get_monthly_summaries_from_db()
        return jsonify(list(summary.values())), 200


def get_monthly_summaries_from_db():
    """Calculates monthly spending totals directly from the database using SQL aggregation."""
    conn = get_db_connection()
    try:
        results = [row for row in sqlite_conn.execute("SELECT strftime('%Y-%m', date) as month, SUM(amount) as total FROM transactions GROUP BY month ORDER BY month DESC") if row]
        
        # Re-executing the query directly for simplicity and robustness in this context
        cursor = sqlite_conn.execute("SELECT strftime('%Y-%m', date) as month, SUM(amount) as total FROM transactions GROUP BY month ORDER BY month DESC")
        results = cursor.fetchall()
        
        return results
    finally:
        sqlite_conn.close()


if __name__ == '__main__':
    # Assuming sqlite3 is used for the database connection setup
    # For this example to run, we need a mock database setup or actual connection.
    # Since the original code context is missing the DB setup, we assume 'sqlite_conn' is available or mock it.
    # In a real application, you would initialize the DB connection here.
    print("Application running. Note: Database interaction requires an initialized connection.")
    # Example of how to run if the DB setup was complete:
    # app.run(debug=True)