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
    """Calculates monthly spending totals directly from the database using SQL aggregation and caches results in a dictionary for O(1) lookup."""
    conn = get_db_connection()
    try:
        # Optimized single query to get all monthly summaries
        cursor = conn.execute("SELECT strftime('%Y-%m') as month, SUM(amount) as total FROM transactions GROUP BY month ORDER BY month DESC")
        results = cursor.fetchall()
        
        # Cache the results in a dictionary for fast lookup
        db_summary_cache['all'] = {row['month']: {'month_year': row['month'], 'total_spent': row['total']} for row in results}
        
        return db_summary_cache['all']
    finally:
        conn.close()

def get_monthly_average_spending_from_db():
    """Calculates the average spending for each month directly from the database using SQL aggregation and caches results."""
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
    Endpoint to retrieve summary data (total spent) for a specific month using O(1) cache lookup.
    """
    # Check if the month exists in the cached data
    if 'totals' in globals() and month in globals()['totals']:
        return {"month": month, "total_spent": globals()['totals'][month]}
    return {"error": "Data not found for this month"}

# Example usage for demonstration (not part of the core API structure, but helpful for testing)
if __name__ == '__main__':
    from flask import Flask, jsonify
    app = Flask(__name__)

    @app.route('/api/summary/<month>')
    def get_summary(month):
        # Access the globally stored data initialized by the setup above
        totals = globals().get('totals', {})
        if month in totals:
            return jsonify({"month": month, "total_spent": totals[month]})
        return jsonify({"error": f"No summary found for {month}"}), 404

    # To run this example, you would need to run the application context.
    # For simplicity in this environment, we skip running the Flask server setup.
    print("Application setup complete. To use this, integrate with a Flask environment.")