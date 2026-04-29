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
    # Standardize table name and structure for time-series data
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
    """Endpoint to retrieve data, supporting filtering by category and utilizing caching."""
    category = request.args.get('category')
    
    # Determine cache key. Use a standardized format.
    cache_key = category if category else 'all'

    # 1. Check cache first
    if cache_key in data_cache:
        print(f"Cache hit for key: {cache_key}")
        return jsonify(data_cache[cache_key])

    data = []
    try:
        with app.app_context():
            conn = get_db_connection()
            
            # 2. Dynamic SQL based on request parameters
            query = "SELECT * FROM data_points"
            params = []
            
            if category:
                query += " WHERE category = ?"
                params.append(category)
            
            cursor = conn.execute(query, params)
            results = cursor.fetchall() # Corrected: results should be fetched from the cursor
            
            # Convert results to list of dictionaries for cleaner JSON output
            columns = [description[0] for description in cursor.description]
            data = [dict(zip(columns, row)) for row in results]
            
            # 3. Store result in cache before returning
            data_cache[cache_key] = data
            print(f"Cache miss. Stored result for key: {cache_key}")
            
            return jsonify(data)

    except sqlite3.Error as e:
        # Handle specific database errors
        print(f"Database error: {e}")
        return jsonify({"error": "Database operation failed"}), 500
    except Exception as e:
        # Handle other unexpected errors
        print(f"Unexpected error: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500