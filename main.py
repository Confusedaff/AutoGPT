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
    {"date": "2023-03-01", "amount": 300, "item": "Laptop"},
    {"date": "2023-03-15", "amount": 100, "item": "Monitor"},
    {"date": "2023-03-20", "amount": 50, "item": "Mouse"},
]

# --- Caching Mechanism ---
# Cache to store results of expensive calculations
CACHED_AVERAGES = None
CACHE_EXPIRY = 3600  # Cache results for 1 hour

def calculate_monthly_averages(data):
    """Calculates the average transaction value per month."""
    monthly_totals = {}
    monthly_counts = {}

    for record in data:
        # Assuming 'date' is in a format that allows easy month extraction (e.g., YYYY-MM-DD)
        try:
            date_obj = datetime.datetime.strptime(record['date'], '%Y-%m-%d')
            month_key = date_obj.strftime('%Y-%m')
            amount = record['amount']

            monthly_totals[month_key] = monthly_totals.get(month_key, 0) + amount
            monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
        except (ValueError, KeyError) as e:
            # Handle malformed data gracefully
            print(f"Skipping record due to error: {e}")
            continue

    monthly_averages = {}
    for month, total in monthly_totals.items():
        count = monthly_counts[month]
        monthly_averages[month] = round(total / count, 2)

    return monthly_averages

from datetime import datetime

@app.route('/api/monthly_averages', methods=['GET'])
def get_monthly_averages():
    """Endpoint to retrieve calculated monthly averages."""
    if not data:
        return jsonify({"error": "No data available"}), 404

    averages = calculate_monthly_averages(data)
    return jsonify({"monthly_averages": averages})

# Placeholder for Flask app setup (required for the routes to function)
from flask import Flask, jsonify

app = Flask(__name__)

# Example of how to run (for testing purposes)
if __name__ == '__main__':
    # In a real application, you would run this with a proper WSGI server
    # For this example, we just define the structure.
    print("Flask app initialized. Run with a proper server to test endpoints.")
    # app.run(debug=True)