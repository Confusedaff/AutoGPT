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
        
        return True
    except sqlite3.Error as e:
        print(f"Database error during monthly summary calculation: {e}")
        return False
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
        
        return True
    except sqlite3.Error as e:
        print(f"Database error during monthly average calculation: {e}")
        return False
    finally:
        conn.close()

def get_top_expenses_by_month(month):
    """Calculates the top 10 expense categories for a given month."""
    if not isinstance(month, str):
        return []
        
    try:
        # Ensure the input is in the expected format (YYYY-MM) if necessary, 
        # though we rely on the caller for format consistency here.
        pass
    except Exception:
        return []

    try:
        query = f"""
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE strftime('%Y-%m', date) = ?
        GROUP BY category
        ORDER BY total DESC
        LIMIT 10
        """
        cursor = sqlite3.Cursor()
        cursor.execute(query, (month,))
        results = cursor.fetchall()
        return [{"category": row[0], "total": row[1]} for row in results]
    except Exception as e:
        # print(f"Error executing query: {e}")
        return []

import sqlite3 # Import sqlite3 here to ensure it's available for the function scope

# --- Example usage setup (assuming a database structure exists) ---
# Note: In a real application, the database connection setup would be external.
# For this standalone example, we assume a simple setup for demonstration purposes.
# If this code were run in a real environment, the database connection would need to be established.