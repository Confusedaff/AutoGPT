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
    # Table structure remains the same
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

@app.route('/data', methods=['GET'])
def get_data():
    """Retrieves all data from the database, utilizing caching."""
    cache_key = 'all_data'
    
    if cache_key in data_cache:
        # Return cached data
        return jsonify(data_cache[cache_key])

    try:
        conn = get_db_connection()
        cursor = conn.execute('SELECT * FROM data_points')
        data = cursor.fetchall()
        conn.close()
        
        # Store result in cache
        data_cache[cache_key] = data
        
        return jsonify(data)
    except sqlite3.Error as e:
        # Specific handling for SQLite errors
        app.logger.error(f"SQLite error in get_data: {e}")
        return jsonify({"error": "Database operation failed"}), 500
    except Exception as e:
        # General error handling
        app.logger.error(f"General error in get_data: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/data_by_category', methods=['GET'])
def get_data_by_category():
    """Retrieves data filtered by category, utilizing caching."""
    category = request.args.get('category')
    
    if not category:
        return jsonify({"error": "Missing required parameter: category"}), 400

    cache_key = f'data_by_category_{category}'
    
    if cache_key in data_cache:
        # Return cached data
        return jsonify(data_cache[cache_key])

    try:
        conn = get_db_connection()
        # Query filtered data
        cursor = conn.execute('SELECT * FROM data_points WHERE category = ?', (category,))
        data = cursor.fetchall()
        conn.close()
        
        # Store result in cache
        data_cache[cache_key] = data
        
        return jsonify(data)
    except sqlite3.Error as e:
        app.logger.error(f"SQLite error in get_data: {e}")
        return {"error": "Database error occurred"}