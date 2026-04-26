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

@app.route('/data', methods=['GET'])
def get_data():
    """Retrieves all data from the database."""
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.execute('SELECT * FROM data')
        data = cursor.fetchall()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Note: To make this runnable, you would need to import Flask and sqlite3, 
# and ensure the database file 'data.db' exists or is created.
# For this response, I assume the necessary imports are available in the execution environment.