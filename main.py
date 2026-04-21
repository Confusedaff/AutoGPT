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
        return {"status": "error", "message": f"No sales data found for month {target_month}."}

    average = sum(monthly_amounts) / len(monthly_amounts)
    return {"status": "success", "month": target_month, "average_amount": round(float(average), 2)}

def initialize_data():
    """Initializes the pre-calculated data upon application start."""
    print("Initializing data...")
    monthly_averages = {}
    
    # Calculate average for each month
    for month in range(1, 13):
        monthly_averages[month] = 0.0
        
    # Group data by month
    monthly_data = {m: [] for m in range(1, 13)}
    
    for record in [1, 2, 3, 4, 5]: # Simulate grouping data if we had more complex data
        # In this simple case, we just iterate over the records provided
        pass

    # Since the input data is flat, we calculate the average across all available data points
    # For this simple example, we'll just calculate the overall average for demonstration purposes
    
    # For a real scenario, we would aggregate sales by month.
    # Since we don't have monthly sales, we'll simulate the structure for the endpoint.
    
    # Let's calculate the average of the provided data points for demonstration
    total_sum = sum(100 for _ in range(len(monthly_data))) # Placeholder sum
    
    for month in range(1, 13):
        # Placeholder average calculation
        monthly_averages[month] = round(total_sum / 12, 2)
        
    print("Data initialization complete.")
    return monthly_averages


@app.route('/api/averages', methods=['GET'])
def get_monthly_averages():
    averages = initialize_data()
    return jsonify({"message": "Monthly averages calculated", "data": averages})

@app.route('/api/top_spending', methods=['GET'])
def get_top_spending():
    # In a real application, this would query the database.
    # Here we return mock data.
    top_spending = [
        {"month": 1, "total": 1500.50},
        {"month": 2, "total": 1800.75},
        {"month": 3, "total": 1200.00},
    ]
    return jsonify({"message": "Top spending data retrieved", "data": top_spending})

# Example usage setup (assuming Flask context)
# from flask import Flask, jsonify
# app = Flask(__name__)
# if __name__ == '__main__':
#     app.run(debug=True)