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
        return {"status": "error", "message": f"No data found for month {month}"}

    return {"month": target_month, "average": sum(monthly_amounts) / len(monthly_amounts)}

def initialize_data():
    """Calculates and stores the aggregated data, populating caches."""
    print("Initializing data...")
    
    monthly_totals = defaultdict(lambda: {'total': 0, 'count': 0})
    
    # 1. Calculate monthly averages
    monthly_totals = {}
    for record in self.data:
        month = record['date'].strftime('%Y-%m')
        amount = record['amount']
        
        if month not in monthly_totals:
            monthly_totals[month] = 0
        monthly_totals[month] += amount

    for month, total in monthly_totals.items():
        average = total / len([r for r in self.data if r['date'].strftime('%Y-%m') == month])
        monthly_totals[month] = average
        
    self.monthly_averages = monthly_totals

    # 2. Calculate top spending categories (Example: grouping by month for simplicity)
    # In a real scenario, this would involve grouping by category. Here we simulate a simple grouping.
    category_spending = {}
    for record in self.data:
        month = record['date'].strftime('%Y-%m')
        category = record['category']
        amount = record['amount']
        
        if month not in category_spending:
            category_spending[month] = {}
        
        if category not in category_spending[month]:
            category_spending[month][category] = 0
            
        category_spending[month][category] += amount

    self.monthly_category_spending = category_spending
    
    print("Data initialization complete.")


# --- Class structure to hold data and methods ---
class DataProcessor:
    def __init__(self, data):
        self.data = data
        self.monthly_averages = {}
        self.monthly_category_spending = {}

    def process(self):
        """Runs the data processing logic."""
        self.initialize_data()

    def initialize_data(self):
        """Performs the actual calculation based on the input data."""
        
        monthly_totals = {}
        category_spending = {}
        
        for record in self.data:
            date = record['date']
            amount = record['amount']
            category = record['category']
            
            month_key = date.strftime('%Y-%m')
            
            # Calculate monthly average
            if month_key not in monthly_totals:
                monthly_totals[month_key] = {'total': 0, 'count': 0}
            monthly_totals[month_key]['total'] += amount
            monthly_totals[month_key]['count'] += 1

            # Calculate category spending
            if month_key not in category_spending:
                category_spending[month_key] = {}
            
            if category not in category_spending[month_key]:
                category_spending[month_key][category] = 0
            category_spending[month_key][category] += amount
            
        # Finalize averages
        self.monthly_averages = {}
        for month, data in monthly_totals.items():
            self.monthly_averages[month] = data['total'] / data['count']
            
        self.monthly_category_spending = category_spending


# --- Example Usage ---

# Sample Data Setup
sample_data = [
    {'date': '2023-01-15', 'amount': 100, 'category': 'Groceries'},
    {'date': '2023-01-20', 'amount': 50, 'category': 'Entertainment'},
    {'date': '2023-02-05', 'amount': 150, 'category': 'Groceries'},
    {'date': '2023-02-10', 'amount': 200, 'category': 'Rent'},
    {'date': '2023-02-25', 'amount': 75, 'category': 'Entertainment'},
]

processor = DataProcessor(sample_data)
processor.process()

print("\n--- Monthly Averages ---")
for month, avg in processor.monthly_averages.items():
    print(f"{month}: ${avg:.2f}")

print("\n--- Monthly Category Spending ---")
for month, categories in processor.monthly_category_spending.items():
    print(f"Month {month}:")
    for category, amount in categories.items():
        print(f"  {category}: ${amount:.2f}")