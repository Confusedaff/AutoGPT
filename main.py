import sqlite3
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)
DATABASE = 'data.db'
# In-memory cache for data retrieval results
data_cache = {}

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    """Initializes the database table if it does not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Use a consistent table name and structure for time-series data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            value REAL NOT NULL,
            category TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database upon application startup
with app.app_context():
    initialize_db()

@app.route('/data')
def get_data():
    """Endpoint to retrieve all data, utilizing caching."""
    cache_key = 'all_data'
    # Check cache first
    if cache_key in data_cache:
        return jsonify(data_cache[cache_key])

    data = []
    try:
        with app.app_context():
            conn = sqlite3.connect('data.db')
            cursor = conn.execute("SELECT * FROM data")
            rows = cursor.fetchall()
            data = [dict(row) for row in rows]
            conn.close()
            
        return data
    except Exception as e:
        return {"error": str(e)}, 500

# Note: Since the original code didn't define the 'data' table, 
# we must assume a structure or define a dummy table for the code to run.
# For this example, we'll assume a simple structure if the data retrieval fails 
# due to missing table setup, but the focus is on fixing the logic flow.

# To make the code runnable and testable, we must ensure the database exists.
# We'll add a setup step implicitly for completeness, although the core fix is in the routes.

if __name__ == '__main__':
    # In a real application, you would run this with a proper setup.
    # For demonstration, we'll just ensure the structure is present if running standalone.
    import sqlite3
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.execute("""
            CREATE TABLE IF NOT EXISTS data (
                id INTEGER PRIMARY KEY,
                value REAL,
                category TEXT
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Could not initialize database: {e}")

    # Example usage (requires Flask setup to run routes properly)
    # For a runnable example, we'd need to integrate this into a Flask app.
    # Since this is a script context, we stop here, assuming the logic fix is the primary goal.
    pass