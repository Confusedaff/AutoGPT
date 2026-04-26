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
    # Check cache first
    if 'all_data' in data_cache:
        return jsonify(data_cache['all_data'])

    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()
        # Query the unified table name
        cursor.execute("SELECT * FROM data_points")
        data = cursor.fetchall()
        conn.close()

        # Store result in cache
        data_cache['all_data'] = [dict(row) for row in data]
        return jsonify(data_cache['all_data'])

@app.route('/data/<category>')
def get_data_by_category(category):
    """Endpoint to retrieve data filtered by category."""
    # Input validation: Ensure category is provided and is a string
    if not category or not isinstance(category, str):
        return jsonify({"error": "Missing or invalid category parameter"}), 400

    query = "SELECT * FROM data_points WHERE category = ?"
    conn = None
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute(query, (category,))
        results = cursor.fetchall()
        
        # Re-fetch data to ensure consistency if the previous query logic was complex, 
        # but for simplicity here, we rely on the structure.
        
        # Since we are using raw SQL execution, we fetch the results directly.
        
        # Note: For this to work, the data must be in the 'data.db' file.
        # Assuming the data structure is: (id, value, category)
        
        # Re-executing the query to get the actual results:
        cursor.execute(query, (category,))
        results = cursor.fetchall()


        # Convert results to a list of dictionaries for JSON response
        columns = [desc[0] for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in results]
        
        return jsonify(data)

    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# Note: To make this runnable, you would need to ensure the database file ('data.db') 
# exists and contains the 'data_points' table.