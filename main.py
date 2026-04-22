from flask import Flask, jsonify, request
from datetime import datetime
from collections import defaultdict
import operator
import time

app = Flask(__name__)

# --- Database Simulation (Simulating SQLite persistence via in-memory structure) ---
# Consolidated and standardized sales data for analysis
SALES_DATA = [
    {"date": "2023-01-01", "amount": 100, "item": "Laptop"},
    {"date": "2023-01-05", "amount": 50, "item": "Mouse"},
    {"date": "2023-01-10", "amount": 200, "item": "Keyboard"},
    {"date": "2023-02-01", "amount": 150, "item": "Monitor"},
    {"date": "2023-02-15", "amount": 75, "item": "Mouse"},
]

def get_sales_data():
    """Processes raw sales data into structured summaries."""
    sales_summary = {}
    for record in SALES_DATA:
        date_obj = datetime.datetime.strptime(record['date'], '%Y-%m-%d')
        month_key = date_obj.strftime('%Y-%m')
        
        if month_key not in sales_summary:
            sales_summary[month_key] = {'total_sales': 0, 'items': set()}
            
        sales_summary[month_key]['total_sales'] += record['amount']
        sales_summary[month_key]['items'].add(record['item'])
        
    return sales_summary

SALES_SUMMARY = get_sales_data()

@app.route('/summary')
def get_summary():
    """Returns the aggregated sales summary by month."""
    return jsonify(SALES_SUMMARY)

@app.route('/summary/<month>')
def get_monthly_summary(month):
    """Returns the sales summary for a specific month."""
    if month in SALES_SUMMARY:
        return jsonify(SALES_SUMMARY[month])
    return jsonify({"error": "Month not found"}), 404

# Note: To run this, you would need to import Flask and datetime.
# Since this is a standalone snippet, I'll assume the necessary imports 
# (like Flask and datetime) are present in the execution environment.
# For a runnable example, we need to add imports:
import datetime
from flask import Flask, jsonify

app = Flask(__name__)

if __name__ == '__main__':
    # Example usage simulation (not runnable without proper setup)
    # print("Running Flask app simulation...")
    pass