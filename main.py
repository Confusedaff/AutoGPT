from flask import Flask, jsonify, request
from datetime import datetime
from collections import defaultdict
import time

app = Flask(__name__)

# --- Database Simulation (Simulating SQLite persistence via in-memory structure) ---
# Consolidated and standardized sales data for analysis
SALES_DATA = [
    {"date": "2023-01-01", "amount": 100, "item": "Laptop"},
    {"date": "2023-01-05", "amount": 50, "item": "Mouse"},
    {"date": "2023-01-10", "amount": 200, "item": "Keyboard"},
    {"date": "2023-02-01", "amount": 150, "item": "Monitor"},
    {"date": "2023-02-15", "amount": 75, "item": "Mouse"},
    {"date": "2023-03-01", "amount": 300, "item": "Laptop"},
    {"date": "2023-03-15", "amount": 100, "item": "Monitor"},
    {"date": "2023-03-20", "amount": 50, "item": "Mouse"},
]

# --- Caching Mechanism ---
# Cache to store results of expensive calculations
CACHED_AVERAGES = None
CACHE_EXPIRY = 3600  # Cache duration in seconds

def calculate_monthly_averages(data):
    """Calculates the average value for each month in the provided data."""
    monthly_totals = defaultdict(float)
    monthly_counts = defaultdict(int)

    for record in data:
        # Assuming the date format is YYYY-MM-DD
        month = record['date'][:7]  # Extract YYYY-MM
        value = record['amount']

        monthly_totals[month] += value
        monthly_counts[month] += 1

    averages = {}
    for month, total in monthly_totals.items():
        count = monthly_counts[month]
        averages[month] = round(total / count, 2)

    return averages

@app.route('/averages', methods=['GET'])
def get_averages():
    """Endpoint to retrieve calculated monthly averages with caching."""
    global CACHED_AVERAGES

    current_time = time.time()

    # 1. Check Cache
    if CACHED_AVERAGES is not None and (current_time - CACHED_AVERAGES['timestamp'] < CACHE_EXPIRY):
        print("Cache HIT for /averages")
        return jsonify({"message": "Results served from cache", "monthly_averages": CACHED_AVERAGES['data']})

    # 2. Calculate if cache miss
    print("Cache miss. Calculating results...")
    
    # Simulate processing time for demonstration
    # time.sleep(0.1) 
    
    results = {}
    for month, avg in results.items():
        results[month] = avg

    # In a real application, this would be the heavy calculation
    results = {}
    for month, avg in results.items():
        results[month] = avg

    # 3. Store result in cache
    cache_key = "monthly_averages"
    results_to_cache = {}
    for month, avg in results.items():
        results_to_cache[month] = avg
        
    # Simple in-memory cache implementation
    # In a production environment, use Redis or a proper caching layer
    global CACHE
    CACHE = {cache_key: results_to_cache}
    
    # 4. Return result
    return results_to_cache

if __name__ == '__main__':
    # Example usage (if running standalone)
    # print("Access the endpoint to test the caching mechanism.")
    pass