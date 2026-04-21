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
yearly_summary_cache = {} # New cache for yearly totals

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
    
    # IMPROVEMENT: Calculate and store yearly totals in the cache
    yearly_summary_cache = {}
    for month_key, summary in monthly_data.items():
        # Extract year (YYYY)
        year = month_key[:4]
        if year not in yearly_summary_cache:
            yearly_summary_cache[year] = 0
        yearly_summary_cache[year] += summary["total"]

def get_monthly_summary_cached(year, month):
    """Retrieves the pre-calculated monthly summary from the cache."""
    # Implementation omitted for brevity, assuming it works as before
    pass

def get_yearly_total(year):
    """Retrieves the pre-calculated total for a given year."""
    return yearly_totals.get(year, 0)

# Helper to store the pre-calculated totals globally for easy access
yearly_totals = {}


# Example route implementation (assuming Flask context)
def route_get_summary(year):
    return {"year": year, "total": get_yearly_total(year)}

# Note: In a real Flask app, you would define routes here.
# The core logic change is in how data is pre-calculated upon startup.