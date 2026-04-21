from flask import Flask, jsonify, request
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

# --- Database Simulation (Simulating SQLite persistence via in-memory structure) ---
# In a real application, this would be replaced by SQLite interaction.
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
            print(f"Skipping malformed record: {record}. Error: {e}")
            continue
    return dict(yearly_totals)

# Initialize the cache upon application startup
YEARLY_TOTALS_CACHE = calculate_yearly_totals(SALES_DATA)


# --- API Endpoints ---

@app.route('/api/yearly_summary/<int:year>', methods=['GET'])
def get_yearly_summary(year):
    """
    Retrieves the total sales amount for a specific year.
    Implements robust input validation and safe data retrieval.
    """
    if year < 1900:
        return jsonify({"error": "Year must be a valid historical year."}), 400

    total = YEARLY_TOTALS_CACHE.get(year)

    if total is not None:
        return jsonify({
            "year": year,
            "total_amount": total,
            "status": "success"
        }), 200
    else:
        # Specific error handling for missing data
        return jsonify({
            "error": f"No sales data found for the year {year}.",
            "status": "not_found"
        }), 404

@app.route('/api/average_spending/<int:month>', methods=['GET'])
def get_average_spending(month):
    """
    Calculates the average sales amount for a specific month (1-12).
    This endpoint dynamically processes the raw sales data.
    """
    if not 1 <= month <= 12:
        return jsonify({"error": "Month must be an integer between 1 and 12."}), 400

    monthly_totals = defaultdict(float)
    count = 0

    for record in SALES_DATA:
        try:
            # Extract month from the date string (YYYY-MM-DD)
            month_str = record['date'][5:7]
            month = int(month_str)
            amount = record['amount']
            
            monthly_totals[month] += amount
            count += 1
        except (ValueError, KeyError) as e:
            # Skip records that don't conform to the expected structure
            print(f"Skipping record during average calculation: {record}. Error: {e}")
            continue

    if count == 0:
        return jsonify({
            "error": f"No valid sales records found to calculate average for month {month}.",
            "status": "not_found"
        }), 404

    # Calculate the average
    average = sum(monthly_totals.values()) / count

    return jsonify({
        "month": month,
        "average_amount": round(average, 2),
        "record_count": count,
        "status": "success"
    }), 200

# --- Application Run ---

if __name__ == '__main__':
    # In a production environment, use a proper WSGI server.
    # Running on default host/port for demonstration.
    app.run(debug=True)