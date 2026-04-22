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

def get_sales_data():
    """Processes raw sales data into structured summaries, including monthly averages."""
    sales_summary = {}
    
    # Step 1: Aggregate totals and items per month
    for record in SALES_DATA:
        date_obj = datetime.datetime.strptime(record['date'], '%Y-%m-%d')
        month_key = date_obj.strftime('%Y-%m')
        
        if month_key not in sales_summary:
            sales_summary[month_key] = {'total_sales': 0, 'items': set()}
            
        sales_summary[month_key]['total_sales'] += record['amount']
        sales_summary[month_key]['items'].add(record['item'])
        
    # Step 2: Calculate averages
    monthly_averages = {}
    for month_key, data in sales_summary.items():
        if data['total_sales'] > 0:
            average = data['total_sales'] / len(data['items']) # Average transaction value per unique item sold in that month
            # Alternatively, if we want average transaction value per record:
            # average = data['total_sales'] / len(SALES_DATA) # This is total sales divided by total records, which might be more useful.
            
            # Let's calculate the average transaction value for the month based on the number of unique items sold:
            monthly_averages[month_key] = {
                'total_sales': data['total_sales'],
                'unique_items_count': len(data['items']),
                'average_item_value': data['total_sales'] / len(data['items'])
            }
        else:
            monthly_averages[month_key] = {
                'total_sales': 0,
                'unique_items_count': 0,
                'average_item_value': 0.0
            }
            
    return sales_summary, monthly_averages

SALES_SUMMARY, MONTHLY_AVERAGES = get_sales_data()

@app.route('/summary')
def get_summary():
    """Returns the aggregated sales summary by month."""
    return jsonify(SALES_SUMMARY)

@app.route('/summary/<month>')
def get_monthly_summary(month):
    """Returns the sales summary for a specific month."""
    if month in SALES_SUMMARY:
        return jsonify(SALES_SUMMARY[month])
    return jsonify({"error": "Month not found"}), 404

@app.route('/api/average_spending/<month>')
def get_average_spending(month):
    """Returns the average item value sold for a specific month."""
    if month in MONTHLY_AVERAGES:
        return jsonify(MONTHLY_AVERAGES[month])
    return {"error": "Data not found for this month"}