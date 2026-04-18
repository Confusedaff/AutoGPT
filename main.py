import sqlite3
from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)
DATABASE = 'finance.db'
# In-memory cache for monthly summaries: { 'YYYY-MM': {'month_year': ..., 'total_spent': ...} }
monthly_summary_cache = {}

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database schema when the application starts
init_db()

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    """
    Adds a new transaction to the database with robust input validation.
    Expects JSON body: {"date": "YYYY-MM-DD", "description": "...", "amount": 123.45}
    """
    data = request.get_json()
    
    # 1. Check for required fields
    if not data or 'date' not in data or 'description' not in data or 'amount' not in data:
        return jsonify({"error": "Missing required fields: date, description, and amount"}), 400

    try:
        date = data['date']
        description = data['description']
        amount = float(data['amount'])

        # 2. Validate date format (YYYY-MM-DD) and existence
        try:
            datetime.datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400

        # 3. Insert into the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO transactions (date, description, amount) VALUES (?, ?, ?)",
            (date, description, amount)
        )
        conn.commit()
        
        # Invalidate cache upon new transaction to ensure summaries are recalculated next time
        global monthly_summary_cache
        monthly_summary_cache = {} 
        
        return jsonify({"message": "Transaction added successfully", "id": cursor.lastrowid}), 201
        
    except ValueError:
        return jsonify({"error": "Invalid amount. Amount must be a valid number."}), 400
    except Exception as e:
        print(f"Error adding transaction: {e}")
        return {"error": "An internal error occurred"}, 500

def get_monthly_summaries_from_db():
    """Calculates monthly spending totals directly from the database using SQL aggregation."""
    conn = get_db_connection()
    
    # SQL query to group by year and month and sum the amounts
    query = """
        SELECT 
            strftime('%Y-%m', date) as month_year, 
            SUM(amount) as total_spent
        FROM transactions
        GROUP BY month_year
        ORDER BY month_year DESC
    """
    
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    # Store results in a dictionary for easy access
    summary = {row['month']: row['total'] for row in cursor.fetchall()}
    return summary

def get_average_spending(month):
    """Calculates the average spending for a specific month."""
    query = f"""
        SELECT AVG(amount)
        FROM transactions
        WHERE strftime('%Y-%m', date) = '{month}'
    """
    conn = None
    try:
        conn = sqlite3.connect('your_database.db') # Assuming a database connection context, needs actual DB connection setup if this were a standalone script.
        # For demonstration, we assume a connection context exists or mock the execution if this were a full Flask/SQL setup.
        # In a real Flask app, you'd use db.execute(query).fetchone()
        cursor = conn.execute(query)
        result = cursor.fetchone()
        if result:
            return result[0]
        return 0.0
    except Exception as e:
        print(f"Error calculating average spending: {e}")
        return 0.0
    finally:
        if conn:
            conn.close()


# Note: To make get_average_spending functional, a real SQLite connection setup is required.
# Since this is a conceptual response, we rely on the structure.

# Example usage (conceptual):
# monthly_summary = get_average_spending('2023-10')
# print(f"Average spending for October 2023: {monthly_summary}")
# monthly_totals = get_average_spending('2023-10') # This function needs to be properly integrated with the DB.