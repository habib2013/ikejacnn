import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime

URL = "https://www.ikejaelectric.com/cnn/"

def scrape_outage_data():
    """Scrapes outage data from Ikeja Electric CNN page and returns a pandas DataFrame."""
    try:
        # Added User-Agent header as some sites block requests without it
        response = requests.get(URL, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {URL}: {e}")
        return pd.DataFrame(columns=['Date', 'Feeder', 'Status', 'Reason', 'Area']) # Return empty DataFrame on error

    soup = BeautifulSoup(response.content, 'html.parser')
    data_entries = []

    # The website structure seems to be text-based entries rather than a formal HTML table.
    # We'll look for <p> tags, as they often contain the textual data for each outage.
    # If <p> tags are not fruitful, we'll try to find common container elements like <div class="card-body">
    # and extract text from <p> tags within them.

    paragraphs = soup.find_all('p')
    text_from_elements = []

    if paragraphs:
        for p in paragraphs:
            text_from_elements.append(p.get_text(separator='\n', strip=True))
    else:
        # Fallback: Try to find 'card-body' divs if no top-level <p> tags with data
        card_bodies = soup.find_all('div', class_='card-body') # Common class for content blocks
        if card_bodies:
            for cb in card_bodies:
                # Extract text from all <p> tags within each card-body
                for p_tag in cb.find_all('p'):
                    text_from_elements.append(p_tag.get_text(separator='\n', strip=True))
        else:
            # Last resort: get all text from the body if other methods fail
            print("Warning: No specific 'p' tags or 'card-body' divs found containing expected data. Parsing all body text.")
            body_text = soup.body.get_text(separator='\n', strip=True) if soup.body else ""
            text_from_elements.append(body_text)

    full_text = '\n'.join(filter(None, text_from_elements)) # Join non-empty text blocks
    print(f"[PARSER_DEBUG] === Full Text for Parsing ===\n{full_text}\n===============================")
    lines = [line.strip() for line in full_text.split('\n') if line.strip()] # Split into clean lines
    print(f"[PARSER_DEBUG] Total lines for processing: {len(lines)}")

    # Regex patterns to identify and extract data fields
    date_pattern = re.compile(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun), \d{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4}")
    undertaking_keyword_pattern = re.compile(r"^UNDERTAKING:$", re.IGNORECASE) # Matches the literal line "UNDERTAKING:"
    areas_keyword_pattern = re.compile(r"^AREAS AFFECTED:$", re.IGNORECASE)   # Matches the literal line "AREAS AFFECTED:"
    # Pattern to extract Feeder and the rest of the reason, e.g., "OGBA FAULT: DOWNTIME..."
    # This pattern tries to capture a capitalized word (Feeder) followed by FAULT/OUTAGE etc.
    feeder_reason_pattern = re.compile(r"([A-Z0-9\s-]+(?:FAULT|OUTAGE|DOWNTIME|MAINTENANCE|SHUTDOWN)):\s*(.*)", re.IGNORECASE)
    # Simpler feeder pattern if the above is too specific or if 'FAULT' etc. is part of the feeder name
    feeder_simple_pattern = re.compile(r"([A-Z0-9_-]+)\s+(?:FAULT|OUTAGE|DOWNTIME|MAINTENANCE|SHUTDOWN)", re.IGNORECASE)

    current_date_str = None
    i = 0
    while i < len(lines):
        line = lines[i]
        print(f"[PARSER_DEBUG] Main loop: Processing line {i+1}/{len(lines)}: '{line}'")
        date_match = date_pattern.search(line)
        if date_match:
            current_date_str = date_match.group(0)
            print(f"[PARSER_DEBUG]   Date matched: '{current_date_str}'")
            try:
                parsed_date = datetime.strptime(current_date_str, "%a, %d %b %Y")
                formatted_date = parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                formatted_date = current_date_str # Keep original if parsing fails
            
            # Once a date is found, look for undertaking and areas in the subsequent lines.
            undertaking_text = ""
            areas_text = ""
            block_lines = [] # Store lines belonging to the current date block
            
            # Collect all lines until the next date or end of input
            j = i + 1
            while j < len(lines) and not date_pattern.search(lines[j]):
                block_lines.append(lines[j])
                j += 1
            
            # Process the collected block_lines for UNDERTAKING and AREAS AFFECTED
            k = 0
            while k < len(block_lines):
                line_to_check = block_lines[k]
                print(f"[PARSER_DEBUG]     Block line check: '{line_to_check}'")

                if undertaking_keyword_pattern.match(line_to_check) and not undertaking_text:
                    print(f"[PARSER_DEBUG]       Found UNDERTAKING keyword line: '{line_to_check}'")
                    # The actual undertaking text is expected to be on the next line(s)
                    temp_undertaking_lines = []
                    k_undertaking = k + 1
                    while k_undertaking < len(block_lines) and \
                          not areas_keyword_pattern.match(block_lines[k_undertaking]) and \
                          not date_pattern.search(block_lines[k_undertaking]): # Stop if next date found within block
                        if not undertaking_keyword_pattern.match(block_lines[k_undertaking]): # Avoid re-matching keyword
                             temp_undertaking_lines.append(block_lines[k_undertaking])
                        k_undertaking += 1
                    undertaking_text = " ".join(temp_undertaking_lines).strip()
                    print(f"[PARSER_DEBUG]       Collected UNDERTAKING text: '{undertaking_text}'")
                    k = k_undertaking -1 # Adjust k to continue after consumed lines
                
                elif areas_keyword_pattern.match(line_to_check) and not areas_text:
                    print(f"[PARSER_DEBUG]       Found AREAS AFFECTED keyword line: '{line_to_check}'")
                    # The actual areas text is expected to be on the next line(s)
                    temp_areas_lines = []
                    k_areas = k + 1
                    while k_areas < len(block_lines) and \
                          not date_pattern.search(block_lines[k_areas]) and \
                          not undertaking_keyword_pattern.match(block_lines[k_areas]): # Stop if next undertaking keyword
                        if not areas_keyword_pattern.match(block_lines[k_areas]): # Avoid re-matching keyword
                            temp_areas_lines.append(block_lines[k_areas])
                        k_areas += 1
                    areas_text = " ".join(temp_areas_lines).strip()
                    print(f"[PARSER_DEBUG]       Collected AREAS AFFECTED text: '{areas_text}'")
                    k = k_areas - 1 # Adjust k
                k += 1
            
            # Update main loop index i to skip the processed block
            i = j -1

            if undertaking_text: # Only proceed if we have an undertaking line
                feeder = "Unknown"
                reason = undertaking_text # Default reason is the full undertaking text
                status = "Outage" # Default status

                # Try to parse Feeder and refine Reason from undertaking_text
                feeder_reason_match = feeder_reason_pattern.search(undertaking_text)
                if feeder_reason_match:
                    feeder_part = feeder_reason_match.group(1).strip()
                    print(f"[PARSER_DEBUG]         Feeder part from regex: '{feeder_part}', Reason part: '{feeder_reason_match.group(2).strip()}'")
                    reason = feeder_reason_match.group(2).strip()
                    # Extract feeder name from feeder_part (e.g., "OGBA FAULT" -> "OGBA")
                    simple_feeder_match = feeder_simple_pattern.search(feeder_part)
                    if simple_feeder_match:
                        feeder = simple_feeder_match.group(1).strip()
                        print(f"[PARSER_DEBUG]           Simple feeder match: '{feeder}'")
                    else: # Fallback if simpler pattern doesn't match, use the whole part before ':'
                        feeder = feeder_part.split(':')[0].strip()

                    # Determine status from keywords
                    if "DOWNTIME" in feeder_part.upper(): status = "Downtime"
                    elif "MAINTENANCE" in feeder_part.upper(): status = "Maintenance"
                    elif "SHUTDOWN" in feeder_part.upper(): status = "Shutdown"
                    elif "FAULT" in feeder_part.upper(): status = "Fault"
                    # If reason still contains status keywords, try to clean it
                    reason = re.sub(r"^(FAULT|OUTAGE|DOWNTIME|MAINTENANCE|SHUTDOWN)[:\s-]*", "", reason, flags=re.IGNORECASE).strip()
                
                # If feeder is still 'Unknown', try a more generic split if ':' is present
                elif ':' in undertaking_text and feeder == "Unknown":
                    parts = undertaking_text.split(':', 1)
                    potential_feeder = parts[0].strip()
                    # Basic check: feeder names are often uppercase and without too many spaces
                    if potential_feeder.isupper() and ' ' not in potential_feeder.split()[0]: 
                        feeder = potential_feeder
                        reason = parts[1].strip() if len(parts) > 1 else ""
                        print(f"[PARSER_DEBUG]         Fallback feeder by colon split: Feeder='{feeder}', Reason='{reason}'")
                
                data_entries.append({
                    "Date": formatted_date,
                    "Feeder": feeder if feeder else "Unknown",
                    "Status": status,
                    "Reason": reason if reason else "Not specified",
                    "Area": areas_text if areas_text else "Not specified"
                })
                print(f"[PARSER_DEBUG]         Appended data entry: Date='{formatted_date}', Feeder='{feeder}', Status='{status}', Reason='{reason}', Area='{areas_text if areas_text else 'Not specified'}'")
        i += 1 # Move to the next line in the main loop

    if not data_entries:
        print("[PARSER_DEBUG] No data entries were successfully parsed and appended. This means the main parsing loop did not identify complete data blocks according to the current logic (Date -> Undertaking -> Areas Affected).")
        print("No data entries parsed. Check website structure or parsing logic.")
        return pd.DataFrame(columns=['Date', 'Feeder', 'Status', 'Reason', 'Area'])

    df = pd.DataFrame(data_entries)
    
    # Basic Data Cleaning
    df['Feeder'] = df['Feeder'].str.strip().str.upper()
    df['Area'] = df['Area'].str.strip()
    df['Reason'] = df['Reason'].str.strip()
    df['Status'] = df['Status'].str.strip().str.capitalize()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')

    # Remove entries where Date could not be parsed
    df.dropna(subset=['Date'], inplace=True)

    return df

if __name__ == '__main__':
    print(f"Attempting to scrape data from {URL}...")
    outage_df = scrape_outage_data()
    if not outage_df.empty:
        print("\nSuccessfully Scraped Data (First 5 entries):")
        print(outage_df.head())
        print(f"\nTotal entries scraped: {len(outage_df)}")
        if 'Feeder' in outage_df.columns:
            print("\nUnique Feeders Found (sample):")
            print(list(outage_df['Feeder'].unique()[:10]))
        if 'Area' in outage_df.columns:
            print("\nUnique Areas Found (sample):")
            print(list(outage_df['Area'].unique()[:5]))
        if 'Status' in outage_df.columns:
            print("\nUnique Statuses Found:")
            print(list(outage_df['Status'].unique()))
    else:
        print("\nNo data was scraped or parsed successfully.")
