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
]

def process_sales_data():
    """
    Processes raw sales data into a structured summary, calculating monthly totals and averages.
    """
    monthly_totals = defaultdict(float)
    monthly_item_counts = defaultdict(lambda: defaultdict(int))
    
    for record in SALES_DATA:
        try:
            date_obj = datetime.strptime(record['date'], '%Y-%m-%d')
            month_key = date_obj.strftime('%Y-%m')
            amount = float(record['amount'])
            item = str(record['item'])
            
            monthly_totals[month_key] += amount
            monthly_item_counts[month_key][item] += 1
            
        except (ValueError, KeyError) as e:
            # Log or handle records with invalid data silently
            continue
            
    monthly_averages = {}
    for month, total in monthly_totals.items():
        # Calculate the number of distinct transactions for this month
        # Since SALES_DATA is flat, we count the number of entries per month for simplicity of average calculation
        transaction_count = sum(monthly_item_counts[month].values())
        if transaction_count > 0:
            monthly_averages[month] = total / transaction_count
        else:
            monthly_averages[month] = 0.0

    return monthly_averages


@app.route('/api/monthly_averages', methods=['GET'])
def get_monthly_averages():
    """
    New endpoint to retrieve the average spending for each month.
    """
    monthly_averages = process_sales_data()
    return jsonify({
        "message": "Monthly average sales calculated successfully",
        "averages": monthly_averages
    })

if __name__ == '__main__':
    # In a real application, you would run this with a proper WSGI server.
    # For demonstration, we just show how the endpoint would be accessed.
    print("Run the application to test the endpoint (e.g., using Flask/Django setup).")
    # To run this standalone for testing purposes, you would typically use a framework.