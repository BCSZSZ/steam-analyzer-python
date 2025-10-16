import requests
import json
import time
import urllib.parse
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# Base URL for the Steam App Reviews API
BASE_URL = "https://store.steampowered.com/appreviews/"

def get_all_steam_reviews(
    appid: int,
    language: str = 'all',
    review_type: str = 'all',
    purchase_type: str = 'all',
    num_per_page: int = 100,
    delay_seconds: float = 1.0,
    max_pages: Optional[int] = None
) -> Dict[str, Any]:
    """
    Fetches user reviews for a specified Steam App ID, handling pagination
    automatically using the 'cursor' mechanism.

    Args:
        appid: The Steam application ID (e.g., 570 for Dota 2).
        language: The language filter (e.g., 'english'). Use 'all' for all languages.
        review_type: Filter by 'all', 'positive', or 'negative'.
        purchase_type: Filter by 'all', 'non_steam_purchase', or 'steam'.
        num_per_page: Number of reviews to fetch per page (max 100).
        delay_seconds: The time to pause between API requests to prevent rate limiting.
        max_pages: If set, the scraping will stop after this many pages.

    Returns:
        A dictionary containing the list of all collected reviews and query summary.
    """
    if num_per_page > 100:
        print("Warning: num_per_page cannot exceed 100. Setting to 100.")
        num_per_page = 100

    all_reviews: List[Dict[str, Any]] = []
    cursor: str = '*'  # Initial cursor value
    query_summary: Optional[Dict[str, Any]] = None
    page_count: int = 0
    url = f"{BASE_URL}{appid}"
    
    # Static parameters for the API call
    params = {
        'json': '1',
        'filter': 'updated',
        'language': language,
        'review_type': review_type,
        'purchase_type': purchase_type,
        'num_per_page': str(num_per_page),
    }

    print(f"Starting review collection for App ID: {appid} with filter '{params['filter']}'")
    
    while True:
        if max_pages is not None and page_count >= max_pages:
            print(f"Page limit reached: Stopping after {page_count} pages.")
            break
            
        params['cursor'] = cursor  # FIXED: Assign raw cursor. urlencode will handle it.
        
        try:
            # Construct query string. urlencode will correctly handle special chars in cursor.
            query_string = urllib.parse.urlencode(params)
            request_url = f"{url}?{query_string}"

            print(f"Fetching page {page_count + 1}. ({len(all_reviews)} reviews collected)")
            print(f"Requesting URL: {request_url}")

            response = requests.get(request_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            page_count += 1
        
        except requests.exceptions.RequestException as e:
            print(f"Error during API request: {e}")
            break
        except json.JSONDecodeError:
            print("Error: Could not decode JSON response.")
            break

        if data.get('success') != 1:
            print(f"API call failed for App ID {appid}. Success code: {data.get('success')}")
            break

        if not query_summary:
            query_summary = data.get('query_summary', {})
            total_expected = query_summary.get('total_reviews', 'N/A')
            print(f"Query summary received. Total reviews for this filter: {total_expected}")

        reviews = data.get('reviews', [])
        
        if reviews:
            all_reviews.extend(reviews)
            next_cursor = data.get('cursor')
            
            if next_cursor and next_cursor != cursor:
                cursor = next_cursor
                if delay_seconds > 0:
                    print(f"Pausing for {delay_seconds} seconds...")
                    time.sleep(delay_seconds) 
            else:
                print("Finished collecting reviews: No new cursor returned.")
                break
        else:
            print("Finished collecting reviews: No more reviews returned.")
            break
            
    results = {
        'metadata': {
            'appid': appid,
            'language': language,
            'review_type': review_type,
            'purchase_type': purchase_type,
            'total_reviews_collected': len(all_reviews),
            'pages_fetched': page_count,
            'date_collected_utc': datetime.utcnow().isoformat()
        },
        'query_summary': query_summary,
        'reviews': all_reviews
    }
    return results

def save_reviews_to_json(data: Dict[str, Any], folder: str = 'json', max_pages_requested: Optional[int] = None) -> None:
    """
    Saves the collected review data to a uniquely named JSON file.

    Args:
        data: The data dictionary returned by get_all_steam_reviews.
        folder: The subfolder to save the JSON file in. Defaults to 'json'.
        max_pages_requested: The maximum number of pages that were requested, used for filename.
    """
    if not data or 'metadata' not in data or not data.get('reviews'):
        print("No data to save.")
        return

    metadata = data['metadata']
    appid = metadata['appid']
    total_reviews = metadata['total_reviews_collected']
    
    # Create a unique filename
    today_str = datetime.utcnow().strftime('%Y-%m-%d')
    # Append 'max' to the review count if a page limit was set
    review_count_str = f"{total_reviews}" if max_pages_requested is None else f"{total_reviews}max"
    filename = f"{appid}_{today_str}_{review_count_str}_reviews.json"
    
    # Ensure the output directory exists
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Created directory: ./{folder}/")
    except OSError as e:
        print(f"Error creating directory ./{folder}/: {e}")
        return

    filepath = os.path.join(folder, filename)
    
    # Save the file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print("-" * 40)
        print(f"Successfully collected {metadata['total_reviews_collected']} reviews from {metadata['pages_fetched']} pages.")
        print(f"Data saved to {filepath}")
        print("-" * 40)
    except IOError as e:
        print(f"Error saving file to {filepath}: {e}")

if __name__ == "__main__":
    # --- Configuration for standalone execution ---
    APP_ID_TO_SCRAPE = 570  # Example: 570 for Dota 2
    SCRAPE_LANGUAGE = 'all'
    SCRAPE_REVIEW_TYPE = 'all'
    REQUEST_DELAY_SECONDS = 1.0 # Be respectful to the API
    MAX_PAGES_TO_SCRAPE = 5 # Set to None to attempt to fetch all reviews

    print("--- Steam Review Scraper (Standalone Mode) ---")
    
    # 1. Fetch the data
    scraped_data = get_all_steam_reviews(
        appid=APP_ID_TO_SCRAPE, 
        language=SCRAPE_LANGUAGE,
        review_type=SCRAPE_REVIEW_TYPE,
        delay_seconds=REQUEST_DELAY_SECONDS,
        max_pages=MAX_PAGES_TO_SCRAPE
    )
    
    # 2. Save the data to a file
    save_reviews_to_json(scraped_data, max_pages_requested=MAX_PAGES_TO_SCRAPE)

