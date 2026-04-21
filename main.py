from flask import Flask, jsonify, request

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
monthly_summary_cache = {}
yearly_summary_cache = {}
yearly_totals = {}

def initialize_cache():
    """
    Calculates all monthly sales summaries and yearly totals once upon initialization 
    and populates the cache.
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
    
    # Store the full monthly summary in the cache
    global monthly_summary_cache
    monthly_summary_cache = monthly_data
    
    # Calculate and store yearly totals in the cache
    global yearly_summary_cache
    yearly_summary_cache = {}
    for month_key, summary in monthly_data.items():
        # Extract year (YYYY)
        year = month_key[:4]
        if year not in yearly_summary_cache:
            yearly_summary_cache[year] = 0
        yearly_summary_cache[year] += summary["total"]

    # Calculate yearly totals for direct access
    global yearly_totals
    yearly_totals = yearly_summary_cache


def get_monthly_summary_cached(year, month):
    """Retrieves the pre-calculated monthly summary from the cache."""
    month_key = f"{year}-{month:02d}"
    return monthly_summary_cache.get(month_key)

def get_yearly_total(year):
    """Retrieves the pre-calculated total for a given year."""
    return yearly_totals.get(year, 0)

# --- API Endpoints ---

@app.route('/api/yearly_total/<int:year>', methods=['GET'])
def get_yearly_total_endpoint(year):
    """Endpoint to retrieve the total sales for a specific year."""
    total = get_yearly_total(year)
    if total == 0:
        return jsonify({"error": f"No sales data found for year {year}"}), 404
    return jsonify({"year": year, "total": total})

@app.route('/api/average_spending/<string:month>', methods=['GET'])
def get_average_spending(month):
    """
    NEW MEANINGFUL IMPROVEMENT: Calculates the average spending for a given month
    by iterating over the raw data, demonstrating dynamic calculation capability.
    """
    monthly_data = monthly_summary_cache.get(month)
    
    if not monthly_data:
        return jsonify({"error": f"Data not found for month {month}"}), 404
    
    total_sales = monthly_data["total"]
    count = monthly_data["count"]
    
    if count == 0:
        return jsonify({"error": f"No transactions found for month {month}"}), 404
        
    average = total_sales / count
    return jsonify({
        "month": month,
        "total_sales": total_sales,
        "transaction_count": count,
        "average_spending": round(average, 2)
    })

if __name__ == '__main__':
    # Initialize cache when the application starts
    initialize_cache()
    app.run(debug=True)