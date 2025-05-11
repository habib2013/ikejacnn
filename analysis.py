import pandas as pd

def feeder_outage_counts(df):
    """Counts how often each feeder appears in the outage data.

    Args:
        df (pandas.DataFrame): DataFrame with outage data, expecting a 'Feeder' column.

    Returns:
        pandas.Series: A Series with feeder names and their counts, sorted.
                       Returns an empty Series if 'Feeder' not in df.columns or df is empty.
    """
    if df.empty or 'Feeder' not in df.columns:
        return pd.Series(dtype='int64')
    # Filter out 'UNKNOWN' feeders before counting
    return df[df['Feeder'].str.upper() != 'UNKNOWN']['Feeder'].value_counts()

def top_affected_areas(df, n=5):
    """Counts how often each area is affected and returns the top N.

    Args:
        df (pandas.DataFrame): DataFrame with outage data, expecting an 'Area' column.
        n (int): Number of top affected areas to return.

    Returns:
        pandas.Series: A Series with area names and their counts, sorted.
                       Returns an empty Series if 'Area' not in df.columns or df is empty.
    """
    if df.empty or 'Area' not in df.columns:
        return pd.Series(dtype='int64')
    # Filter out 'NOT SPECIFIED' areas before counting
    return df[df['Area'].str.lower() != 'not specified']['Area'].value_counts().nlargest(n)

def get_frequent_reasons(df, n=5):
    """Counts the occurrences of each outage reason and returns the top N.

    Args:
        df (pandas.DataFrame): DataFrame with outage data, expecting a 'Reason' column.
        n (int): Number of top reasons to return.

    Returns:
        pandas.Series: A Series with reasons and their counts, sorted.
                       Returns an empty Series if 'Reason' not in df.columns or df is empty.
    """
    if df.empty or 'Reason' not in df.columns:
        return pd.Series(dtype='int64')
    # Filter out 'NOT SPECIFIED' or empty reasons before counting
    valid_reasons = df[(df['Reason'].str.lower() != 'not specified') & 
                       (df['Reason'].str.strip() != '')]
    if valid_reasons.empty:
        return pd.Series(dtype='int64')
    return valid_reasons['Reason'].value_counts().nlargest(n)

def get_status_distribution(df):
    """Counts the occurrences of each status.

    Args:
        df (pandas.DataFrame): DataFrame with outage data, expecting a 'Status' column.

    Returns:
        pandas.Series: A Series with statuses and their counts.
                       Returns an empty Series if 'Status' not in df.columns or df is empty.
    """
    if df.empty or 'Status' not in df.columns:
        return pd.Series(dtype='int64')
    return df['Status'].value_counts()

def get_location_data(df, location):
    """Filters outage data for a specific location/area.

    Args:
        df (pandas.DataFrame): DataFrame with outage data, expecting an 'Area' column.
        location (str): The location/area to filter for.

    Returns:
        pandas.DataFrame: Filtered DataFrame containing only rows where 'Area' contains the location.
                         Returns empty DataFrame if 'Area' not in df.columns, df is empty, or no matches.
    """
    if df.empty or 'Area' not in df.columns or not location:
        return pd.DataFrame(columns=df.columns if not df.empty else ['Date', 'Feeder', 'Status', 'Reason', 'Area'])
    
    # Case-insensitive search for location in Area column
    return df[df['Area'].str.contains(location, case=False, na=False)]

def get_all_locations(df):
    """Extracts all unique locations/areas from the outage data.

    Args:
        df (pandas.DataFrame): DataFrame with outage data, expecting an 'Area' column.

    Returns:
        list: A sorted list of all unique area names.
              Returns an empty list if 'Area' not in df.columns or df is empty.
    """
    if df.empty or 'Area' not in df.columns:
        return []
    
    # Filter out 'NOT SPECIFIED' areas and empty strings
    valid_areas = df[(df['Area'].str.lower() != 'not specified') & 
                     (df['Area'].str.strip() != '')]
    if valid_areas.empty:
        return []
    
    # Extract unique areas and sort alphabetically
    areas = valid_areas['Area'].unique().tolist()
    return sorted(areas)

def get_outage_summary(df):
    """Generates a summary of outage data for the API.

    Args:
        df (pandas.DataFrame): The input DataFrame from the scraper.

    Returns:
        dict: A dictionary containing top faulty feeders, top affected areas,
              frequent reasons, status distribution, and all locations.
    """
    if df.empty:
        return {
            "top_faulty_feeders": {},
            "top_affected_areas": {},
            "frequent_reasons": {},
            "status_distribution": {},
            "all_locations": []
        }

    top_feeders = feeder_outage_counts(df).nlargest(5) # Get top 5 faulty feeders
    top_areas = top_affected_areas(df, n=5)       # Get top 5 affected areas
    reasons = get_frequent_reasons(df, n=5)       # Get top 5 frequent reasons
    statuses = get_status_distribution(df)        # Get distribution of statuses
    locations = get_all_locations(df)             # Get all unique locations

    return {
        "top_faulty_feeders": top_feeders.to_dict(),
        "top_affected_areas": top_areas.to_dict(),
        "frequent_reasons": reasons.to_dict(),
        "status_distribution": statuses.to_dict(),
        "all_locations": locations
    }

