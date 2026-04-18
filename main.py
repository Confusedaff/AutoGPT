import sqlite3
from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)
DATABASE = 'finance.db'

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
        return jsonify({"error": "An internal error occurred while processing the request"}), 500
    finally:
        conn.close()

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Retrieves all transactions from the database."""
    conn = get_db_connection()
    transactions = conn.execute('SELECT * FROM transactions ORDER BY date DESC').fetchall()
    conn.close()
    
    # Convert rows to a list of dictionaries for JSON response
    result = [dict(row) for row in transactions]
    return jsonify(result)

@app.route('/api/average_spending', methods=['GET'])
def get_average_spending():
    """
    Calculates the average transaction amount for a specific month.
    Expects query parameter: ?month=YYYY-MM
    """
    month = request.args.get('month')
    
    if not month or len(month) != 7 or month[4] != '-':
        return jsonify({"error": "Invalid month format. Please provide a date in YYYY-MM format."}), 400

    try:
        # Use LIKE operator for reliable month filtering in SQLite
        search_pattern = f"{month}%"
        
        conn = get_db_connection()
        cursor = conn.execute(
            "SELECT AVG(amount) FROM transactions WHERE date LIKE ? LIMIT 1",
            (search_pattern,)
        )
        result = cursor.fetchone()
        
        if result:
            average_amount = result[0]
            return jsonify({
                "month": month,
                "average_amount": round(average_amount, 2)
            }), 200
        else:
            return jsonify({"error": f"No transactions found for the month {month}"}), 404

    except Exception as e:
        print(f"Error calculating average spending: {e}")
        return jsonify({"error": "An internal error occurred while calculating the average."})

@app.route('/api/monthly_summary', methods=['GET'])
def get_monthly_summary():
    """
    Calculates the total spending for each month present in the database.
    Returns a list of dictionaries, one for each month.
    """
    conn = get_db_connection()
    
    # Group transactions by year and month, calculating the sum of amounts
    query = """
        SELECT 
            strftime('%Y-%m', date) AS month_year, 
            SUM(amount) AS total_spent
        FROM transactions
        GROUP BY month_year
        ORDER BY month_year DESC
    """
    transactions = conn.execute(query).fetchall()
    conn.close()
    
    # Convert results to a list of dictionaries
    result = [dict(row) for row in transactions]
    return jsonify(result)