from flask import Flask, jsonify, request
from datetime import datetime
from collections import defaultdict

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
# Cache for pre-calculated yearly totals
YEARLY_TOTALS_CACHE = {}
# Cache for pre-calculated monthly averages
MONTHLY_AVERAGES_CACHE = {}

def calculate_yearly_totals(data):
    """Calculates the total sales amount for each year from the raw data."""
    yearly_totals = defaultdict(int)
    for record in data:
        try:
            # Extract year from the date string (assuming YYYY-MM-DD format)
            year = int(record['date'][:4])
            amount = record['amount']
            yearly_totals[year] += amount
        except (ValueError, KeyError) as e:
            # Robust error handling for malformed data points
            print(f"Skipping malformed record during yearly calculation: {record}. Error: {e}")
            continue
    return dict(yearly_totals)

def calculate_monthly_averages(data):
    """Calculates the average sales amount for each month from the list."""
    monthly_totals = {}
    monthly_counts = {}
    for record in data:
        month = record['month']
        amount = record['amount']
        monthly_totals[month] = monthly_totals.get(month, 0) + amount
        monthly_counts[month] = monthly_counts.get(month, 0) + 1

    results = {}
    for month, total in monthly_totals.items():
        results[month] = total / monthly_counts[month]
    
    return results

def process_data(data):
    """Processes the raw data into structured lists for efficient lookup."""
    yearly_totals = {}
    monthly_data = []

    for record in data:
        year = int(record['year'])
        month = int(record['month'])
        amount = float(record['amount'])
        
        # Yearly totals
        yearly_totals[year] = yearly_totals.get(year, 0) + amount
        
        # Monthly data for average calculation
        monthly_data.append({'year': year, 'month': month, 'amount': amount})

    # Calculate final yearly totals
    final_yearly_totals = {year: yearly_totals[year] for year in yearly_totals}
    
    # Calculate monthly averages
    monthly_averages = {}
    monthly_sums = {}
    monthly_counts = {}

    for item in monthly_data:
        key = (item['year'], item['month'])
        amount = item['amount']
        
        monthly_sums[key] = monthly_sums.get(key, 0) + amount
        monthly_counts[key] = monthly_counts.get(key, 0) + 1

    for (year, month), total in monthly_sums.items():
        monthly_averages[(year, month)] = total / monthly_counts[(year, month)]

    return final_yearly_totals, monthly_averages


# --- Initialization ---
# Simulate raw data input structure based on the required calculations
raw_data = [
    {'year': 2023, 'month': 1, 'amount': 100.0},
    {'year': 2023, 'month': 1, 'amount': 150.0},
    {'year': 2023, 'month': 2, 'amount': 200.0},
    {'year': 2023, 'month': 3, 'amount': 50.0},
    {'year': 2024, 'month': 1, 'amount': 300.0},
    {'year': 2024, 'month': 1, 'amount': 100.0},
    {'year': 2024, 'month': 2, 'amount': 200.0},
]

# Process the data once upon loading
yearly_totals, monthly_averages = process_data(raw_data)

# --- Example Usage ---
print("--- Yearly Totals ---")
print(yearly_totals)
print("\n--- Monthly Averages ---")
print(monthly_averages)