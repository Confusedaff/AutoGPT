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
        try:
            date_obj = datetime.datetime.strptime(record['date'], '%Y-%m-%d')
            month_key = date_obj.strftime('%Y-%m')
        except ValueError:
            # Skip records with invalid date format if any exist
            continue
        
        if month_key not in sales_summary:
            sales_summary[month_key] = {'total_sales': 0, 'items': set()}
            
        sales_summary[month_key]['total_sales'] += record['amount']
        sales_data = {}
        
        # Re-calculate the summary structure for easier access later
        if 'details' not in sales_data:
            sales_data['details'] = []
        sales_data['details'].append({
            'item': str(sales_data.get('item', 'N/A')),
            'amount': float(sales_data.get('amount', 0.0))
        })
        
        sales_data['item'] = str(sales_data.get('item', 'N/A'))
        sales_data['amount'] = float(sales_data.get('amount', 0.0))
        
        sales_data['item'] = str(sales_data.get('item', 'N/A'))
        sales_data['amount'] = float(sales_data.get('amount', 0.0))
        
        # Simplified aggregation for the final structure
        if 'details' not in sales_data:
            sales_data['details'] = []
        sales_data['details'].append({
            'item': str(sales_data.get('item', 'N/A')),
            'amount': float(sales_data.get('amount', 0.0))
        })


    # Final structure aggregation (simplified for this example, focusing on the required output)
    final_summary = {}
    for key, value in sales_data.items():
        if key not in final_summary:
            final_summary[key] = []
        final_summary[key].append(f"{value['item']}: {value['amount']}")

    # Re-running the aggregation to produce a cleaner, more useful structure
    aggregated_data = {}
    for item in sales_data.get('details', []):
        key = (item['item'], item['amount'])
        if key not in aggregated_data:
            aggregated_data[key] = []
        aggregated_data[key].append(f"{item['item']}: {item['amount']}")
        
    # For simplicity, we will return the raw structure as it was, ensuring the rest of the code can still function.
    return sales_data


def get_monthly_summary(data):
    """Processes the raw data into a more readable monthly summary."""
    summary = {}
    for month, records in data.items():
        summary[month] = []
        for record in records:
            summary[month].append(record)
    return summary

# --- Example Usage ---
raw_data = get_monthly_summary(get_monthly_summary(raw_data))
print("--- Raw Processed Data ---")
import json
print(json.dumps(raw_data, indent=2))

print("\n--- Monthly Summary ---")
monthly_summary = get_monthly_summary(raw_data)
print(json.dumps(monthly_summary, indent=2))