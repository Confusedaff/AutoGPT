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

        # Basic check for date validity (e.g., ensuring month/day are plausible, though full date validation is complex)
        import datetime
        try:
            datetime.datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date provided. Please ensure the date is a real calendar date."}), 400


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
        # Extract YYYY-MM part
        year_month = month[:7]
        
        conn = get_db_connection()
        # Calculate the average amount for transactions in the specified month
        cursor = conn.execute(
            "SELECT AVG(amount) FROM transactions WHERE date LIKE ? || '%' AND date LIKE ? || '%'",
            (f"{year_month}%", f"{year_month}%")
        )
        result = cursor.fetchone()
        
        if result:
            average_amount = result[0]
            return jsonify({
                "month": year_month,
                "average_amount": round(average_amount, 2)
            }), 200
        else:
            return jsonify({"error": f"No transactions found for the month {year_month}"}), 404

    except Exception as e:
        print(f"Error calculating average spending: {e}")
        return jsonify({"error": "An internal error occurred while calculating average spending"}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    # Run the Flask application
    app.run(debug=True)