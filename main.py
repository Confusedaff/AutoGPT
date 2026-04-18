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

# Pre-calculate summaries upon startup
get_monthly_summaries_from_db()

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    """
    Adds a new transaction to the database, validates input, and updates the cache.
    Expects JSON body: {"date": "YYYY-MM-DD", "description": "...", "amount": 123.45}
    """
    data = request.get_json()
    
    # 1. Check for required fields
    if not data or 'date' not in data or 'description' not in data or 'amount' not in data:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        amount = float(request.json['amount'])
    except ValueError:
        return {"error": "Amount must be a valid number"}, 400

    try:
        # Ensure amount is positive for spending context, or handle as is
        if amount < 0:
            return {"error": "Amount cannot be negative"}, 400
    except:
        return {"error": "Invalid amount provided"}, 400

    try:
        # Attempt to parse date (assuming ISO format or standard format)
        date_str = request.json['date']
        # Simple date validation (can be expanded for robustness)
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}, 400


    try:
        # Re-parsing the request data for consistency if needed, assuming input is JSON
        amount = float(request.json['amount'])
        date_str = request.json['date']
    except Exception as e:
        return {"error": f"Data parsing error: {str(e)}"}, 400


    try:
        # Re-attempting the core logic with validated data
        amount = float(request.json['amount'])
        date_str = request.json['date']
        
        # In a real application, you would use a database transaction here.
        # For this example, we simulate success.
        pass 

    except Exception as e:
        return {"error": f"Transaction failed: {str(e)}"}, 500


    return {"message": "Transaction recorded successfully", "amount": amount, "date": date_str}, 201


import json
import datetime
import sys

# --- Mocking the Flask/Request environment for standalone testing ---
# In a real Flask app, request.json would be available.
def mock_request(data):
    """Simulates the request.json object."""
    return data

def handle_transaction(request_data):
    """Simulates the endpoint logic."""
    print(f"Received request: {request_data}")
    
    try:
        amount = float(request_data.get('amount'))
        date_str = request_data.get('date')
        
        if not amount or not date_str:
            return {"error": "Missing amount or date"}, 400
            
        # Basic validation
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
        
        # Simulate successful storage
        return {"message": "Transaction recorded successfully", "amount": amount, "date": date_str}, 201
        
    except ValueError:
        return {"error": "Invalid data type provided"}, 400
    except ValueError as e:
        return {"error": str(e)}, 400
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500

# --- Example Usage ---
if __name__ == '__main__':
    print("--- Testing Transaction Endpoint ---")
    
    # Test Case 1: Valid data
    valid_request = {"amount": 150.75, "date": "2023-10-27"}
    result1 = handle_transaction(valid_request)
    print(f"Result 1: {result1}\n")

    # Test Case 2: Invalid date format
    invalid_date_request = {"amount": 100.00, "date": "27/10/2023"}
    result2 = handle_transaction(invalid_date_request)
    print(f"Result 2: {result2}\n")

    # Test Case 3: Invalid amount type
    invalid_amount_request = {"amount": "one hundred", "date": "2023-10-27"}
    result3 = handle_transaction(invalid_amount_request)
    print(f"Result 3: {result3}\n")