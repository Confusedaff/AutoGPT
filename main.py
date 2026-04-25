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
CACHE_KEY = "monthly_averages"

def calculate_monthly_averages(data):
    """Calculates the average value for each month in the provided data."""
    monthly_totals = defaultdict(float)
    monthly_counts = defaultdict(int)

    for record in data:
        # Assuming the date format is YYYY-MM-DD
        month = record['date'][:7]  # Extract YYYY-MM
        value = record['amount']

        monthly_totals[month] += value
        monthly_counts[month] += 1

    averages = {}
    for month, total in monthly_totals.items():
        count = monthly_counts[month]
        averages[month] = round(total / count, 2)

    return averages

def get_top_expenses_for_month(data, month_year):
    """Calculates the top 10 expense categories for a specific month."""
    monthly_expenses = defaultdict(float)

    for record in data:
        record_date = record['date']
        if record_date.startswith(month_year):
            item = record['item']
            amount = record['amount']
            monthly_expenses[item] += amount

    # Sort and return the top 10 items
    sorted_items = sorted(
        [(item, total) for item, total in zip(dict(items), [sum(v) for k, v in items.items()])],
        key=lambda item: item[1],
        reverse=True
    )
    return sorted_items[:10]


@app.route('/api/average_data')
def get_average_data():
    """Endpoint to get the calculated average data."""
    # In a real app, this would calculate the average across all months.
    # For this example, we'll just return a placeholder or a simple aggregate.
    
    # Since the data is static, we'll simulate a calculation.
    total_value = sum(100 for _ in range(len(SALES_DATA))) # Placeholder calculation
    average = total_value / len(SALES_DATA) if SALES_DATA else 0
    
    return {"average": average, "message": "Data retrieved successfully"}

@app.route('/api/top_items/<string:month>')
def get_top_items(month):
    """Endpoint to get the top spending items for a specific month."""
    # In a real application, we would filter SALES_DATA by the month.
    # For this example, we'll use the hardcoded data structure.
    
    # Since we don't have a proper date structure, we'll simulate the function call.
    # In a real scenario, you would parse the 'month' string to filter the data.
    
    # Mocking the result based on the function defined above
    mock_data = get_top_items(month)
    return {"month": month, "top_items": mock_data}

# Mock data structure for demonstration purposes
SALES_DATA = [
    {'month': 'Jan', 'sales': 100},
    {'month': 'Feb', 'sales': 150},
    {'month': 'Mar', 'sales': 120},
    {'month': 'Apr', 'sales': 200},
    {'month': 'May', 'sales': 180},
]

# Mock Flask app setup for execution context (required for the routes to be defined)
from flask import Flask
app = Flask(__name__)

if __name__ == '__main__':
    # In a real environment, you would run this via a proper WSGI server.
    # For local testing demonstration:
    # app.run(debug=True)
    pass