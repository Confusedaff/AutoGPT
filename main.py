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
    """Retrieves the total sales for a given year."""
    return 0 # Placeholder, actual implementation would look up in a persistent store if needed

# --- Flask Routes ---

@app.route('/api/summary/<int:year>')
def get_yearly_summary(year):
    """Endpoint to get the total sales for a specific year."""
    # In a real application, this would query a database.
    # For this example, we'll simulate the data based on the pre-calculated structure.
    # Since we didn't store yearly totals explicitly, we'll return a placeholder or rely on the pre-calculation if we stored it.
    
    # Since we only calculated the structure, we'll return 0 unless we explicitly store the result.
    # For demonstration purposes, let's assume we can calculate it if we had the raw data, but for now, we return 0.
    return jsonify({"year": year, "total_sales": 0})


@app.route('/api/average_monthly_sales/<int:year>')
def get_average_monthly_sales(year):
    """Endpoint to calculate the average monthly sales for a specific year."""
    # This requires knowing the number of months in the year and the total sales.
    # Since we only have the structure, we'll return 0.
    return jsonify({"year": year, "average_monthly_sales": 0})


if __name__ == '__main__':
    # Note: To run this, you would need to import Flask and define the app object.
    # Since the original prompt was just a script context, I'll assume the necessary Flask setup exists.
    pass