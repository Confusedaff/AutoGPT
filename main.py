from flask import Flask, jsonify, request
from datetime import datetime
from collections import defaultdict
import operator
import time

app = Flask(__name__)

# --- Database Simulation (Simulating SQLite persistence via in-memory structure) ---
# Improved data structure to include categories for meaningful analysis
SALES_DATA = [
    {"date": "2023-01-15", "amount": 150, "category": "Groceries"},
    {"date": "2023-01-16", "amount": 100, "category": "Entertainment"},
    {"date": "2023-01-17", "amount": 200, "category": "Groceries"},
    {"date": "2023-01-18", "amount": 150, "category": "Food"},
    {"date": "2023-02-05", "amount": 300, "category": "Groceries"},
    {"date": "2023-02-10", "amount": 50, "category": "Entertainment"},
    {"date": "2023-02-20", "amount": 100, "category": "Food"},
]

# --- Caching Mechanism ---
ANALYSIS_CACHE = {}

def get_monthly_spending(data):
    """Calculates total spending per month."""
    monthly_totals = defaultdict(float)
    for record in data:
        try:
            date = record['date']
            amount = record['amount']
            month_year = date[:7]  # YYYY-MM format
            monthly_totals[month_year] += amount
        except KeyError:
            # Skip records missing required fields
            continue
    return dict(monthly_totals)

def get_top_spending_by_month_and_category(data):
    """Calculates total spending per month, grouped by category."""
    monthly_spending = get_monthly_spending(data)
    
    if not monthly_spending:
        return {}

    category_spending = defaultdict(lambda: defaultdict(float))
    
    for record in data:
        try:
            date = record['date']
            amount = record['amount']
            category = record.get('category')
            month_year = date[:7]
            
            if month_year in monthly_spending and category:
                category_spending[month_year][category] += amount
        except KeyError:
            continue
            
    return dict(category_spending)


def analyze_data(data):
    """Analyzes the provided sales data and caches the result."""
    cache_key = "monthly_category_analysis"
    if cache_key in ANALYSIS_CACHE:
        print(f"Cache hit for {cache_key}")
        return ANALYSIS_CACHE[cache_key]

    print("Performing expensive data analysis...")
    monthly_category_results = get_top_spending_by_month_and_category(data)
    
    ANALYSIS_CACHE[cache_key] = monthly_category_results
    return monthly_category_results


# --- API Endpoints Simulation ---

def handle_request(method, path):
    if path == "/analyze":
        if method == "GET":
            data = {}
            try:
                data = {"total_records": len(SALES_DATA), "summary": get_summary(SALES_DATA)}
            except Exception as e:
                return {"error": str(e)}, 500
            return data, 200
        return {"error": "Method not supported"}, 405
    return {"error": "Not Found"}, 404

def get_summary(data):
    """Helper function to generate a simple summary."""
    if not data:
        return "No data available."
    
    summary = {}
    total_sales = 0
    
    for item in data:
        total_sales += item.get('amount', 0)
        
    summary['total_sales'] = total_sales
    summary['record_count'] = len(data)
    
    # Group by month for a simple view
    monthly_sales = {}
    for item in data:
        month = item['date'][:7]  # YYYY-MM
        if month not in monthly_sales:
            monthly_sales[month] = {'sales': 0, 'items': 0}
        monthly_sales[month]['sales'] += item.get('amount', 0)
        monthly_sales[month]['items'] += 1
        
    summary['monthly_breakdown'] = monthly_sales
    return summary

# --- Mock Data Setup ---
SALES_DATA = [
    {'date': '2023-10-01', 'amount': 150.50, 'item': 'Laptop'},
    {'date': '2023-10-05', 'amount': 45.00, 'item': 'Mouse'},
    {'date': '2023-11-10', 'amount': 300.00, 'item': 'Monitor'},
    {'date': '2023-11-15', 'amount': 120.00, 'item': 'Keyboard'},
    {'date': '2023-10-20', 'amount': 50.00, 'item': 'Webcam'},
]

# Example usage simulation (for testing the logic)
# result, status = get_summary(SALES_DATA)
# print(f"Summary: {result}")
# print(f"Data: {SALES_DATA}")
# print(f"Cached result: {get_summary(SALES_DATA)}")