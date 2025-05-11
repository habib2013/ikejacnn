from flask import Flask, jsonify, render_template, request
import pandas as pd
from cnn_parser import scrape_outage_data
from analysis import (
    get_outage_summary as get_analysis_summary, 
    group_by_date_for_trend_analysis,
    get_frequent_reasons,
    get_status_distribution,
    get_location_data,
    get_all_locations
)
import os

app = Flask(__name__)

# In-memory cache for the scraped data
# For a production app, consider a more robust caching mechanism or a database
CACHED_DATA = None

def get_data():
    """Helper function to get data, using cache if available."""
    global CACHED_DATA
    if CACHED_DATA is None:
        print("No cached data. Scraping new data...")
        CACHED_DATA = scrape_outage_data()
        if CACHED_DATA.empty:
            print("Scraping returned no data. Cache remains empty.")
            # Return a default structure if scraping fails, to prevent errors downstream
            return pd.DataFrame(columns=['Date', 'Feeder', 'Status', 'Reason', 'Area'])
        print(f"Data scraped successfully. {len(CACHED_DATA)} rows found.")
    else:
        print("Using cached data.")
    return CACHED_DATA

@app.route('/')
def dashboard():
    """Serves the frontend dashboard."""
    return render_template('dashboard.html')

@app.route('/api/data')
def get_all_data():
    """Returns the full cleaned outage data as JSON."""
    df = get_data()
    if df.empty:
        return jsonify({"error": "No data available"}), 500
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/outage-summary')
def get_outage_summary_endpoint(): 
    """Returns top faulty feeders, most affected areas, frequent reasons, status distribution, and all locations."""
    df = get_data()
    if df.empty:
        return jsonify({
            "error": "No data available to generate summary",
            "top_feeders": {},
            "most_affected_areas": {},
            "frequent_reasons": {},
            "status_distribution": {},
            "all_locations": []
        }), 500

    # Call the consolidated summary function from analysis.py
    summary_data = get_analysis_summary(df) 
    
    last_updated = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S') 

    return jsonify({
        "top_feeders": summary_data.get("top_faulty_feeders", {}),
        "most_affected_areas": summary_data.get("top_affected_areas", {}),
        "frequent_reasons": summary_data.get("frequent_reasons", {}),
        "status_distribution": summary_data.get("status_distribution", {}),
        "all_locations": summary_data.get("all_locations", []),
        "last_updated": last_updated
    })

@app.route('/api/trends')
def get_outage_trends():
    """Returns outage trends by date."""
    df = get_data()
    if df.empty:
        return jsonify({"error": "No data available to generate trends"}), 500

    trends = group_by_date_for_trend_analysis(df)
    
@app.route('/api/location-data')
def get_location_data_endpoint():
    """Returns outage data for a specific location."""
    location = request.args.get('location', '')
    if not location:
        return jsonify({"error": "Location parameter is required"}), 400
        
    df = get_data()
    if df.empty:
        return jsonify({"error": "No data available"}), 500
        
    location_df = get_location_data(df, location)
    if location_df.empty:
        return jsonify({
            "error": f"No data found for location: {location}",
            "location": location,
            "data": []
        })
        
    return jsonify({
        "location": location,
        "data": location_df.to_dict(orient='records'),
        "count": len(location_df)
    })
    
@app.route('/api/causes')
def get_causes_endpoint():
    """Returns the most frequent outage reasons."""
    df = get_data()
    if df.empty:
        return jsonify({"error": "No data available"}), 500
        
    reasons = get_frequent_reasons(df, n=5)
    return jsonify({
        "frequent_reasons": reasons.to_dict()
    })
    
@app.route('/api/status-distribution')
def get_status_distribution_endpoint():
    """Returns the distribution of outage statuses."""
    df = get_data()
    if df.empty:
        return jsonify({"error": "No data available"}), 500
        
    statuses = get_status_distribution(df)
    return jsonify({
        "status_distribution": statuses.to_dict()
    })
    
    if isinstance(trends, pd.Series) and not trends.empty:
        trends_dict = {str(index): value for index, value in trends.items()}
    else:
        trends_dict = {}

    return jsonify(trends_dict)

@app.route('/refresh-data') # Added a simple endpoint to manually refresh data
def refresh_data_endpoint():
    global CACHED_DATA
    CACHED_DATA = None # Clear cache
    get_data() # Rescrape
    return jsonify({"message": "Data refresh initiated. Check /api/data or /api/outage-summary for updated results."})



if __name__ == '__main__':
    # For local development, you can uncomment the line below and run `python3 app.py`
    # Make sure to set debug=False for any production-like testing locally.
    # port = int(os.environ.get("PORT", 5001))
    # app.run(debug=True, host='0.0.0.0', port=port)
    pass # Gunicorn will serve the app in production
