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
    
    # Store results in the cache
    global monthly_summary_cache
    monthly_summary_cache = {row['month_year']: {'month_year': row['month_year'], 'total_spent': row['total_spent']} for row in results}
    
    return monthly_summary_cache

@app.route('/summaries')
def summaries():
    """Endpoint to retrieve pre-calculated monthly summaries, utilizing the cache."""
    if not monthly_summary_cache:
        # If cache is empty, recalculate from the database
        get_monthly_summaries_from_db()
    
    return jsonify(monthly_summary_cache)

@app.route('/api/top_expenses/<YYYY-MM>')
def top_expenses(year_month):
    """
    New endpoint: Retrieves the top 10 spending descriptions for a specific month.
    Example usage: /api/top_expenses/2023-10
    """
    try:
        # Validate the input format
        datetime.datetime.strptime(year_month, '%Y-%m')
    except ValueError:
        return jsonify({"error": "Invalid month format. Please use YYYY-MM."}), 400

    conn = get_db_connection()
    
    # SQL query to find the top 10 descriptions by total spent for the given month
    query = """
        SELECT 
            description, 
            SUM(amount) as total_spent
        FROM transactions
        WHERE strftime('%Y-%m', date) = ?
        GROUP BY description
        ORDER BY total_spent DESC
        LIMIT 10
    """
    
    cursor = conn.cursor()
    cursor.execute(query, (year_month,))
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        return jsonify({"message": f"No transactions found for {year_month}"}), 200

    # Format results for JSON response
    formatted_results = [
        {"description": row['description'], "total_spent": round(row['total_spent'], 2)}
        for row in results
    ]
    
    return jsonify({
        "month": year_month,
        "top_expenses": formatted_results
    }), 200

if __name__ == '__main__':
    # In a real application, use a proper WSGI server.
    print("Server starting...")
    # Note: Running this directly is for demonstration purposes only.
    # app.run(debug=True)