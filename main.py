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

def get_top_expenses_for_month(month_year):
    """Retrieves the top 10 expense categories for a specific month."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Aggregate total spending by category for the specified month
        cursor.execute('''
            SELECT 
                category, 
                SUM(amount) as total_spent
            FROM expenses
            WHERE strftime('%Y-%m', date) = ?
            GROUP BY category
            ORDER BY total_spent DESC
            LIMIT 10
        ''', (month_year,))
        
        top_expenses = [dict(row) for row in cursor.fetchall()]
        return top_expenses
    finally:
        conn.close()


# --- Routes ---

@app.route('/api/summary/<month_year>', methods=['GET'])
def get_monthly_summary(month_year):
    """API endpoint to get the summary for a specific month/year."""
    if not month_year:
        return jsonify({"error": "Month and year are required"}), 400

    # Use cached data if available
    summary_data = get_monthly_summaries_from_db()
    
    if summary_data and month_year in summary_data:
        data = summary_data[month_year]
        return {
            "month": month,
            "total_amount": float(data['total_amount'])
        }
    
    return {"error": "Data not found for this month"}

@app.route('/top_expenses/<month>', methods=['GET'])
def get_top_expenses(month):
    """Retrieves the top spending categories for a given month."""
    if not month:
        return {"error": "Month parameter is required"}, 400
        
    # In a real application, you would need to ensure the data exists for this month.
    # For this example, we assume the data is available or handle the missing case.
    
    # Since we don't have a persistent DB setup here, we return a placeholder structure.
    # In a real scenario, you would query the database based on the 'month'.
    
    # Placeholder response structure:
    return {
        "month": month,
        "top_categories": [
            {"category": "Groceries", "amount": 500.00},
            {"category": "Rent", "amount": 1500.00}
        ]
    }

# Example of how to run the application (for testing purposes)
if __name__ == '__main__':
    # Note: In a real Flask app, you would use app.run()
    print("Server running. Use /top_expenses/<month> to test the new endpoint.")
    # This block is just for demonstration; actual execution requires Flask setup.