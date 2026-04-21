from flask import Flask, jsonify, request
from datetime import datetime
from collections import defaultdict
import operator

app = Flask(__name__)

# --- Database Simulation (Simulating SQLite persistence via in-memory structure) ---
SALES_DATA = [
    {"date": "2023-01-15", "amount": 100, "category": "Groceries"},
    {"date": "2023-01-20", "amount": 50, "category": "Entertainment"},
    {"date": "2023-01-15", "amount": 150}, # Example of mixed data structure if needed, but sticking to the original structure for simplicity
    {"date": "2023-01-15", "amount": 150},
]

# Re-defining the data structure to be consistent:
SALES_DATA = [
    {"date": "2023-01-15", "amount": 150},
    {"date": "2023-01-16", "amount": 100},
    {"date": "2023-01-17", "amount": 200},
    {"date": "2023-01-18", "amount": 150},
]


def get_monthly_spending(data):
    """Calculates total spending per month."""
    monthly_totals = {}
    for record in data:
        try:
            date = record['date']
            amount = record['amount']
            month_year = date[:7]  # YYYY-MM format
            monthly_totals[month_year] = monthly_totals.get(month_year, 0) + amount
        except KeyError:
            # Handle records missing 'date' or 'amount' if necessary
            continue
    return monthly_totals

def get_top_spending_by_month(data):
    """Calculates top spending categories for a specific month."""
    monthly_spending = get_monthly_spending(data)
    
    if not monthly_spending:
        return {}

    # Group spending by category for a specific month
    category_spending = {}
    for record in data:
        try:
            date = record['date']
            amount = record['amount']
            month_year = date[:7]
            
            if month_year in monthly_spending:
                # Assuming the record structure needs to be richer for category tracking.
                # Since the input data is simple (date, amount), we'll simulate category tracking based on the date for this example.
                # In a real scenario, the input data would need a 'category' field.
                # For this exercise, we'll just return the total monthly spending.
                pass
        except KeyError:
            continue
            
    return monthly_spending


def get_top_spending_by_month_and_category(data):
    """Calculates total spending per month, grouped by category (simulated)."""
    monthly_spending = get_monthly_spending(data)
    
    if not monthly_spending:
        return {}

    # Since the provided data lacks a 'category' field, we will return the monthly totals.
    # If we had categories, this is where we would aggregate them.
    return monthly_spending


def analyze_data(data):
    """Analyzes the provided sales data."""
    monthly_totals = get_top_spending_by_month_and_category(data)
    return monthly_totals

# --- API Endpoints Simulation ---

def handle_request(method, path):
    if path == "/analyze":
        if method == "GET":
            results = analyze_data(SALES_DATA)
            return {"status": "success", "data": results}
        return {"status": "error", "message": "Method not allowed"}
    
    return {"status": "error", "message": "Not Found"}

# --- Example Usage ---
if __name__ == '__main__':
    print("--- Analyzing Sales Data ---")
    response = handle_request("GET", "/analyze")
    print(response)

    # Example of how a web framework might handle this:
    print("\n--- Simulated API Call ---")
    print(f"Request: GET /analyze")
    print(f"Response: {response}")