def group_by_date_for_trend_analysis(df):
    """Groups outage data by date to show daily outage counts (trends).

    Args:
        df (pandas.DataFrame): DataFrame with outage data, expecting a 'Date' column.

    Returns:
        pandas.Series: A Series with dates and their corresponding total outage counts.
                       Returns an empty Series if 'Date' not in df.columns, df is empty,
                       or if 'Date' cannot be parsed.
    """
    if df.empty or 'Date' not in df.columns:
        return pd.Series(dtype='int64')

    # Ensure 'Date' column is in datetime format
    # The cnn_parser should already format this, but good to be robust
    try:
        # Create a copy to avoid SettingWithCopyWarning if df is a slice
        df_copy = df.copy()
        df_copy['ParsedDate'] = pd.to_datetime(df_copy['Date'], errors='coerce')
        # Drop rows where date parsing failed
        df_copy.dropna(subset=['ParsedDate'], inplace=True)
        if df_copy.empty:
            return pd.Series(dtype='int64')
        return df_copy.groupby(df_copy['ParsedDate'].dt.date).size()
    except Exception as e:
        print(f"Error processing date for trend analysis: {e}")
        return pd.Series(dtype='int64')

if __name__ == '__main__':
    # Create a sample DataFrame for testing, matching cnn_parser.py output
    sample_data = {
        'Date': ['2023-01-01', '2023-01-01', '2023-01-02', '2023-01-02', '2023-01-03', '2023-01-01', None, '2023-01-04'],
        'Feeder': ['FDR_A', 'FDR_B', 'FDR_A', 'FDR_C', 'FDR_B', 'FDR_A', 'FDR_D', 'UNKNOWN'],
        'Status': ['Fault', 'Outage', 'Fault', 'Maintenance', 'Outage', 'Fault', 'Outage', 'Fault'],
        'Reason': ['R1', 'R2', 'R1', 'R3', 'R2', 'R1', 'R4', 'R5'],
        'Area': ['Area_X', 'Area_Y', 'Area_X', 'Area_Z', 'Area_Y', 'Area_X', 'Not specified', 'Area_X']
    }
    test_df = pd.DataFrame(sample_data)
    # cnn_parser.py converts Date to datetime and then to string 'YYYY-MM-DD'
    # For testing, ensure Date is in a format that group_by_date_for_trend_analysis can parse
    test_df['Date'] = pd.to_datetime(test_df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
    test_df.dropna(subset=['Date'], inplace=True) # Simulate cnn_parser cleaning

    print("--- Testing Analysis Functions ---")
    print("Sample DataFrame:")
    print(test_df)

    print("\nFeeder Outage Counts:")
    feeder_counts = feeder_outage_counts(test_df)
    print(feeder_counts)

    print("\nTop 2 Affected Areas:")
    top_areas_test = top_affected_areas(test_df, n=2)
    print(top_areas_test)

    print("\nOutage Summary (Top 5s):")
    summary = get_outage_summary(test_df)
    print(summary)

    print("\nDaily Outage Trends:")
    daily_trends = group_by_date_for_trend_analysis(test_df)
    print(daily_trends)

    # Test with empty DataFrame
    empty_df = pd.DataFrame(columns=['Date', 'Feeder', 'Status', 'Reason', 'Area'])
    print("\n--- Testing with Empty DataFrame ---")
    print("Feeder Outage Counts (Empty DF):")
    print(feeder_outage_counts(empty_df))
    print("Top Affected Areas (Empty DF):")
    print(top_affected_areas(empty_df))
    print("Outage Summary (Empty DF):")
    print(get_outage_summary(empty_df))
    print("Daily Outage Trends (Empty DF):")
    print(group_by_date_for_trend_analysis(empty_df))

    # Test with only 'UNKNOWN' feeders and 'Not specified' areas
    all_unknown_data = {
        'Date': ['2023-02-01', '2023-02-01'],
        'Feeder': ['UNKNOWN', 'unknown'],
        'Status': ['Fault', 'Outage'],
        'Reason': ['R1', 'R2'],
        'Area': ['Not specified', 'not specified']
    }
    test_df_all_unknowns = pd.DataFrame(all_unknown_data)
    test_df_all_unknowns['Date'] = pd.to_datetime(test_df_all_unknowns['Date']).dt.strftime('%Y-%m-%d')

    print("\n--- Testing with all 'Unknown'/'Not specified' values ---")
    print("Feeder Outage Counts (All Unknowns):")
    print(feeder_outage_counts(test_df_all_unknowns))
    print("Top Affected Areas (All Not specified):")
    print(top_affected_areas(test_df_all_unknowns, n=2))
    print("Outage Summary (All Unknowns):")
    print(get_outage_summary(test_df_all_unknowns))
