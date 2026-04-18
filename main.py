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
        return jsonify({"message": "Transaction added successfully", "id": cursor.lastrowid}), 201
        
    except ValueError:
        return jsonify({"error": "Invalid amount. Amount must be a valid number."}), 400
    except Exception as e:
        print(f"Error adding transaction: {e}")
        return {"error": "An internal error occurred"}, 500

def get_all_monthly_summaries():
    """Calculates and returns the total spending for each month."""
    from datetime import datetime
    
    # Fetch all transactions
    query = "SELECT DATE(transaction_date) as transaction_date, amount FROM transactions"
    cursor = sqlite3.Cursor()
    cursor.execute(query)
    transactions = cursor.fetchall()
    
    monthly_totals = {}
    
    for row in transactions:
        date = row[0]
        amount = row[1]
        # Format key as YYYY-MM
        month_key = date.strftime('%Y-%m')
        
        if month_key not in monthly_totals:
            monthly_totals[month_key] = 0.0
        
        monthly_totals[month_key] += amount
        
    # Store results in the cache (simulating a persistent cache update)
    # In a real application, this would interact with Redis or a DB table.
    global CACHE
    CACHE = monthly_totals
    
    return monthly_totals

# Initialize a global cache variable (required for the function above to work)
CACHE = {}

@app.route('/summaries')
def summaries():
    """Endpoint to retrieve pre-calculated monthly summaries."""
    monthly_data = get_all_monthly_summaries()
    return jsonify(monthly_data)

# Note: To run this code, you would need to import necessary libraries (like sqlite3)
# and define the Flask app context. For this example, we assume the necessary setup exists.