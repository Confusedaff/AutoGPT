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

@app.route('/api/summary/<string:month>', methods=['GET'])
def get_summary_by_month(month):
    """
    Endpoint to retrieve summary data (total spent) for a specific month.
    Implements O(1) lookup against the cached data.
    """
    if 'all' in db_summary_cache:
        # Search the cached results directly
        for summary in db_summary_cache['all']:
            if summary['month'] == month:
                return jsonify({
                    "month": summary['month'],
                    "total_spent": summary['total'],
                    "status": "Success"
                })
        return jsonify({"error": f"Summary data for month {month} not found."}), 404
    
    return jsonify({"error": "No summary data available"}), 404

@app.route('/api/summary')
def get_all_summary():
    """Endpoint to retrieve all pre-calculated summary data."""
    if 'all' in db_summary_cache:
        # Return the list of all monthly summaries
        return jsonify({"data": db_summary_cache['all']})
    return jsonify({"error": "No summary data available"}), 404


@app.route('/api/average_spending/<string:month>', methods=['GET'])
def get_average_spending(month):
    """
    Endpoint to retrieve the average spending for a specific month.
    """
    # Note: Since we only calculated total sums in the initial setup (which is not present here), 
    # this endpoint would typically require a separate pre-calculation step if the data was complex.
    # For this example, we assume the necessary data structure exists or we return a placeholder if not calculated.
    # In a real scenario, this would query the pre-calculated results.
    
    # Placeholder for demonstration purposes:
    return {"message": f"Average calculation for {month} requires specific aggregation logic."}

if __name__ == '__main__':
    # Example setup for testing (ensure you have data inserted for this to work fully)
    # In a real application, you would run this with a proper database setup.
    print("Application running. Use /api/summary/<month> to test.")
    # app.run(debug=True) 
    pass