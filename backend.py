"""
Backend module for Steam review data fetching and analysis.
Handles API communication with Steam and coordinates report generation.
"""

import requests
import json
import csv
import time
import urllib.parse
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import threading

from analyzers.language_report import LanguageReportAnalyzer

# API and storage configuration
BASE_URL = "https://store.steampowered.com/appreviews/"
TEMP_FOLDER = 'data/cache'
JSON_FOLDER = 'data/raw'
REPORTS_FOLDER = 'data/processed/reports'
CHECKPOINT_INTERVAL_PAGES = 50

# Language code to Chinese translation mapping (for legacy compatibility)
LANGUAGE_MAPPING = {
    'All Languages Combined': '全部语言', 'english': '英语', 'schinese': '简体中文',
    'tchinese': '繁体中文', 'japanese': '日语', 'koreana': '韩语', 'russian': '俄语',
    'german': '德语', 'french': '法语', 'spanish': '西班牙语', 'latam': '拉丁美洲西班牙语',
    'portuguese': '葡萄牙语', 'brazilian': '巴西葡萄牙语', 'polish': '波兰语',
    'turkish': '土耳其语', 'thai': '泰语', 'italian': '意大利语', 'dutch': '荷兰语',
    'danish': '丹麦语', 'swedish': '瑞典语', 'finnish': '芬兰语', 'norwegian': '挪威语',
    'hungarian': '匈牙利语', 'czech': '捷克语', 'romanian': '罗马尼亚语',
    'bulgarian': '保加利亚语', 'greek': '希腊语', 'vietnamese': '越南语',
    'ukrainian': '乌克兰语', 'arabic': '阿拉伯语', 'unknown_language': '未知语言'
}

# Steam review category to Chinese translation mapping
CATEGORY_MAPPING = {
    'Overwhelmingly Positive': '好评如潮', 'Very Positive': '特别好评',
    'Mostly Positive': '多半好评', 'Mixed': '褒贬不一', 'Mostly Negative': '多半差评',
    'Very Negative': '特别差评', 'Overwhelmingly Negative': '差评如潮',
    'No Reviews': '暂无评测'
}

def get_recent_review_summary(appid: int) -> Optional[Dict[str, int]]:
    """
    Fetch review summary statistics from Steam API.
    
    Args:
        appid: Steam application ID
        
    Returns:
        Dictionary with total, positive, and negative review counts, or None if failed
    """
    url = f"{BASE_URL}{appid}"
    params = {'json': '1', 'language': 'all'}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('success') == 1 and 'query_summary' in data:
            summary = data['query_summary']
            return {
                'total': summary.get('total_reviews', 0),
                'positive': summary.get('total_positive', 0),
                'negative': summary.get('total_negative', 0)
            }
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"Error fetching review summary: {e}")
    return None

