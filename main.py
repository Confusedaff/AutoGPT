import sqlite3
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)
DATABASE = 'data.db'

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
    Endpoint to add a new data point with input validation.
    Improvement: Implemented strict input validation and specific error handling.
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

        return jsonify({"message": "Data added successfully", "id": cursor.lastrowid}), 201

    except ValueError as e:
        return jsonify({"error": f"Data type error: {e}"}), 400
    except Exception as e:
        # Catch any other unexpected errors
        app.logger.error(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

@app.route('/api/data', methods=['GET'])
def get_data():
    """
    Endpoint to retrieve all data points.
    """
    conn = get_db_connection()
    try:
        data = conn.execute("SELECT timestamp, value, category FROM data_points ORDER BY timestamp DESC").fetchall()
        
        # Convert rows to a list of dictionaries for JSON serialization
        results = [dict(row) for row in data]
        
        return jsonify(results), 200
    except Exception as e:
        app.logger.error(f"Error retrieving data: {e}")
        return jsonify({"error": "Failed to retrieve data"}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    # Running in debug mode for development
    app.run(debug=True)