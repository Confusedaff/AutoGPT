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
    # This endpoint remains for backward compatibility, though we add a new one below.
    return {"message": "Use /api/sales/summary for detailed monthly breakdown."}

@app.route('/api/sales/summary', methods=['GET'])
def get_sales_summary():
    """Returns the total sales aggregated by month."""
    # Calculate monthly totals
    monthly_totals = {}
    for record in SALES_DATA:
        month = record['date'][:7]  # Extract YYYY-MM
        amount = record['amount']
        monthly_totals[month] = monthly_totals.get(month, 0) + amount

    # Format the result
    result = {
        "monthly_totals": monthly_totals,
        "total_records": len(SALES_DATA)
    }
    return result

# Note: For this code to run, 'SALES_DATA' must be defined globally or imported.
# Assuming SALES_DATA is defined as a list of dictionaries for demonstration purposes:
SALES_DATA = [
    {"date": "2023-01-15", "amount": 150.00},
    {"date": "2023-02-20", "amount": 200.50},
    {"date": "2023-03-10", "amount": 350.75},
    {"date": "2023-04-01", "amount": 100.00},
]