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

def get_sales_by_month(data, month):
    """Filters sales data for a specific month and calculates the average."""
    if not data:
        return None

    target_month = int(month)
    
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


# --- API Endpoints ---

@app.route('/api/yearly_totals', methods=['GET'])
def get_yearly_totals():
    """Returns the total sales aggregated by year."""
    yearly_totals = defaultdict(float)
    for record in SALES_DATA:
        try:
            year = int(record['date'][:4])
            amount = float(record['amount'])
            yearly_totals[year] += amount
        except (ValueError, KeyError, TypeError):
            continue
            
    # Return sorted results
    return jsonify({
        "status": "success", 
        "data": dict(sorted(yearly_totals.items(), reverse=True))
    })

@app.route('/api/monthly_averages', methods=['GET'])
def get_monthly_averages():
    """Calculates the average transaction amount for each month."""
    monthly_totals = {}
    monthly_counts = {}

    for record in SALES_DATA:
        try:
            date = record['date']
            amount = record['amount']
            month = date.month
            
            if month not in monthly_totals:
                monthly_totals[month] = 0
                monthly_counts[month] = 0
            
            monthly_totals[month] += amount
            monthly_counts[month] += 1
        except (TypeError, KeyError):
            # Skip malformed records
            continue

    averages = {}
    for month, total in monthly_totals.items():
        count = monthly_counts[month]
        averages[month] = round(total / count, 2)

    return {"monthly_averages": averages}

# Example of a new endpoint utilizing the data
@app.route('/api/average_by_month/<int:month>', methods=['GET'])
def get_average_by_month(month):
    """Returns the average transaction amount for a specific month."""
    results = get_monthly_averages()
    
    if month in results.get("monthly_averages", {}):
        return {"month": month, "average_amount": results["monthly_averages"][month]}
    else:
        return {"error": f"No data found for month: {month}"}, 404

# Note: In a real Flask application, you would need to import Flask and define the data source.
# For this self-contained example, we assume 'SALES_DATA' is accessible or defined globally.
# Since the original prompt implies a runnable example, I'll structure it as a runnable script context.