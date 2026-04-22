from flask import Flask, jsonify, request
from datetime import datetime
from collections import defaultdict
import operator
import time

app = Flask(__name__)

# --- Database Simulation (Simulating SQLite persistence via in-memory structure) ---
# Consolidated and standardized sales data for analysis
SALES_DATA = [
    {"date": "2023-10-01", "amount": 150.50, "item": "Laptop"},
    {"date": "2023-10-15", "amount": 200.00, "item": "Mouse"},
    {"date": "2023-11-05", "amount": 300.75, "item": "Monitor"},
    {"date": "2023-11-20", "amount": 50.25, "item": "Webcam"},
    {"date": "2023-10-25", "amount": 100.00, "item": "Keyboard"},
]

# --- Caching Mechanism ---
ANALYSIS_CACHE = {}

def get_monthly_summary(data):
    """Calculates the total sum for each month from the provided transaction data."""
    monthly_totals = defaultdict(float)
    for record in data:
        try:
            # Ensure 'date' and 'amount' keys exist
            date_obj = datetime.strptime(record['date'], '%Y-%m-%d')
            month_key = date_obj.strftime('%Y-%m')
            monthly_totals[month_key] += record['amount']
        except (KeyError, ValueError) as e:
            # Log or handle errors for robustness
            print(f"Skipping record due to error: {e} in record {record}")
            continue
    return dict(monthly_totals)

def get_item_sales(data):
    """Calculates total sales per item."""
    item_totals = {}
    for item, amount in data:
        item_totals[item] = item_totals.get(item, 0) + amount
    return item_totals

@app.route('/api/sales/summary', methods=['GET'])
def get_sales_summary():
    """Endpoint to get the overall sales summary."""
    sales_data = []
    for item, amount in SALES_DATA:
        sales_data.append({"item": item, "total_sales": amount})
    return jsonify({"summary": sales_data})

@app.route('/api/sales/items', methods=['GET'])
def get_item_sales_report():
    """Endpoint to get the total sales per item."""
    item_sales = get_item_sales(SALES_DATA)
    return jsonify({"item_sales": item_sales})

# Note: Since this is a conceptual example, I'll assume 'app' and 'jsonify' are imported from Flask.
# For a runnable example, Flask setup would be required.