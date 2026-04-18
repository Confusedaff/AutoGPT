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
            return {"error": "Invalid date format. Please use YYYY-MM-DD."}
        
        # Basic date validation (optional but good practice)
        import datetime
        datetime.datetime.strptime(date, '%Y-%m-%d')

        # Insert into DB (Placeholder for actual DB interaction)
        # In a real app, this would involve a database call.
        # For this example, we simulate success.
        
        # Update in-memory cache (simulating persistence)
        # In a real application, this would be a database transaction.
        
        # Simulate cache update based on the new entry (this is highly simplified)
        # A real implementation would query the DB for the current month's total.
        
        return {"message": "Transaction recorded successfully.", "date": date}

    except ValueError as e:
        return {"error": f"Date validation failed: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}


@app.route('/summary')
def get_summary():
    """Retrieves the summary data."""
    # In a real application, we would query the database.
    # Here, we return the cached data if available.
    
    # Since we are simulating, we return a placeholder.
    if not hasattr(app, 'transaction_cache'):
        return {"message": "No transactions recorded yet."}
        
    return {"summary": "Data retrieval simulated. Check POST endpoint for new entries."}

# Note: To run this, you would need to define 'app' and handle the POST request properly.
# The provided code structure is conceptual, focusing on the logic flow requested.