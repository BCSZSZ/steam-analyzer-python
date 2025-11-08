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

def _save_checkpoint_and_data(appid, all_reviews, cursor, start_time, target_count, 
                              page_count, total_reviews_available, raw_data_filename, 
                              checkpoint_filename, status_queue):
    """
    Helper function to save checkpoint and raw data files.
    Updates filenames with current count and renames existing files.
    """
    # Generate/update filenames
    if not raw_data_filename:
        # First checkpoint - create initial filenames
        date_str = start_time.strftime('%Y-%m-%d')
        time_str = start_time.strftime('%H-%M-%S')
        target = target_count if target_count else (total_reviews_available if total_reviews_available else 0)
        raw_data_filename = f"{appid}_{date_str}_{time_str}_{target}_{len(all_reviews)}_reviews.json"
        checkpoint_filename = f"{appid}_{date_str}_{time_str}_{target}_{len(all_reviews)}_checkpoint.json"
    else:
        # Update filenames with new current count
        old_raw_filename = raw_data_filename
        old_checkpoint_filename = checkpoint_filename
        
        # Extract parts and update count
        parts = raw_data_filename.rsplit('_', 2)
        base = parts[0]  # appid_date_time_targetcount
        raw_data_filename = f"{base}_{len(all_reviews)}_reviews.json"
        checkpoint_filename = f"{base}_{len(all_reviews)}_checkpoint.json"
        
        # Rename old files if they exist
        old_raw_path = os.path.join(JSON_FOLDER, old_raw_filename)
        new_raw_path = os.path.join(JSON_FOLDER, raw_data_filename)
        if os.path.exists(old_raw_path) and old_raw_path != new_raw_path:
            os.rename(old_raw_path, new_raw_path)
        
        old_checkpoint_path = os.path.join(TEMP_FOLDER, old_checkpoint_filename)
        new_checkpoint_path = os.path.join(TEMP_FOLDER, checkpoint_filename)
        if os.path.exists(old_checkpoint_path) and old_checkpoint_path != new_checkpoint_path:
            os.rename(old_checkpoint_path, new_checkpoint_path)
    
    # Save checkpoint file
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    checkpoint_path = os.path.join(TEMP_FOLDER, checkpoint_filename)
    final_target = target_count if target_count else (total_reviews_available if total_reviews_available else len(all_reviews))
    checkpoint_data = {
        'cursor': cursor,
        'raw_data_filename': raw_data_filename,
        'appid': appid,
        'target_count': final_target,
        'current_count': len(all_reviews),
        'start_time': start_time.isoformat()
    }
    with open(checkpoint_path, 'w', encoding='utf-8') as f:
        json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
    
    # Save raw data file
    os.makedirs(JSON_FOLDER, exist_ok=True)
    raw_data_path = os.path.join(JSON_FOLDER, raw_data_filename)
    raw_data = {
        'metadata': {
            'appid': appid,
            'total_reviews_collected': len(all_reviews),
            'pages_fetched': page_count,
            'date_collected_utc': datetime.utcnow().isoformat(),
            'target_count': final_target,
            'start_time': start_time.isoformat()
        },
        'reviews': all_reviews
    }
    with open(raw_data_path, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    
    return raw_data_filename, checkpoint_filename


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
    all_reviews: List[Dict[str, Any]] = []
    cursor = '*'
    start_time = datetime.now()
    raw_data_filename = None
    checkpoint_filename = None
    target_count = None
    
    # Find existing checkpoint file for this appid (if any)
    checkpoint_path = None
    if resume:
        checkpoint_files = [f for f in os.listdir(TEMP_FOLDER) if f.startswith(f"{appid}_") and f.endswith('_checkpoint.json')]
        if checkpoint_files:
            # Use the most recent checkpoint
            checkpoint_path = os.path.join(TEMP_FOLDER, checkpoint_files[0])
    
    # Load checkpoint if resuming
    if resume and checkpoint_path and os.path.exists(checkpoint_path):
        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
                cursor = checkpoint_data.get('cursor', '*')
                raw_data_filename = checkpoint_data.get('raw_data_filename')
                target_count = checkpoint_data.get('target_count')
                start_time_str = checkpoint_data.get('start_time')
                if start_time_str:
                    start_time = datetime.fromisoformat(start_time_str)
                
                # Load existing reviews from raw data file
                if raw_data_filename:
                    raw_data_path = os.path.join(JSON_FOLDER, raw_data_filename)
                    if os.path.exists(raw_data_path):
                        with open(raw_data_path, 'r', encoding='utf-8') as rf:
                            existing_data = json.load(rf)
                            all_reviews = existing_data.get('reviews', [])
                status_queue.put(f"Resuming download from {len(all_reviews)} reviews.")
        except (IOError, json.JSONDecodeError) as e:
            status_queue.put(f"Could not load checkpoint: {e}. Starting fresh.")
            all_reviews, cursor = [], '*'
            start_time = datetime.now()
            raw_data_filename = None

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
    total_reviews_available = None  # Will be set from first API response
    
    while not (max_pages is not None and page_count >= max_pages):
        if cancel_event.is_set():
            # Save checkpoint on cancellation
            _save_checkpoint_and_data(appid, all_reviews, cursor, start_time, target_count, 
                                     page_count, total_reviews_available, raw_data_filename, 
                                     checkpoint_filename, status_queue)
            status_queue.put("Download cancelled by user.")
            print(f"[DEBUG] Loop exit: User cancellation")
            return None
        
        params['cursor'] = cursor
        try:
            query_string = urllib.parse.urlencode({k: v for k, v in params.items() if k not in ['delay_seconds', 'max_pages']})
            request_url = f"{url}?{query_string}"
            
            # Record request start time
            request_start = time.time()

            response = requests.get(request_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Calculate request duration
            request_duration = time.time() - request_start
            
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
            
            # Consolidated fetch log per page
            reviews_count = len(reviews)
            total_count = len(all_reviews) + reviews_count
            if total_reviews_available:
                progress_pct = (total_count / total_reviews_available * 100)
                status_indicator = "OK" if reviews_count > 0 else "EMPTY"
                print(f"[FETCH] Page {page_count + 1} | Reviews: +{reviews_count} (Total: {total_count:,} / {total_reviews_available:,} = {progress_pct:.1f}%) | Time: {request_duration:.2f}s | Status: {status_indicator} | Cursor: {next_cursor}")
            else:
                status_indicator = "OK" if reviews_count > 0 else "EMPTY"
                print(f"[FETCH] Page {page_count + 1} | Reviews: +{reviews_count} (Total: {total_count:,}) | Time: {request_duration:.2f}s | Status: {status_indicator} | Cursor: {next_cursor}")
            
            # Log target confirmation on first page
            if page_count == 0 and total_reviews_available:
                print(f"[FETCH] Target confirmed: {total_reviews_available:,} total reviews available")
            
            # Check if we should stop: empty reviews
            if not reviews:
                print(f"[FETCH] Page {page_count + 1} | Empty page encountered - stopping")
                
                # Check if we've collected all available reviews
                if total_reviews_available and len(all_reviews) >= total_reviews_available:
                    status_queue.put(f"Finished: Collected all {len(all_reviews):,} reviews (matched total available)")
                    print(f"[FETCH] Complete | All reviews collected ({len(all_reviews):,}/{total_reviews_available:,})")
                else:
                    # Save checkpoint before stopping
                    raw_data_filename, checkpoint_filename = _save_checkpoint_and_data(
                        appid, all_reviews, cursor, start_time, target_count, 
                        page_count, total_reviews_available, raw_data_filename, 
                        checkpoint_filename, status_queue)
                    status_queue.put(f"Empty page encountered. Checkpoint saved ({len(all_reviews):,} reviews).")
                    print(f"[FETCH] Checkpoint saved | {len(all_reviews):,} reviews | Can resume")
                break

            # Got reviews - add them to collection
            all_reviews.extend(reviews)
            page_count += 1
            
            # Check if we've reached the total available reviews
            if total_reviews_available and len(all_reviews) >= total_reviews_available:
                status_queue.put(f"Finished: Collected all {len(all_reviews):,} reviews")
                print(f"[FETCH] Complete | All {len(all_reviews):,} reviews collected")
                break

            if next_cursor and next_cursor != cursor:
                cursor = next_cursor
                # Save checkpoint every N pages for resume capability
                if page_count % CHECKPOINT_INTERVAL_PAGES == 0:
                    raw_data_filename, checkpoint_filename = _save_checkpoint_and_data(
                        appid, all_reviews, cursor, start_time, target_count, 
                        page_count, total_reviews_available, raw_data_filename, 
                        checkpoint_filename, status_queue)
                    print(f"[FETCH] Checkpoint saved at page {page_count} | {len(all_reviews):,} reviews")
                    status_queue.put(f"Checkpoint saved ({len(all_reviews)} reviews).")
                
                if delay_seconds > 0: 
                    time.sleep(delay_seconds)
            else:
                status_queue.put("Finished: No new cursor returned.")
                print(f"[FETCH] Stopped | No new cursor | Total: {len(all_reviews):,} reviews")
                break
        except requests.exceptions.Timeout as e:
            # Network timeout - save checkpoint
            status_queue.put(f"Network timeout occurred. Saving checkpoint...")
            print(f"[FETCH] ERROR | Timeout on page {page_count + 1} | Exception: {e}")
            raw_data_filename, checkpoint_filename = _save_checkpoint_and_data(
                appid, all_reviews, cursor, start_time, target_count, 
                page_count, total_reviews_available, raw_data_filename, 
                checkpoint_filename, status_queue)
            print(f"[FETCH] Checkpoint saved | {len(all_reviews):,} reviews | Can resume")
            status_queue.put(f"Checkpoint saved due to timeout. You can resume later.")
            break
        except requests.exceptions.ConnectionError as e:
            # Connection error - save checkpoint
            status_queue.put(f"Connection error occurred. Saving checkpoint...")
            print(f"[FETCH] ERROR | Connection error on page {page_count + 1} | Exception: {e}")
            raw_data_filename, checkpoint_filename = _save_checkpoint_and_data(
                appid, all_reviews, cursor, start_time, target_count, 
                page_count, total_reviews_available, raw_data_filename, 
                checkpoint_filename, status_queue)
            print(f"[FETCH] Checkpoint saved | {len(all_reviews):,} reviews | Can resume")
            status_queue.put(f"Checkpoint saved due to connection error. You can resume later.")
            break
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            # Other request/JSON errors - save checkpoint
            status_queue.put(f"An error occurred. Saving checkpoint...")
            print(f"[FETCH] ERROR | {type(e).__name__} on page {page_count + 1} | Exception: {e}")
            raw_data_filename, checkpoint_filename = _save_checkpoint_and_data(
                appid, all_reviews, cursor, start_time, target_count, 
                page_count, total_reviews_available, raw_data_filename, 
                checkpoint_filename, status_queue)
            print(f"[FETCH] Checkpoint saved | {len(all_reviews):,} reviews | Can resume")
            status_queue.put(f"Checkpoint saved due to error. You can resume later.")
            break
    
    print(f"[DEBUG] Exited pagination loop. Final count: {len(all_reviews)} reviews, pages: {page_count}")
    
    # Generate final filenames if not already created
    if not raw_data_filename:
        date_str = start_time.strftime('%Y-%m-%d')
        time_str = start_time.strftime('%H-%M-%S')
        final_target = target_count if target_count else (total_reviews_available if total_reviews_available else len(all_reviews))
        raw_data_filename = f"{appid}_{date_str}_{time_str}_{final_target}_{len(all_reviews)}_reviews.json"
        checkpoint_filename = f"{appid}_{date_str}_{time_str}_{final_target}_{len(all_reviews)}_checkpoint.json"
    else:
        # Update filenames with final count
        old_raw_filename = raw_data_filename
        old_checkpoint_filename = checkpoint_filename
        
        parts = raw_data_filename.rsplit('_', 2)
        base = parts[0]
        raw_data_filename = f"{base}_{len(all_reviews)}_reviews.json"
        checkpoint_filename = f"{base}_{len(all_reviews)}_checkpoint.json"
        
        # Rename old files if they exist
        old_raw_path = os.path.join(JSON_FOLDER, old_raw_filename)
        new_raw_path = os.path.join(JSON_FOLDER, raw_data_filename)
        if os.path.exists(old_raw_path) and old_raw_path != new_raw_path:
            os.rename(old_raw_path, new_raw_path)
    
    # Package collected data with metadata
    final_target = target_count if target_count else (total_reviews_available if total_reviews_available else len(all_reviews))
    final_data = {
        'metadata': {
            'appid': appid, 
            'total_reviews_collected': len(all_reviews),
            'pages_fetched': page_count, 
            'date_collected_utc': datetime.utcnow().isoformat(),
            'target_count': final_target,
            'start_time': start_time.isoformat()
        },
        'reviews': all_reviews
    }

    # If task completed successfully (not cancelled, not error), delete checkpoint
    if not cancel_event.is_set():
        checkpoint_path = os.path.join(TEMP_FOLDER, checkpoint_filename)
        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
            status_queue.put(f"Task completed - checkpoint file deleted.")

    return final_data

def save_reviews_to_json(data: Dict[str, Any], status_queue) -> None:
    """
    Save raw review data to JSON file with standardized naming.
    
    File naming format: {appid}_{date}_{time}_{targetcount}_{currentcount}_reviews.json
    Example: 1030300_2025-11-06_14-30-45_5000_5000_reviews.json
    
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
    target_count = metadata.get('target_count', total_reviews)
    
    # Get start time from metadata, or use current time
    start_time_str = metadata.get('start_time')
    if start_time_str:
        start_time = datetime.fromisoformat(start_time_str)
    else:
        start_time = datetime.now()
    
    date_str = start_time.strftime('%Y-%m-%d')
    time_str = start_time.strftime('%H-%M-%S')
    
    filename = f"{appid}_{date_str}_{time_str}_{target_count}_{total_reviews}_reviews.json"
    
    os.makedirs(JSON_FOLDER, exist_ok=True)
    filepath = os.path.join(JSON_FOLDER, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        status_queue.put(f"Raw review data saved to {filename}")
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


