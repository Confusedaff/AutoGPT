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

# Initialize the database on startup
initialize_db()

@app.route('/api/data', methods=['POST'])
def add_data():
    """
    Endpoint to add a new data point with input validation and cache invalidation.
    """
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        timestamp = data.get('timestamp')
        value = data.get('value')
        category = data.get('category')

        # Input Validation
        if not timestamp or not value or not category:
            return jsonify({"error": "Missing required fields: timestamp, value, and category"}), 400
        
        if not isinstance(value, (int, float)):
            return jsonify({"error": "Value must be a number"}), 400
        
        # Basic timestamp format check (assuming ISO format or similar)
        try:
            # Ensure timestamp is in a format SQLite can handle well (ISO format is fine)
            datetime.fromisoformat(timestamp)
        except ValueError:
            return jsonify({"error": "Invalid timestamp format. Use ISO format."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO data_points (timestamp, value, category) VALUES (?, ?, ?)",
            (timestamp, float(value), category)
        )
        conn.commit()
        conn.close()

        # Invalidate cache upon successful write
        data_cache.clear()
        
        return jsonify({"message": "Data added successfully", "id": cursor.lastrowid}), 201

    except ValueError as e:
        return jsonify({"error": f"Data type error: {e}"}), 400
    except Exception as e:
        app.logger.error(f"An unexpected error occurred during data insertion: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

@app.route('/api/data', methods=['GET'])
def get_data():
    """Endpoint to retrieve all data."""
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.execute('SELECT * FROM data')
        data = cursor.fetchall()
        conn.close()
        return jsonify(data)
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

# Note: To make this runnable, we need to ensure the database file exists and is populated.
# Since the original prompt didn't provide setup, I'll assume a standard SQLite setup is implied for the functions above to work.
# For a complete runnable example, one would typically add setup code here.
# Since I cannot modify the environment outside the function definitions, I rely on the structure provided.