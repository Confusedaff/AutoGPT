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

# --- API Endpoints ---

@app.route('/api/summary/<int:year>/<int:month>', methods=['GET'])
def get_summary(year, month):
    """
    Endpoint to retrieve the total sales for a specific month, utilizing the pre-calculated cache.
    """
    if not (1 <= month <= 12):
        return jsonify({"error": "Invalid month provided"}), 400

    # Direct lookup from the pre-calculated cache (O(1))
    summary = get_monthly_summary_cached(year, month)

    if summary is None:
        return jsonify({"error": "No sales data found for this period"}), 404
    
    return jsonify({
        "year": year,
        "month": month,
        "total_sales": summary["total"]
    })

@app.route('/api/average_spending/<int:year>/<int:month>', methods=['GET'])
def get_average_spending(year, month):
    """
    NEW ENDPOINT: Calculates the average sales for a specific month using cached data.
    """
    if not (1 <= month <= 12):
        return jsonify({"error": "Invalid month provided"}), 400

    key = f"{year}-{month:02d}"
    summary = get_monthly_summary_cached(year, month)

    if summary is None:
        return jsonify({"error": "No sales data found for this period"}), 404
    
    total = summary["total"]
    count = summary["count"]
    
    average = total / count
    
    return jsonify({
        "year": year,
        "month": month,
        "average_spending": round(average, 2)
    })


@app.route('/api/status', methods=['GET'])
def get_status():
    """Endpoint to check the status of the cache."""
    return jsonify({
        "status": "OK",
        "cache_size": len(monthly_summary_cache)
    })

if __name__ == '__main__':
    app.run(debug=True)