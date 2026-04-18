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

def get_monthly_average_spending_from_db():
    """Calculates the average spending for each month directly from the database."""
    conn = get_db_connection()
    try:
        # Calculate average spending per month
        cursor = conn.execute("SELECT strftime('%Y-%m') as month, AVG(amount) as average FROM transactions GROUP BY month ORDER BY month DESC")
        results = cursor.fetchall()
        
        # Cache the results
        db_summary_cache['averages'] = results
        
        return results
    finally:
        conn.close()

# Pre-calculate summaries upon startup
get_monthly_summaries_from_db()
get_monthly_average_spending_from_db()

@app.route('/api/summary/<string:month>')
def get_summary(month):
    """Endpoint to retrieve summary data for a specific month."""
    # In a real application, you would fetch data from a proper database.
    # For this example, we simulate fetching based on the pre-calculated data.
    
    # Since we only pre-calculated the full set, we'll return a placeholder
    # or simulate a lookup if the data was stored differently.
    
    # For demonstration, we'll return a generic success message.
    return {"month": month, "status": "Data retrieval simulated"}

@app.route('/api/summary')
def get_all_summary():
    """Endpoint to retrieve all pre-calculated summary data."""
    # In a real application, you would load the results from a persistent store.
    return {"message": "Full summary data is available in the backend."}

@app.route('/api/top_level')
def get_top_level():
    """Endpoint to retrieve the overall summary."""
    return get_all_summary()