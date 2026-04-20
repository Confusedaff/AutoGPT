from flask import Flask, jsonify

app = Flask(__name__)

# --- Database Simulation (In-memory for this example) ---
# In a real application, this would interact with a database.
DB = {
    "sales": [
        {"date": "2023-01-15", "amount": 100},
        {"date": "2023-01-20", "amount": 150},
        {"date": "2023-02-10", "amount": 200},
        {"date": "2023-02-25", "amount": 120},
    ]
}

# --- Data Processing Functions ---

def get_monthly_summary():
    """Calculates the total sales for each month."""
    monthly_totals = {}
    for sale in DB["sales"]:
        # Extract year and month (YYYY-MM)
        month_key = sale["date"][:7]
        amount = sale["amount"]
        monthly_totals[month_key] = monthly_totals.get(month_key, 0) + amount
    return monthly_totals

# --- Caching Mechanism ---
# Cache stores the results of monthly summaries to avoid recalculation.
monthly_summary_cache = {}

def get_monthly_summary_cached(year, month):
    """Retrieves the pre-calculated monthly summary from the cache."""
    key = f"{year}-{month:02d}"
    if key in monthly_summary_cache:
        return monthly_summary_cache[key]
    return None

def calculate_and_cache_monthly_summary(year, month):
    """Calculates the monthly summary and stores it in the cache."""
    key = f"{year}-{month:02d}"
    if key not in monthly_summary_cache:
        monthly_summary_cache[key] = get_monthly_summary()
    return monthly_summary_cache[key]

# --- API Endpoints ---

@app.route('/api/summary/<int:year>/<int:month>', methods=['GET'])
def get_summary(year, month):
    """
    Endpoint to retrieve the total sales for a specific month, utilizing caching.
    """
    if not (1 <= month <= 12):
        return jsonify({"error": "Invalid month provided"}), 400

    # Use the cached function to retrieve the data
    summary = get_monthly_summary_cached(year, month)

    if summary is None:
        # If not found in cache, calculate it (this simulates the heavy lifting)
        summary = calculate_and_cache_monthly_summary(year, month)

    if summary:
        return jsonify({
            "year": year,
            "month": month,
            "total_sales": summary
        })
    else:
        return jsonify({"error": "No sales data found for this period"}), 404

@app.route('/api/status', methods=['GET'])
def get_status():
    """Endpoint to check the status of the cache."""
    return jsonify({
        "status": "OK",
        "cache_size": len(monthly_summary_cache)
    })

if __name__ == '__main__':
    # Example usage:
    # Access: http://127.0.0.1:5000/api/summary/2023/1
    app.run(debug=True)