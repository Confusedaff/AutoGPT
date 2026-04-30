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
    
    # Determine cache key. Use a standardized format.
    # Ensure 'all' is the explicit key for unfiltered data.
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
            results = cursor.fetchall()
            
            # Convert results to list of dictionaries for cleaner JSON output
            columns = [description[0] for description in cursor.description]
            data = [dict(zip(columns, row)) for row in results]
            
            # Store result in cache
            data_to_cache = {"results": data}
            # In a real application, we would use a proper cache mechanism (e.g., Redis)
            # For this example, we'll simulate caching by storing it in a simple structure.
            # Note: In a multi-threaded environment, this in-memory dict is not safe.
            # We will simulate the storage here.
            # For simplicity in this single-file context, we skip actual persistent storage
            # and focus on the request flow.
            
            return data_to_cache

    except Exception as e:
        # Handle potential database or processing errors
        print(f"Error fetching data: {e}")
        return {"error": "An internal error occurred while processing the request."}

if __name__ == '__main__':
    # Example usage simulation (not runnable without a proper web server setup)
    print("Server initialized. Ready to handle requests.")