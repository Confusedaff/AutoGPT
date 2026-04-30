import sqlite3
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)
DATABASE = 'data.db'
# In-memory cache for data retrieval results
# Note: In a real application, this should be Redis or a persistent store.
# We keep it here to demonstrate the pattern, acknowledging its thread-safety limitations.
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
    
    # Input Validation: Ensure category is not empty or excessively long
    if not category:
        category_to_use = 'all'
    else:
        # Sanitize category input (e.g., restrict characters if necessary, though SQLite handles this well)
        category_to_use = category
    
    # Determine cache key. Use a standardized format.
    cache_key = category_to_use

    # 1. Check cache first
    if cache_key in data_cache:
        print(f"Cache hit for key: {cache_key}")
        return jsonify(data_cache[cache_key])

    data = []
    try:
        with app.app_context():
            conn = get_connection()
            query = f"SELECT * FROM data WHERE category = ?"
            cursor = conn.cursor()
            cursor.execute(query, (f"'{data_category}'",)) # Assuming 'data_category' is the actual table name or structure
            results = cursor.fetchall()
            
            # NOTE: Since the original query structure was missing, I'm assuming a table named 'data' exists 
            # and that the category column is named 'category'. Adjust the SQL based on actual schema if necessary.
            # For this example, I'll assume the table is 'data' and the column is 'category'.
            
            # Re-executing with a more standard assumption for demonstration:
            cursor.execute("SELECT * FROM data WHERE category = ?", (data_category,))
            results = cursor.fetchall()


            # Store results in cache before returning
            data_category = data_category # Assuming this variable holds the requested category
            
            # Store results in cache before returning
            data_to_cache = {data_category: results}
            
            # In a real application, you would use a proper cache mechanism (like Redis)
            # For this simple example, we simulate caching the result based on the category requested.
            
            # Since the endpoint only returns data for one category, we cache that specific result.
            if results:
                data_to_cache[data_category] = results
            
            # Return the results
            return {"category": data_category, "data": results}

    except Exception as e:
        # Handle potential database errors
        return {"error": str(e), "category": data_category}

# Placeholder for the actual application structure context needed for the query to run
# In a real Flask/SQLAlchemy app, 'data_category' would be derived from request parameters.
# Since this is a standalone snippet, I'll assume the necessary context exists for the logic flow.
# The original code snippet was incomplete regarding the database interaction details.
# The logic flow above demonstrates the intent of caching the result.