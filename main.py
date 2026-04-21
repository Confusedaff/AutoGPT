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

# Cache storage for pre-calculated results
CACHED_MONTHLY_AVERAGES = {}
CACHED_TOP_EXPENSES = {}

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
        return {"status": "error", "message": f"No data found for month {month}"} if 'month' in locals() else {"error": True}

    return {"month": month, "average": sum(values) / len(values)}

# Pre-calculate the data on startup
def initialize_data():
    """Calculates and stores the aggregated data."""
    print("Initializing data...")
    results = {}
    
    # Group data by month
    monthly_totals = {}
    for record in results:
        month = int(record['month'])
        if month not in monthly_totals:
            monthly_totals[month] = {'total': 0, 'count': 0}
        monthly_totals[month]['total'] += record['amount']
        monthly_totals[month]['count'] += 1

    # Calculate averages
    for month, data in monthly_totals.items():
        results[month] = {
            'average': data['total'] / data['count']
        }
        
    print("Data initialization complete.")
    return results

# Run initialization once when the module loads
if not hasattr(initialize_data, 'initialized'):
    initialize_data()
    initialize_data.initialized = True


@app.route('/data')
def get_monthly_data():
    """Endpoint to retrieve pre-calculated monthly averages."""
    # In a real Flask app, you would access the global results dictionary here.
    # For this standalone example, we simulate access.
    
    # Since we cannot easily access the module-level state in this isolated block, 
    # we'll assume the data is available or re-calculate for demonstration purposes.
    
    # Re-calculating for demonstration purposes if the global state isn't easily accessible:
    
    monthly_results = {}
    monthly_totals = {}
    
    for record in results:
        month = int(record['month'])
        if month not in monthly_totals:
            monthly_totals[month] = {'total': 0, 'count': 0}
        monthly_totals[month]['total'] += record['amount']
        monthly_totals[month]['count'] += 1

    for month, data in monthly_totals.items():
        monthly_results[month] = {
            'average': data['total'] / data['count']
        }
        
    return jsonify(monthly_results)

# --- Mock Flask setup for execution context ---
from flask import Flask, jsonify
app = Flask(__name__)

if __name__ == '__main__':
    # In a real scenario, this would run the server.
    # For this execution, we just ensure the functions run.
    pass