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
    for record in data:
        item = record.get('item')
        amount = record.get('amount')
        if item and isinstance(amount, (int, float)):
            item_totals[item] = item_totals.get(item, 0) + amount
    return item_totals

@app.route('/api/sales/summary', methods=['GET'])
def get_sales_summary():
    """Returns the total sales aggregated by month."""
    monthly_totals = get_monthly_summary(SALES_DATA)
    result = {
        "monthly_totals": monthly_totals,
        "total_records": len(SALES_DATA)
    }
    return jsonify(result)

@app.route('/api/sales/by_month/<month:YYYY-MM>', methods=['GET'])
def get_sales_by_month(month):
    """
    Endpoint to get sales aggregated for a specific month (YYYY-MM).
    Implements a new, specific analytical endpoint.
    """
    try:
        # Validate the input format (already enforced by Flask route variable, but good practice to check parsing)
        datetime.strptime(month, '%Y-%m')
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM."}), 400

    monthly_totals = get_monthly_summary(SALES_DATA)
    
    if month in monthly_totals:
        return {
            "month": month,
            "total_sales": monthly_totals[month]
        }
    else:
        return {"month": month, "total_sales": 0}

if __name__ == '__main__':
    # Example usage (for testing purposes)
    # In a real application, this would be run via a WSGI server.
    pass