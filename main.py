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
    
    # Retrieve all summary data from the cache
    all_summaries = db_summary_cache.get('all', [])
    
    # Filter for the specific month
    for summary in all_summaries:
        if summary['month'] == month:
            return jsonify({
                "month": summary['month'],
                "total_spent": summary['total'],
                "status": "Success"
            })
            
    return jsonify({"error": f"Summary data for month {month} not found."}), 404

@app.route('/api/summary')
def get_all_summary():
    """Endpoint to retrieve all pre-calculated summary data."""
    if 'all' in db_summary_cache:
        return jsonify({
            "message": "Full summary data retrieved successfully.",
            "data": db_summary_cache['all']
        })
    return jsonify({"message": "No summary data available."})

@app.route('/api/average_spending/<string:month>')
def get_average_spending(month):
    """Endpoint to retrieve the average spending for a specific month."""
    
    averages = db_summary_cache.get('averages', [])
    
    for avg in averages:
        if avg['month'] == month:
            return jsonify({
                "month": avg['month'],
                "average_spending": avg['average']
            })
            
    return jsonify({"error": f"Average spending data for month {month} not found."}), 404

@app.route('/api/top_expenses/<string:month>')
def get_top_expenses(month):
    """Endpoint to retrieve the top 10 expense categories for a given month."""
    
    # Note: The current database structure only stores transactions (date, description, amount), 
    # not categories explicitly. To fulfill this request meaningfully, we must aggregate 
    # based on descriptions or assume a category mechanism exists. 
    # Since we cannot introduce a new table, we will simulate finding the top expenses 
    # by grouping transactions for the month.
    
    conn = get_db_connection()
    try:
        # Group transactions by description (as a proxy for category) and sum amounts
        cursor = conn.execute(
            "SELECT description, SUM(amount) as total FROM transactions WHERE strftime('%Y-%m', date) = ? GROUP BY description ORDER BY total DESC LIMIT 10",
            (month,)
        )
        top_expenses = cursor.fetchall()
        
        if not top_expenses:
            return jsonify({"message": f"No expense data found for {month}."})
            
        return jsonify({
            "month": month,
            "top_expenses": [
                {"description": item['description'], "total": item['total']}
                for item in top_expenses
            ]
        })
    finally:
        conn.close()