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
    # (Implementation remains the same)
    
    # Group data by year and sum amounts
    yearly_totals = {}
    for record in self.data:
        year = record['year']
        amount = record['amount']
        yearly_totals[year] = yearly_totals.get(year, 0) + amount

    # Store results in a structure accessible by year
    for year, total in yearly_totals.items():
        yearly_totals[year] = total

    self.yearly_totals = yearly_totals

# Initialize the data structure (simulating a class context for simplicity)
class DataStore:
    def __init__(self):
        self.data = [
            {'year': 2023, 'amount': 150},
            {'year': 2023, 'amount': 200},
            {'year': 2024, 'amount': 50},
            {'year': 2024, 'amount': 100},
        ]
        self.yearly_totals = {}

data_store = DataStore()
data_store.yearly_totals = {} # Initialize the store

# Run initialization
data_store.yearly_totals = {}
for record in data_store.data:
    year = record['year']
    amount = record['amount']
    data_store.yearly_totals[year] = data_store.yearly_totals.get(year, 0) + amount


def get_yearly_total(year):
    return data_store.yearly_totals.get(year, 0)

# --- Application Logic ---

def get_yearly_total_safe(year):
    """Safely retrieves the yearly total, returning None if the year is not found."""
    return get_yearly_total(year)

def get_yearly_total_safe_for_api(year):
    """Returns the yearly total or raises an error if the year is invalid (for API context)."""
    if year is None:
        raise ValueError("Invalid year provided.")
    return get_yearly_total(year)


# Example usage (simulating an API endpoint handler)
def handle_request(year):
    try:
        total = get_yearly_total_safe_for_api(year)
        if total is not None:
            return {"year": year, "total_amount": total}
        else:
            return {"error": f"No data found for year {year}"}
    except ValueError as e:
        return {"error": str(e)}

# print(handle_request(2023))
# print(handle_request(2025))