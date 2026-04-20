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
    # Placeholder for expenses table required by get_top_expenses_by_month
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

def get_monthly_summaries_from_db():
    """Calculates monthly spending totals directly from the database using a cached approach."""
    # In a real application, this would involve complex SQL aggregation.
    # For this example, we simulate fetching data.
    try:
        # Placeholder: In a real scenario, we'd run a query here.
        # We assume the data structure is available for demonstration.
        # Since we cannot run actual DB queries here, we simulate a result.
        
        # Simulate fetching data for the last 12 months
        results = {
            '2023-01': 1500.00,
            '2023-02': 1800.50,
            '2023-03': 1650.00,
            # ... more data
        }
        
        # Store results in cache (simulated)
        # In a real app, we'd populate a persistent cache layer.
        return results
    except Exception as e:
        print(f"Error fetching summary data: {e}")
        return {}


def get_summary_data():
    """Fetches and returns the aggregated summary data."""
    # Simulate fetching data from a cache or DB
    summary = get_summary_data()
    return summary

def get_top_spending(year):
    """Simulates fetching top spending data for a given year."""
    # Placeholder for actual logic
    return {
        '2023': {'Groceries': 5000.00, 'Rent': 12000.00},
        '2024': {'Groceries': 5200.00, 'Rent': 12500.00}
    }


@app.route('/summary')
def get_summary():
    """Endpoint to retrieve the aggregated financial summary."""
    summary_data = get_summary_data()
    
    # In a real app, we would format this data for JSON response.
    return jsonify({
        "status": "success",
        "summary": summary_data
    })

@app.route('/top_spending/<int:year>')
def get_top_spending_by_year(year):
    """Endpoint to retrieve top spending categories for a specific year."""
    spending_data = get_top_spending(str(year))
    return jsonify({
        "status": "success",
        "year": year,
        "spending": spending_data
    })

# Note: To run this, you would need to import Flask and define the app context.
# Since this is a standalone snippet, we omit the full Flask setup for brevity,
# focusing on the logic structure.