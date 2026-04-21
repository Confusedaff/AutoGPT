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


# Run initialization immediately when the application starts
initialize_cache()


def get_monthly_summary_cached(year, month):
    """Retrieves the pre-calculated monthly summary from the cache."""
    month_key = f"{year}-{month:02d}"
    return monthly_summary_cache.get(month_key)

def get_yearly_total(year):
    """Retrieves the total sales for a given year from the cache."""
    return yearly_summary_cache.get(year, 0)


# --- Flask Routes ---

@app.route('/api/summary/<int:year>')
def get_yearly_summary(year):
    """Endpoint to get the total sales for a specific year."""
    total_sales = get_yearly_total(year)
    return jsonify({"year": year, "total_sales": total_sales})


@app.route('/api/average_monthly_sales/<int:year>')
def get_average_monthly_sales(year):
    """Endpoint to calculate the average monthly sales for a specific year."""
    total_sales = get_yearly_total(year)
    
    # Calculate average based on the number of months actually present in the data for that year
    # Since the cache aggregates across all available months, we calculate the average over the 12 months 
    # for consistency, but handle the zero case robustly.
    if total_sales > 0:
        average = total_sales / 12.0
    else:
        average = 0.0
        
    return jsonify({"year": year, "total_sales": total_sales, "average_monthly_sales": round(average, 2)})


@app.route('/api/monthly_breakdown/<int:year>')
def get_monthly_breakdown(year):
    """
    New endpoint to retrieve the detailed monthly sales breakdown for a given year.
    """
    if year < 1900:
        return jsonify({"error": "Invalid year provided"}), 400
        
    monthly_data = {}
    
    # Iterate through all months in the cache and filter by the requested year
    for month_key, summary in monthly_summary_cache.items():
        if month_key.startswith(str(year)):
            # Format the output to include the month number
            month_num = int(month_key[5:])
            monthly_data[f"month_{month_num}"] = {
                "year": int(month_key[:4]),
                "total": summary['total']
            }
            
    return {"year": year, "data": list(monthly_data.values())}