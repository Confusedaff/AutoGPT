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
    monthly_totals = {}
    for record in data:
        try:
            # Ensure 'date' and 'amount' keys exist
            date_obj = datetime.strptime(record['date'], '%Y-%m-%d')
            month_key = date_obj.strftime('%Y-%m')
            monthly_totals[month_key] = monthly_totals.get(month_key, 0.0) + record['amount']
        except (KeyError, ValueError):
            # Skip records missing 'date' or with invalid date format
            continue
    return monthly_totals

@app.route('/api/monthly_summary', methods=['GET'])
def get_monthly_summary_endpoint():
    """
    Endpoint to retrieve the calculated monthly spending summary, utilizing caching.
    """
    # Use a cache key based on the data itself (or a timestamp if data were dynamic)
    cache_key = "monthly_summary_static"
    
    if cache_key in ANALYSIS_CACHE:
        print(f"Cache hit for {cache_key}")
        return jsonify({
            "source": "cache",
            "summary": ANALYSIS_CACHE[cache_key]
        })

    print(f"Cache miss. Calculating summary...")
    
    # Perform the expensive calculation
    summary = get_monthly_summary(SALES_DATA)
    
    # Store result in cache
    ANALYSIS_CACHE[cache_key] = summary
    
    return jsonify({
        "source": "database_simulation",
        "summary": summary
    })

if __name__ == '__main__':
    # Run the application
    # In a production environment, use a proper WSGI server.
    print("Starting Flask server. Access /api/summary to test.")
    # Note: Running directly might require setting debug=True for development.
    # app.run(debug=True) 
    pass