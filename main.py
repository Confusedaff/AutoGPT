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
    {"date": "2023-03-01", "amount": 300, "item": "Laptop"},
    {"date": "2023-03-15", "amount": 100, "item": "Monitor"},
    {"date": "2023-03-20", "amount": 50, "item": "Mouse"},
]

# --- Caching Mechanism ---
# Cache to store results of expensive calculations
CACHED_AVERAGES = None
CACHE_EXPIRY = 3600  # Cache results for 1 hour

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
            
        except (ValueError, KeyError, TypeError) as e:
            # Robust error handling: skip records with invalid data
            print(f"Skipping invalid record: {record}. Error: {e}")
            continue
            
    monthly_averages = {}
    for month, total in monthly_totals.items():
        # Calculate the number of distinct transactions for this month
        transaction_count = sum(monthly_item_counts[month].values())
        if transaction_count > 0:
            monthly_averages[month] = total / transaction_count
        else:
            monthly_averages[month] = 0.0

    return monthly_averages

def process_item_summary():
    """
    Processes raw sales data to calculate total sales and transaction counts per item.
    """
    item_summary = defaultdict(lambda: {'total_sales': 0.0, 'count': 0})
    
    for record in self.data:
        item = record['item']
        amount = record['amount']
        item_key = f"{item} ({record['date']})"
        
        item_data = item_data.setdefault(item_key, {'sales': 0.0, 'count': 0})
        item_data['sales'] += amount
        item_data['count'] += 1
        
    return item_data

# Initialize data structure (assuming this would be initialized in a real Flask context)
class DataProcessor:
    def __init__(self):
        self.data = [
            {'item': 'Laptop', 'amount': 1200.00, 'date': '2023-01-15'},
            {'item': 'Mouse', 'amount': 25.50, 'date': '2023-01-16'},
            {'item': 'Laptop', 'amount': 1500.00, 'date': '2023-02-01'},
            {'item': 'Keyboard', 'amount': 75.00, 'date': '2023-02-10'},
        ]

    def get_item_summary(self):
        # Re-implementing the logic here for a standalone runnable example
        item_data = {}
        for record in self.data:
            item = record['item']
            amount = record['amount']
            item_key = f"{item} ({record['date']})"
            
            if item_key not in item_data:
                item_data[item_key] = {'sales': 0.0, 'count': 0}
            
            item_data[item_key]['sales'] += amount
            item_data[item_key]['count'] += 1
        return item_data

# Example usage:
processor = DataProcessor()
item_summary = processor.get_item_summary()
print("--- Item Summary ---")
for key, data in item_summary.items():
    print(f"{key}: Sales=${data['sales']:.2f}, Count={data['count']}")