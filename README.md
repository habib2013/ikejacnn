# Ikeja Electric Outage Dashboard

This project is a full-stack Python web application that scrapes live power outage data from the Ikeja Electric CNN portal, processes it into structured insights, and presents it through an API and an interactive visual dashboard.

## Objective

To empower Ikeja Electric and its customers to:
- Track outages transparently.
- Identify weak points in the network.
- Plan responses and communicate better.
- Justify maintenance and investment decisions with real data.

## Project Structure

```
ikeja-dashboard/
├── app.py                  # Flask main app (API and frontend serving)
├── cnn_parser.py           # Web scraper module (BeautifulSoup and requests)
├── analysis.py             # Data analytics functions (pandas)
├── templates/
│   └── dashboard.html      # Web UI (HTML, Chart.js)
├── static/
│   └── script.js           # Frontend JavaScript for chart rendering and API calls
├── requirements.txt        # Python package dependencies
└── README.md               # This file
```

## Features

1.  **Web Scraper (`cnn_parser.py`):**
    *   Extracts data from the [Ikeja Electric CNN page](https://www.ikejaelectric.com/cnn/).
    *   Normalizes fields: `Feeder Name`, `Status`, `Date`/`Time`, `Area`/`Injection Substation`, `Reason`.
    *   Outputs a `pandas.DataFrame`.
    *   **Note:** The scraper's reliability depends on the structure of the source website. Significant changes to the website may require updates to `cnn_parser.py` (especially table and column selectors).

2.  **Data Analytics (`analysis.py`):**
    *   `get_top_faulty_feeders(df, n=5)`: Feeders with the most outages.
    *   `get_most_affected_areas(df, n=5)`: Areas most frequently affected.
    *   `get_trends_by_date(df)`: Tracks outage patterns over time (basic implementation).

3.  **Backend (`app.py` - Flask API):**
    *   `GET /`: Serves the frontend dashboard.
    *   `GET /api/data`: Returns the full cleaned outage data as JSON.
    *   `GET /api/outage-summary`: Returns top feeders, most affected areas, and last updated time.
    *   `GET /api/trends`: Returns daily outage counts.
    *   `GET /refresh-data`: Manually triggers a data re-scrape.
    *   Includes a simple in-memory cache for scraped data to reduce load on the source website.

4.  **Frontend Dashboard (`templates/dashboard.html` & `static/script.js`):**
    *   Uses `Chart.js` for visualizations.
    *   Displays:
        *   Top 5 feeders with most outages (Bar Chart).
        *   Top 5 most affected areas (Pie Chart).
        *   Last data update time.
        *   Manual data refresh button.
    *   Basic error handling for API data fetching.

## Setup and Installation

1.  **Clone the repository (or create the files as listed above).**

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

1.  **Start the Flask development server:**
    ```bash
    python app.py
    ```
    The application will typically be available at `http://127.0.0.1:5001` (or the port specified in `app.py`).

2.  **Open your web browser** and navigate to `http://127.0.0.1:5001` to view the dashboard.

    The first time you load the dashboard or hit `/api` endpoints, the application will attempt to scrape data from the Ikeja Electric website. This might take a few seconds. Subsequent requests will use cached data until the `/refresh-data` endpoint is called or the server restarts.

## Important Considerations & Potential Issues

*   **Web Scraping Stability:** The `cnn_parser.py` module relies on the current HTML structure of the Ikeja Electric CNN page. If the website layout changes, the scraper will likely break and require updates to the selectors (e.g., `soup.find('table')`, table header parsing, column name mapping).
*   **Data Quality & Normalization:** The quality of insights depends on the consistency and accuracy of the data on the source website. The current normalization in `cnn_parser.py` and data cleaning in `analysis.py` (e.g., date parsing, status interpretation) are based on assumptions and might need refinement once actual data patterns are observed.
*   **Error Handling:** Basic error handling is in place, but for a production system, more robust error logging and user feedback mechanisms would be needed.
*   **Scalability:** The current in-memory cache is suitable for single-user or low-traffic scenarios. For higher loads or persistent storage, a database (SQLite, PostgreSQL) and a more sophisticated caching strategy (e.g., Redis, Flask-Caching) would be necessary.
*   **Date/Time Parsing:** The `analysis.py` module assumes a specific date format (`'%d-%m-%Y %I:%M:%S %p'`) in `get_trends_by_date`. This must match the format scraped from the website. The scraper (`cnn_parser.py`) needs to ensure it correctly identifies and extracts the date/time column.
*   **Rate Limiting/Blocking:** Frequent scraping could lead to IP blocking by the website. Implement respectful scraping practices (e.g., appropriate delays, user-agent string) if running this continuously.

## Bonus Features (Future Enhancements)

*   **Database Integration:** Store scraped data in SQLite or PostgreSQL for historical analysis and daily snapshots.
*   **Scheduled Scraping:** Use Celery, APScheduler, or Cron jobs to automate data collection (e.g., every 6-12 hours).
*   **Advanced Dashboard Filters:** Add UI controls to filter data by date range, status (e.g., "Outage", "Restored"), or area.
*   **Predictive Analytics:** Implement simple machine learning models to predict outage risk at the feeder level based on historical trends.
