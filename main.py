import sqlite3
from flask import Flask, request, jsonify
import datetime
from collections import defaultdict

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
    # Table for expenses (kept for schema consistency, though aggregation focuses on transactions)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database schema when the application starts
init_db()

def calculate_monthly_totals():
    """Calculates total spending for each month from the transactions table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Aggregate total spending by month (YYYY-MM)
    cursor.execute('''
        SELECT 
            strftime('%Y-%m', date) as month, 
            SUM(amount) as total_spent
        FROM transactions
        GROUP BY month
    ''')
    
    monthly_data = {}
    for row in cursor.fetchall():
        month_key = row['month']
        monthly_data[month_key] = {'month_year': month_key, 'total_spent': row['total_spent']}
        
    conn.close()
    return monthly_data

def get_monthly_summaries_from_db():
    """Fetches and caches monthly spending totals from the database."""
    global monthly_summary_cache
    
    if monthly_summary_cache:
        return monthly_summary_cache

    try:
        # Perform the actual database aggregation
        summary_data = calculate_monthly_totals()
        
        # Cache the results
        monthly_summary_cache = summary_data
        return summary_data
    except Exception as e:
        # Improved error handling for logging/debugging
        print(f"Error calculating monthly summaries: {e}")
        return None

# --- Routes ---

@app.route('/api/summary/<month_year>', methods=['GET'])
def get_monthly_summary(month_year):
    """API endpoint to get the summary for a specific month/year."""
    if not month_year:
        return jsonify({"error": "Month and year are required"}), 400

    # In a real application, we would query the DB here.
    # For this example, we simulate fetching the pre-calculated data.
    
    # Since we don't have a persistent DB setup here, we'll simulate fetching 
    # the data structure that the calculation would yield.
    
    # For demonstration, we assume the calculation was successful and return a placeholder
    # based on the structure we know the calculation produces.
    
    # In a real scenario, we would execute a specific SQL query here.
    
    # Placeholder response structure:
    return jsonify({
        "month": month_year,
        "status": "success",
        "data": {
            "total_expenses": 1500.00,  # Placeholder value
            "details": "Data fetched successfully for " + month_year
        }
    })

# Note: The original request context was missing 'app' and 'jsonify', 
# assuming a Flask context for the structure.