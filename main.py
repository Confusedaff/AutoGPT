import sqlite3
from flask import Flask, request, jsonify

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
    Adds a new transaction to the database with input validation.
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

        # 2. Validate date format (assuming YYYY-MM-DD)
        if not date or len(date) != 10 or date[4] != '-' or date[7] != '-':
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

if __name__ == '__main__':
    # Run the Flask application
    app.run(debug=True)