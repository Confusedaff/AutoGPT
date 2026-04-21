from flask import Flask, jsonify, request
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

# --- Database Simulation (Simulating SQLite persistence via in-memory structure) ---
SALES_DATA = [
    {"date": "2023-01-15", "amount": 100},
    {"date": "2023-01-20", "amount": 150},
    {"date": "2023-02-10", "amount": 200},
    {"date": "2023-02-25", "amount": 120},
    {"date": "2024-03-01", "amount": 50},
    {"date": "2024-04-10", "amount": 100},
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
    """Calculates the average sales amount for each month from the raw data."""
    monthly_totals = defaultdict(float)
    counts = defaultdict(int)

    for record in data:
        try:
            # Extract month from the date string (YYYY-MM-DD)
            month_str = record['date'][5:7]
            month = int(month_str)
            amount = record['amount']
            
            monthly_totals[month] += amount
            counts[month] += 1
        except (ValueError, KeyError) as e:
            # Skip records that don't conform to the expected structure
            print(f"Skipping record during monthly calculation: {record}. Error: {e}")
            continue

    # Calculate the average and populate the cache
    for month, total in monthly_totals.items():
        count = counts[month]
        if count > 0:
            average = total / count
            MONTHLY_AVERAGES_CACHE[month] = round(average, 2)

def calculate_all_data():
    """Calculates all necessary aggregates and populates the cache."""
    print("Calculating yearly totals...")
    global YEARLY_TOTALS_CACHE
    YEARLY_TOTALS_CACHE = calculate_yearly_totals(SALES_DATA)
    
    # Note: Assuming SALES_DATA is defined or passed. If not, we use a placeholder structure.
    # For this example, we'll assume the data is available globally or passed contextually.
    # Since the original code didn't define SALES_DATA, we must define it for execution context.
    
    # Re-running the calculation based on the provided context structure:
    # If we assume the input data is implicitly available, we proceed.
    pass # Placeholder for actual execution flow

# --- Setup Mock Data for runnable example ---
SALES_DATA = [
    {"date": "2023-01-15", "amount": 100},
    {"date": "2023-01-20", "amount": 150},
    {"date": "2023-02-10", "amount": 200},
    {"date": "2023-03-05", "amount": 120},
    {"date": "2023-04-25", "amount": 300},
]
# --- End Mock Data Setup ---


app = Flask(__name__)

@app.route('/api/monthly_average/<int:year>')
def get_monthly_average(year):
    """
    API endpoint to retrieve the average transaction amount for a given year.
    """
    # In a real application, data would be fetched from a database.
    # Here, we simulate filtering the mock data.
    
    monthly_totals = {}
    monthly_counts = {}
    
    for item in SALES_DATA:
        try:
            month = int(item['date'][:7]) # Extract YYYY-MM
            year_key = str(item['date'][:4])
            month_key = item['date'][5:7]
            amount = item['amount']
            
            if year_key not in monthly_totals:
                monthly_totals[year_key] = 0
                monthly_counts[year_key] = 0
            
            monthly_totals[year_key] += amount
            monthly_counts[year_key] += 1
            
        except (ValueError, KeyError) as e:
            # Handle malformed data if necessary
            continue

    results = {}
    for year, total in monthly_totals.items():
        count = monthly_counts[year]
        results[year] = round(total / count, 2)
        
    return {"year": year, "average_amount": results.get(str(year), 0.0)}

if __name__ == '__main__':
    # In a real Flask app, you would run this server.
    # For this demonstration, we just show the structure.
    print("Server structure defined. To run, import Flask and execute.")
    # app.run(debug=True)