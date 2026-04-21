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

def get_sales_by_item(data):
    """Calculates the total sales amount for each unique item."""
    item_totals = defaultdict(float)
    for record in data:
        try:
            item = record['item']
            amount = record['amount']
            item_totals[item] += amount
        except KeyError:
            # Skip records missing required keys
            continue
    return dict(item_totals)


@app.route('/api/monthly_summary', methods=['GET'])
def get_monthly_summary_endpoint():
    """
    Endpoint to retrieve the calculated monthly spending summary, utilizing caching.
    """
    cache_key = "monthly_summary_static"
    
    if cache_key in ANALYSIS_CACHE:
        print(f"Cache hit for {cache_key}")
        return jsonify({
            "source": "cache",
            "summary": ANALYSIS_CACHE[cache_key]
        })

    print(f"Cache miss. Calculating monthly summary...")
    
    # Perform the expensive calculation
    summary = get_monthly_summary(SALES_DATA)
    
    # Store result in cache
    ANALYSIS_CACHE[cache_key] = summary
    
    return jsonify({
        "source": "database_simulation",
        "summary": summary
    })

@app.route('/api/sales_by_item', methods=['GET'])
def get_sales_by_item_endpoint():
    """
    Endpoint to retrieve the total sales amount aggregated by item, utilizing caching.
    """
    cache_key = "sales_by_item_static"
    
    if cache_key in ANALYSIS_CACHE:
        print(f"Cache hit for {cache_key}")
        return jsonify({
            "source": "cache",
            "item_totals": ANALYSIS_CACHE[cache_key]
        })

    print(f"Cache miss. Calculating sales by item...")
    
    # Perform the calculation
    item_summary = get_sales_by_item(SALES_DATA)
    
    # Store result in cache
    ANALYSIS_CACHE[cache_key] = item_summary
    
    return jsonify({
        "source": "database_simulation",
        "item_totals": item_summary
    })

if __name__ == '__main__':
    # Run the application
    print("Starting Flask server. Access /api/monthly_summary or /api/sales_by_item to test.")
    # Note: In a real application, use a proper WSGI server.
    # For demonstration, we keep it simple.
    # app.run(debug=True)
    pass