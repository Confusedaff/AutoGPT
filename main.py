from flask import Flask, jsonify, request
from datetime import datetime
from collections import defaultdict
import operator

app = Flask(__name__)

# --- Database Simulation (Simulating SQLite persistence via in-memory structure) ---
SALES_DATA = [
    {"date": "2023-01-15", "amount": 100},
    {"date": "2023-01-20", "amount": 150},
    {"date": "2023-02-10", "amount": 200},
    {"date": "2023-03-05", "amount": 120},
    {"date": "2023-04-25", "amount": 300},
    {"date": "2024-01-01", "amount": 50},
    {"date": "2024-02-15", "amount": 100},
]

# --- Data Processing and Caching Mechanism ---

# Cache storage
CACHED_MONTHLY_AVERAGES = None

def get_sales_by_month(data, month):
    """Filters sales data for a specific month and calculates the average."""
    if not data:
        return {"status": "error", "message": f"No sales data found for month {month}."}

    try:
        target_month = int(month)
    except ValueError:
        return {"status": "error", "message": "Invalid month format."}

    monthly_amounts = []
    
    for record in data:
        try:
            record_date = datetime.strptime(record['date'], "%Y-%m-%d")
            if record_date.month == target_month:
                monthly_amounts.append(float(record['amount']))
        except (ValueError, KeyError, TypeError):
            # Skip malformed records
            continue

    if not monthly_amounts:
        return {"status": "error", "message": f"No sales data found for month {target_month}."}

    average = sum(monthly_amounts) / len(monthly_amounts)
    return {"status": "success", "month": target_month, "average_amount": round(average, 2), "count": len(monthly_amounts)}

def calculate_all_monthly_averages(data):
    """Calculates the average sales amount for every month present in the data."""
    if not data:
        return {}
    
    monthly_results = {}
    unique_months = set()

    for record in data:
        try:
            record_date = datetime.strptime(record['date'], "%Y-%m-%d")
            month = record_date.month
            unique_months.add(month)
        except ValueError:
            continue

    for month in sorted(list(unique_months)):
        result = get_sales_by_month(data, month)
        if result['status'] == 'success':
            monthly_results[month] = result
        else:
            monthly_results[month] = result
            
    return monthly_results

@app.route('/totals')
def get_totals():
    """Returns a general status message."""
    return {"status": "ok", "message": "Data retrieval endpoint operational."}

@app.route('/yearly_summary')
def yearly_summary():
    """Returns a general yearly summary placeholder."""
    return {"summary": "Yearly summary data placeholder"}

@app.route('/api/monthly_averages')
def get_monthly_averages():
    """
    New endpoint: Calculates and returns the average sales amount for every month 
    present in the dataset, utilizing caching.
    """
    global CACHED_MONTHLY_AVERAGES
    
    if CACHED_MONTHLY_AVERAGES is None:
        print("Calculating all monthly averages for the first time...")
        CACHED_MONTHLY_AVERAGES = calculate_all_monthly_averages(SALES_DATA)
    
    return jsonify({
        "status": "success",
        "data": CACHED_MONTH_AVERAGES
    })

if __name__ == '__main__':
    # Example usage:
    # To test the endpoint, run the application and access /api/monthly_summary
    print("Application running. Access /api/monthly_summary to see aggregated data.")
    # In a real application, you would run: app.run(debug=True)