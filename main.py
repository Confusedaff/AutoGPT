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

# Initialize the database upon application startup (optional but good practice for setup)
with app.app_context():
    # Ensure the database file exists or is ready if needed, though for simple SQLite it often just creates it on first write.
    pass


@app.route('/data')
def get_data():
    """Endpoint to retrieve all data (example usage)."""
    with app.app_context():
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM data")
        data = cursor.fetchall()
        conn.close()
        return jsonify(data)

@app.route('/data/<category>')
def get_data_by_category(category):
    """Endpoint to retrieve data filtered by category."""
    with app.app_context():
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        # Filter data by the category parameter
        cursor.execute("SELECT * FROM data WHERE category = ?", (category,))
        data = cursor.fetchall()
        conn.close()
        if not data:
            return jsonify({"message": f"No data found for category: {category}"}), 404
        return jsonify(data)

# Example of how to run this (requires Flask setup)
if __name__ == '__main__':
    import sqlite3
    from flask import Flask, jsonify
    app = Flask(__name__)

    @app.route('/data')
    def get_data():
        with app.app_context():
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM data")
            data = cursor.fetchall()
            conn.close()
            return jsonify(data)

    @app.route('/data/<category>')
    def get_data_by_category(category):
        with app.app_context():
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM data WHERE category = ?", (category,))
            data = cursor.fetchall()
            conn.close()
            if not data:
                return jsonify({"message": f"No data found for category: {category}"}), 404
            return jsonify(data)

    # Setup dummy data for testing
    with app.app_context():
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS data (id INTEGER PRIMARY KEY, name TEXT, category TEXT)")
        cursor.execute("INSERT OR IGNORE INTO data (id, name, category) VALUES (1, 'Item A', 'Electronics')")
        cursor.execute("INSERT OR IGNORE INTO data (id, name, category) VALUES (2, 'Item B', 'Books')")
        cursor.execute("INSERT OR IGNORE INTO data (id, name, category) VALUES (3, 'Item C', 'Electronics')")
        conn.commit()
        conn.close()


    app.run(debug=True)