def get_all_steam_reviews(
    appid: int, 
    status_queue, 
    cancel_event: threading.Event,
    resume: bool = False,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Fetch all reviews for a Steam application with checkpoint support.
    
    Implements pagination through Steam's cursor-based API, with automatic
    checkpointing every 50 pages to enable resume after cancellation.
    
    Args:
        appid: Steam application ID
        status_queue: Queue for sending status updates to UI
        cancel_event: Threading event to signal cancellation
        resume: If True, attempt to resume from checkpoint file
        **kwargs: Additional parameters (max_pages, delay_seconds, etc.)
        
    Returns:
        Dictionary with 'metadata' and 'reviews' keys, or None if cancelled
    """
    checkpoint_path = os.path.join(TEMP_FOLDER, f"{appid}_checkpoint.json")
    all_reviews: List[Dict[str, Any]] = []
    cursor = '*'
    
    # Load checkpoint if resuming
    if resume and os.path.exists(checkpoint_path):
        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
                all_reviews = checkpoint_data.get('reviews', [])
                cursor = checkpoint_data.get('next_cursor', '*')
                status_queue.put(f"Resuming download from {len(all_reviews)} reviews.")
        except (IOError, json.JSONDecodeError) as e:
            status_queue.put(f"Could not load checkpoint: {e}. Starting fresh.")
            all_reviews, cursor = [], '*'
    elif os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)

    # API request parameters
    # filter='recent' fetches ALL reviews sorted by creation time (including never-edited reviews)
    # filter='updated' only fetches reviews that were edited, missing never-edited reviews
    params = {
        'json': '1', 'filter': 'recent', 'language': 'all', 'review_type': 'all', 
        'purchase_type': 'all', 'num_per_page': '100', **kwargs
    }
    page_count = len(all_reviews) // 100
    url = f"{BASE_URL}{appid}"
    delay_seconds = float(params.get('delay_seconds', 1.0))
    max_pages = params.get('max_pages')

    status_queue.put(f"Starting review collection for App ID: {appid}...")

    # Pagination loop - continues until max_pages reached or no more reviews
    print(f"[DEBUG] Starting pagination loop. max_pages={max_pages}")
    consecutive_empty_pages = 0
    max_empty_pages = 10
    total_reviews_available = None  # Will be set from first API response
    
    while not (max_pages is not None and page_count >= max_pages):
        if cancel_event.is_set():
            status_queue.put("Download cancelled by user.")
            print(f"[DEBUG] Loop exit: User cancellation")
            break
        
        params['cursor'] = cursor
        try:
            query_string = urllib.parse.urlencode({k: v for k, v in params.items() if k not in ['delay_seconds', 'max_pages']})
            request_url = f"{url}?{query_string}"
            status_queue.put(f"Fetching page {page_count + 1}. ({len(all_reviews)} reviews collected)")

            response = requests.get(request_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Log API response details
            print(f"[DEBUG] Page {page_count + 1}: API success={data.get('success')}")
            
            if data.get('success') != 1:
                status_queue.put(f"API call failed. Success code: {data.get('success')}")
                print(f"[DEBUG] Loop exit: API success != 1")
                print(f"[DEBUG] API response: {data}")
                break

            reviews = data.get('reviews', [])
            query_summary = data.get('query_summary', {})
            next_cursor = data.get('cursor')
            
            # Get total available reviews from first response
            if total_reviews_available is None and query_summary:
                total_reviews_available = query_summary.get('total_reviews')
                if total_reviews_available:
                    print(f"[INFO] Total reviews available according to API: {total_reviews_available:,}")
                    status_queue.put(f"API reports {total_reviews_available:,} total reviews available")
            
            print(f"[DEBUG] Reviews in response: {len(reviews)}")
            print(f"[DEBUG] Query summary: {query_summary}")
            print(f"[DEBUG] Current cursor: {cursor[:50]}..." if len(cursor) > 50 else f"[DEBUG] Current cursor: {cursor}")
            print(f"[DEBUG] Next cursor: {next_cursor[:50]}..." if next_cursor and len(next_cursor) > 50 else f"[DEBUG] Next cursor: {next_cursor}")
            print(f"[DEBUG] Cursor changed: {next_cursor != cursor}")
            
            # Check if we should stop: empty reviews AND (no cursor change OR no cursor)
            if not reviews:
                consecutive_empty_pages += 1
                print(f"[DEBUG] Empty page encountered ({consecutive_empty_pages}/{max_empty_pages})")
                
                # Check if we've collected all available reviews
                if total_reviews_available and len(all_reviews) >= total_reviews_available:
                    status_queue.put(f"Finished: Collected all {len(all_reviews):,} reviews (matched total available)")
                    print(f"[DEBUG] Loop exit: Collected all available reviews ({len(all_reviews):,}/{total_reviews_available:,})")
                    break
                
                # Stop if cursor didn't change
                if not next_cursor or next_cursor == cursor:
                    status_queue.put("Finished: No more reviews returned.")
                    print(f"[DEBUG] Loop exit: Empty reviews array AND cursor unchanged/null")
                    print(f"[DEBUG] Total collected: {len(all_reviews):,} reviews")
                    if total_reviews_available:
                        print(f"[DEBUG] Expected {total_reviews_available:,}, got {len(all_reviews):,} ({len(all_reviews)/total_reviews_available*100:.1f}%)")
                    print(f"[DEBUG] Query summary at stop: {query_summary}")
                    break
                
                # Stop if too many consecutive empty pages
                if consecutive_empty_pages >= max_empty_pages:
                    status_queue.put(f"Finished: {max_empty_pages} consecutive empty pages - assuming end of data")
                    print(f"[DEBUG] Loop exit: Too many consecutive empty pages ({consecutive_empty_pages})")
                    print(f"[DEBUG] Total collected: {len(all_reviews):,} reviews")
                    if total_reviews_available:
                        print(f"[DEBUG] Expected {total_reviews_available:,}, got {len(all_reviews):,} ({len(all_reviews)/total_reviews_available*100:.1f}%)")
                    break
                
                # Empty reviews but cursor changed - might be a gap, continue
                print(f"[DEBUG] WARNING: Empty reviews but cursor changed - continuing (possible data gap)")
                status_queue.put(f"Warning: Empty page {page_count + 1}, but cursor changed. Continuing... ({consecutive_empty_pages}/{max_empty_pages})")
                page_count += 1
                cursor = next_cursor
                if delay_seconds > 0:
                    print(f"[DEBUG] Sleeping {delay_seconds} seconds before next request")
                    time.sleep(delay_seconds)
                print(f"[DEBUG] Continuing to next page after empty response...")
                continue

            # Reset empty page counter when we get reviews
            consecutive_empty_pages = 0
            all_reviews.extend(reviews)
            page_count += 1
            print(f"[DEBUG] Total reviews so far: {len(all_reviews):,}")
            
            # Check if we've reached the total available reviews
            if total_reviews_available and len(all_reviews) >= total_reviews_available:
                status_queue.put(f"Finished: Collected all {len(all_reviews):,} reviews")
                print(f"[DEBUG] Loop exit: Reached total available reviews ({len(all_reviews):,}/{total_reviews_available:,})")
                break

            if next_cursor and next_cursor != cursor:
                cursor = next_cursor
                # Save checkpoint every N pages for resume capability
                if page_count % CHECKPOINT_INTERVAL_PAGES == 0:
                    os.makedirs(TEMP_FOLDER, exist_ok=True)
                    with open(checkpoint_path, 'w', encoding='utf-8') as f:
                        json.dump({'reviews': all_reviews, 'next_cursor': cursor}, f)
                    status_queue.put(f"Milestone saved ({len(all_reviews)} reviews).")
                
                if delay_seconds > 0: 
                    print(f"[DEBUG] Sleeping {delay_seconds} seconds before next request")
                    time.sleep(delay_seconds)
                print(f"[DEBUG] Continuing to next page...")
            else:
                status_queue.put("Finished: No new cursor returned.")
                print(f"[DEBUG] Loop exit: Cursor unchanged or null")
                print(f"[DEBUG] next_cursor={next_cursor}, current_cursor={cursor[:50] if cursor and len(cursor) > 50 else cursor}")
                print(f"[DEBUG] Total collected: {len(all_reviews)} reviews")
                break
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            status_queue.put(f"An error occurred: {e}")
            print(f"[DEBUG] Loop exit: Exception - {type(e).__name__}: {e}")
            break
    
    print(f"[DEBUG] Exited pagination loop. Final count: {len(all_reviews)} reviews, pages: {page_count}")
    
    # Package collected data with metadata
    final_data = {
        'metadata': {
            'appid': appid, 
            'total_reviews_collected': len(all_reviews),
            'pages_fetched': page_count, 
            'date_collected_utc': datetime.utcnow().isoformat(),
            'max_pages_requested': max_pages
        },
        'reviews': all_reviews
    }

    # Handle cancellation - save checkpoint for resume
    if cancel_event.is_set():
        os.makedirs(TEMP_FOLDER, exist_ok=True)
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump({'reviews': all_reviews, 'next_cursor': cursor}, f)
        status_queue.put(f"Progress saved. You can resume later.")
        return None
    elif os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)

    return final_data

def save_reviews_to_json(data: Dict[str, Any], status_queue) -> None:
    """
    Save raw review data to JSON file with standardized naming.
    
    File naming format: {appid}_{date}_{count}_reviews.json
    Example: 1030300_2025-11-05_2000max_reviews.json
    
    Args:
        data: Dictionary containing 'metadata' and 'reviews' keys
        status_queue: Queue for sending status updates to UI
    """
    if not data or not data.get('reviews'):
        status_queue.put("No raw review data to save.")
        return

    metadata = data['metadata']
    appid = metadata['appid']
    total_reviews = metadata['total_reviews_collected']
    today_str = datetime.utcnow().strftime('%Y-%m-%d')
    
    count_str = "all" if metadata.get('max_pages_requested') is None else f"{total_reviews}max"
    filename = f"{appid}_{today_str}_{count_str}_reviews.json"
    
    os.makedirs(JSON_FOLDER, exist_ok=True)
    filepath = os.path.join(JSON_FOLDER, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        status_queue.put(f"Raw review data saved to {filepath}")
    except IOError as e:
        status_queue.put(f"Error saving raw JSON file: {e}")

def analyze_and_save_report(review_data: Dict[str, Any], status_queue, game_title: str = "N/A") -> Optional[List[Dict]]:
    """
    Generate language-based analysis report from review data.
    
    This is a wrapper function that delegates to LanguageReportAnalyzer.
    Maintains backward compatibility with existing code.
    
    Args:
        review_data: Dictionary containing 'metadata' and 'reviews' keys
        status_queue: Queue for sending status updates to UI
        game_title: Game title for report filename generation
        
    Returns:
        List of report row dictionaries for UI display, or None if no reviews
    """
    analyzer = LanguageReportAnalyzer(reports_folder=REPORTS_FOLDER)
    return analyzer.analyze(review_data, game_title=game_title, status_queue=status_queue)


