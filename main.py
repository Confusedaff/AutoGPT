import sqlite3
from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)
DATABASE = 'finance.db'
# In-memory cache for monthly summaries: { 'YYYY-MM': {'month_year': ..., 'total_spent': ...} }
monthly_summary_cache = {}
# Cache for database derived summaries: { 'YYYY-MM': [list_of_summaries] }
db_summary_cache = {}

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

def get_monthly_summaries_from_db():
    """Calculates monthly spending totals directly from the database using SQL aggregation."""
    conn = get_db_connection()
    try:
        # Optimized single query to get all monthly summaries
        cursor = conn.execute("SELECT strftime('%Y-%m') as month, SUM(amount) as total FROM transactions GROUP BY month ORDER BY month DESC")
        results = cursor.fetchall()
        
        # Cache the results
        db_summary_cache['all'] = results
        
        return results
    finally:
        conn.close()

# Pre-calculate summaries upon startup
get_monthly_summaries_from_db()

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    """
    Adds a new transaction to the database, validates input, and updates the cache.
    Expects JSON body: {"date": "YYYY-MM-DD", "description": "...", "amount": 123.45}
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_fields = ['date', 'description', 'amount']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields: date, description, and amount"}), 400

    date_str = data['date']
    description = data['description']
    amount_str = data['amount']

    # 1. Validate Amount
    try:
        amount = float(amount_str)
        if amount < 0:
            return jsonify({"error": "Amount cannot be negative"}), 400
    except ValueError:
        return jsonify({"error": "Amount must be a valid number"}), 400

    # 2. Validate Date Format
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD"}), 400

    # 3. Database Insertion (Atomic Operation)
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO transactions (date, description, amount) VALUES (?, ?, ?)',
            (date_str, description, amount)
        )
        conn.commit()
        return {"message": "Transaction added successfully", "id": sqlite3.lastrowid}
    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        return {"error": f"Database error: {str(e)}"}
    finally:
        conn.close()

if __name__ == '__main__':
    import sqlite3 # Import sqlite3 here for the function to work standalone if needed, though it's usually imported at the top.
    # Example usage setup (assuming this script is run):
    # app.run(debug=True)
    pass