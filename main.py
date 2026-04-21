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
# Cache for pre-calculated yearly totals (will be calculated on request for dynamic behavior)
# YEARLY_TOTALS_CACHE = {}
# Cache for pre-calculated monthly averages
# MONTHLY_AVERAGES_CACHE = {}

def process_data(data):
    """Processes the raw data into structured lists for efficient lookup."""
    yearly_totals = defaultdict(float)
    monthly_sums = defaultdict(float)
    monthly_counts = defaultdict(int)

    for record in data:
        try:
            year = int(record['year'])
            month = int(record['month'])
            amount = float(record['amount'])
            
            # Yearly totals
            yearly_totals[year] += amount
            
            # Monthly data for average calculation
            key = (year, month)
            monthly_sums[key] += amount
            monthly_counts[key] += 1
        except (ValueError, KeyError, TypeError) as e:
            # Robust error handling for malformed data points
            print(f"Skipping malformed record during processing: {record}. Error: {e}")
            continue

    # Calculate final monthly averages
    monthly_averages = {}
    for (year, month), total in monthly_sums.items():
        monthly_averages[(year, month)] = total / monthly_counts[(year, month)]

    # Calculate final yearly totals
    final_yearly_totals = dict(yearly_totals)
    
    return final_yearly_totals, monthly_averages

# Pre-process data once when the application starts (simulating loading from DB)
try:
    yearly_totals_cache, monthly_averages_cache = process_data(SALES_DATA)
except Exception as e:
    print(f"Fatal error during initial data processing: {e}")
    yearly_totals_cache = {}
    monthly_averages_cache = {}


# --- API Endpoints ---

@app.route('/api/yearly_totals', methods=['GET'])
def get_yearly_totals():
    """Returns the total sales aggregated by year."""
    return {"status": "success", "data": dict(sorted(items(), reverse=True))}

@app.route('/api/monthly_averages', methods=['GET'])
def get_monthly_averages():
    """Returns the average sales for each month."""
    return {"status": "success", "data": dict(sorted(items(), reverse=True))}

if __name__ == '__main__':
    # Example usage (for testing purposes)
    # In a real application, you would use a proper WSGI server.
    print("Server running. Access endpoints via /api/monthly_averages or /api/monthly_averages")
    # Note: To run this, you would need to import Flask and run the app.
    # For this self-contained example, we just define the routes.
    pass