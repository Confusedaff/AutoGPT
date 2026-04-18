import sqlite3
from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)
DATABASE = 'finance.db'
# In-memory cache for monthly summaries: { 'YYYY-MM': {'month_year': ..., 'total_spent': ...} }
monthly_summary_cache = {}
# Cache for database derived summaries: { 'YYYY-MM': [list_of_summaries] }
db_summary_cache = {}

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

def get_monthly_summaries_from_db():
    """Calculates monthly spending totals directly from the database using SQL aggregation."""
    conn = get_db_connection()
    try:
        # Optimized single query to get all monthly summaries
        cursor = conn.execute("SELECT strftime('%Y-%m') as month, SUM(amount) as total FROM transactions GROUP BY month ORDER BY month DESC")
        results = cursor.fetchall()
        
        # Cache the results
        db_summary_cache['all'] = results
        
        return results
    finally:
        conn.close()

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    """
    Adds a new transaction to the database, validates input, and updates the cache.
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

        # 2. Validate date format (YYYY-MM-DD)
        if not isinstance(date, str) or len(date) != 10:
            return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400
        
        # Basic date validation
        datetime.datetime.strptime(date, '%Y-%m-%d')

        # 3. Insert into DB
        conn = get_db_connection()
        cursor = conn.execute(
            "INSERT INTO transactions (date, description, amount) VALUES (?, ?, ?)",
            (date, description, amount)
        )
        conn.commit()
        conn.close()

        # 4. Update in-memory cache based on the new entry
        # Extract YYYY-MM from the date
        month_key = date[:7]
        
        if month_key not in monthly_summary_cache:
            monthly_summary_cache[month_key] = {'month_year': month_key, 'total_spent': 0.0}
        
        # Update the total spent for that month
        monthly_summary_cache[month_key]['total_spent'] += amount
        
        return jsonify({
            "message": "Transaction recorded successfully.", 
            "date": date,
            "month_summary_updated": monthly_summary_cache[month_key]
        }), 201

    except ValueError as e:
        return jsonify({"error": f"Date validation failed: {e}"}), 400
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error occurred: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route('/api/transactions', methods=['GET'])
def get_all_transactions():
    """Retrieves all transactions from the database."""
    conn = get_db_connection()
    try:
        transactions = conn.execute("SELECT id, date, description, amount FROM transactions ORDER BY date DESC").fetchall()
        return jsonify([dict(t) for t in transactions])
    finally:
        conn.close()


@app.route('/summary')
def get_summary():
    """Retrieves the cached monthly spending totals."""
    if db_summary_cache.get('all'):
        return jsonify({"summary": db_summary_cache['all']})
    
    return jsonify({"message": "No transactions recorded yet."})


@app.route('/api/average_spending/<string:month_year>')
def get_average_spending(month_year):
    """
    Calculates the average spending for a specific month (YYYY-MM).
    """
    try:
        # Calculate total and count for the specified month
        query = "SELECT SUM(amount) FROM transactions WHERE strftime('%Y-%m', date) = ?"
        cursor = sqlite3.connect('your_database_name') # NOTE: Replace 'your_database_name' with your actual DB connection logic if this were a real app.
        cursor.row_factory = sqlite3.Row
        cursor.execute(query, (f"{month}-%",))
        result = cursor.fetchone()
        
        if result:
            average = result[0]
            return {"month": month, "average_amount": round(average, 2)}
        else:
            return {"month": month, "average_amount": 0.00}
    except Exception as e:
        # In a real application, proper error handling for DB connection/query errors is crucial.
        return {"error": str(e)}


# NOTE: To make the above function runnable, you would need to import sqlite3 and ensure a proper database connection setup.
# Since this is a conceptual example, the actual SQLite connection logic is omitted for brevity, focusing on the API endpoint structure.
# For this example to run, assume a connection context exists.