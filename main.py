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

        # 2. Validate date format (YYYY-MM-DD)
        if not isinstance(date, str) or len(date) != 10:
            return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400
        
        # Basic date validation
        datetime.datetime.strptime(date, '%Y-%m-%d')

        # 3. Insert into DB
        conn = get_db_connection()
        cursor = conn.execute(
            "INSERT INTO transactions (date, description, amount) VALUES (?, ?, ?)",
            (date, description, amount)
        )
        conn.commit()
        conn.close()

        # 4. Update in-memory cache based on the new entry
        # Extract YYYY-MM from the date
        month_key = date[:7]
        
        if month_key not in monthly_summary_cache:
            monthly_summary_cache[month_key] = {'month_year': month_key, 'total_spent': 0.0}
        
        # Update the total spent for that month
        monthly_summary_cache[month_key]['total_spent'] += amount
        
        return jsonify({
            "message": "Transaction recorded successfully.", 
            "date": date,
            "month_summary_updated": monthly_summary_cache[month_key]
        }), 201

    except ValueError as e:
        return jsonify({"error": f"Date validation failed: {e}"}), 400
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error occurred: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route('/summary')
def get_summary():
    """Retrieves the summary data."""
    # Return the cached data if available.
    if db_summary_cache.get('all'):
        return jsonify({"summary": db_summary_cache['all']})
    
    return jsonify({"message": "No transactions recorded yet."})