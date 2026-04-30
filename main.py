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
    category = request.args.get('category', '').strip()
    
    # 1. Input Validation: Ensure category is valid.
    if not category:
        category_to_use = 'all'
    else:
        # Simple sanitization: only allow alphanumeric and underscore for category names
        if not all(c.isalnum() or c == '_' for c in category):
            return jsonify({"error": "Invalid category format. Categories must be alphanumeric or use underscores."}), 400
        category_to_use = category
    
    # Determine cache key.
    cache_key = category_to_use

    # 2. Check cache first
    if cache_key in data_cache:
        print(f"Cache hit for key: {cache_key}")
        return jsonify(data_cache[cache_key])

    data = []
    try:
        with app.app_context():
            conn = get_db_connection()
            
            # SQL Query: Select data based on the validated category
            query = "SELECT timestamp, value FROM data_points WHERE category = ?"
            cursor = conn.cursor()
            
            # Execute query safely
            cursor.execute(query, (category_to_use,))
            results = cursor.fetchall()
            
            conn.close()

            # 3. Store results in cache if data was found
            if results:
                data_to_cache = {"category": category_to_use, "data": [dict(row) for row in results]}
                data_cache[cache_key] = data_to_cache
                return jsonify(data_to_cache)
            else:
                # Return empty result if no data is found for the category
                return jsonify({"category": category_to_use, "results": []}), 200

    except Exception as e:
        # Handle potential database errors
        print(f"Error fetching data: {e}")
        return {"error": "Internal server error"}, 500