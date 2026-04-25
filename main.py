from flask import Flask, jsonify, request
from datetime import datetime
from collections import defaultdict
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
CACHE_EXPIRY = 3600  # Cache duration in seconds

def calculate_monthly_averages(data):
    """Calculates the average value for each month in the provided data."""
    monthly_totals = {}
    monthly_counts = {}

    for record in data:
        # Assuming the date format is YYYY-MM-DD
        month = record['date'][:7]  # Extract YYYY-MM
        value = record['amount']

        monthly_totals[month] = monthly_totals.get(month, 0) + value
        monthly_counts[month] = monthly_counts.get(month, 0) + 1

    averages = {}
    for month, total in monthly_totals.items():
        count = monthly_counts[month]
        averages[month] = round(total / count, 2)

    return averages

@app.route('/averages', methods=['GET'])
def get_averages():
    """Endpoint to retrieve calculated monthly averages."""
    if not SALES_DATA:
        return {"error": "No sales data available"}, 404

    monthly_averages = calculate_monthly_averages(SALES_DATA)
    return {"monthly_averages": monthly_averages}

# Mock setup for Flask context (assuming this is run within a Flask environment)
# If running standalone, you would need to import Flask and define the data source.
# For this example, we simulate the necessary context:
from flask import Flask
app = Flask(__name__)
SALES_DATA = [
    {'date': '2023-01-15', 'amount': 100.50},
    {'date': '2023-01-20', 'amount': 150.25},
    {'date': '2023-02-10', 'amount': 200.00},
    {'date': '2023-02-25', 'amount': 120.00},
    {'date': '2023-03-05', 'amount': 300.50},
    {'date': '2023-03-15', 'amount': 100.00},
]

if __name__ == '__main__':
    # In a real application, you would run the Flask app.
    # For demonstration purposes, we just show the structure.
    pass