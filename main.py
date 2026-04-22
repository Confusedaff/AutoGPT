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

def get_average_spending_by_month(data, month_key):
    """Calculates the average spending for a specific month."""
    monthly_totals = defaultdict(float)
    count = 0
    
    for record in data:
        try:
            date_obj = datetime.strptime(record['date'], '%Y-%m-%d')
            month_key_record = date_obj.strftime('%Y-%m')
            
            if month_key_record == month_key:
                monthly_totals[month_key_record] += record['amount']
                count += 1
        except (KeyError, ValueError):
            continue

    if count == 0:
        return None
    
    return round(monthly_totals[month_key] / count, 2)


@app.route('/api/monthly_summary', methods=['GET'])
def get_monthly_summary_endpoint():
    """
    Endpoint to retrieve the calculated monthly spending summary, utilizing caching.
    """
    cache_key = "monthly_summary_static"
    
    if cache_key in ANALYSIS_CACHE:
        print("Cache hit for monthly summary.")
        return {"result": "cached", "data": "data not shown for brevity"}
    
    print("Calculating monthly summary...")
    # Simulate calculation time
    # time.sleep(0.1) 
    
    # In a real application, this would involve heavy DB/calculation
    result = {"result": "calculated", "data": {"Jan": 1000, "Feb": 1500}}
    
    # Store result in cache
    # cache.set(result) 
    return result

# New endpoint to calculate average spending for a month
@app.route('/average_spending/<month_year>', methods=['GET'])
def get_average_spending(month_year):
    """Calculates the average spending for a given month and year."""
    try:
        # Simple parsing for demonstration (e.g., '2023-01')
        year = int(month_year[:4])
        month = int(month_year[5:7])
        
        # In a real app, this would query the data source
        # For this demo, we'll just return a placeholder based on the previous calculation logic
        
        # Mocking the calculation based on the structure of the data
        if month == 1:
            return {"month": month, "year": year, "average_spending": 1250.00}
        elif month == 2:
            return {"month": month, "year": year, "average_spending": 1375.00}
        else:
            return {"month": month, "year": year, "average_spending": 1125.00}

    except ValueError:
        return {"error": "Invalid date format. Please use YYYY-MM."}, 400

# Note: To run this example, you would need to import Flask and define an app context.
# For this demonstration, we assume the structure above is what would be exposed via a web framework.