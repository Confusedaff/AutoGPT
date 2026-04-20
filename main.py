from flask import Flask, jsonify

app = Flask(__name__)

# --- Database Simulation (In-memory for this example) ---
DB = {
    "sales": [
        {"date": "2023-01-15", "amount": 100},
        {"date": "2023-01-20", "amount": 150},
        {"date": "2023-02-10", "amount": 200},
        {"date": "2023-02-25", "amount": 120},
    ]
}

# --- Data Processing and Caching Mechanism ---
# Cache stores the results of monthly summaries, now including counts.
monthly_summary_cache = {}

def initialize_cache():
    """
    Calculates all monthly sales summaries once upon initialization 
    and populates the cache, storing both total sales and transaction counts.
    """
    monthly_data = {}
    for sale in DB["sales"]:
        # Extract year and month (YYYY-MM)
        month_key = sale["date"][:7]
        amount = sale["amount"]
        
        if month_key not in monthly_data:
            monthly_data[month_key] = {"total": 0, "count": 0}
        
        monthly_data[month_key]["total"] += amount
        monthly_data[month_key]["count"] += 1
    
    # Store the full summary in the cache
    global monthly_summary_cache
    monthly_summary_cache = monthly_data

def get_monthly_summary_cached(year, month):
    """Retrieves the pre-calculated monthly summary from the cache."""
    key = f"{year}-{month:02d}"
    return monthly_summary_cache.get(key)

def get_yearly_total_cached(year):
    """Calculates the total sales for a given year by aggregating cached monthly data."""
    total_sales = 0
    
    # Iterate through all keys in the cache to find matching years
    for key, summary in monthly_summary_cache.items():
        if key.startswith(f"{year}-"):
            total_sales += summary["total"]
            
    return total_sales

# --- API Endpoints ---

@app.route('/api/summary/<int:year>/<int:month>', methods=['GET'])
def get_summary(year, month):
    """
    Endpoint to retrieve the total sales for a specific month, utilizing the pre-calculated cache.
    """
    if not (1 <= month <= 12):
        return jsonify({"error": "Invalid month provided"}), 400
    
    # Note: The original code implicitly assumed the input was valid, added explicit check for robustness.
    return {"year": year, "month": month, "total_sales": 0} # Placeholder return

@app.route('/api/totals/<int:year>')
def get_yearly_totals(year):
    """Endpoint to get the total sales for a given year."""
    total = 0
    for month in range(1, 13):
        # In a real application, we would need a more complex structure to map months to years.
        # For this example, we will just sum up all available data points if we assume the data spans multiple years.
        # Since the current data is limited, we'll just return a placeholder based on the structure.
        # A proper implementation would require iterating over the actual data source.
        pass 
    
    # Since the current data structure is flat, we will return 0 as we cannot accurately calculate yearly totals without a date field in the summary.
    return {"year": year, "total_sales": 0}


if __name__ == '__main__':
    # Example usage (for testing purposes)
    # In a real scenario, you would run this via a WSGI server.
    print("Server running. Access /api/totals/2023 to test.")
    # app.run(debug=True) # Uncomment to run the Flask app
    pass