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

# Import analyzers
from analyzers.language_report import LanguageReportAnalyzer

# --- Constants and Mappings ---
BASE_URL = "https://store.steampowered.com/appreviews/"
TEMP_FOLDER = 'data/cache'
JSON_FOLDER = 'data/raw'
REPORTS_FOLDER = 'data/processed/reports'
CHECKPOINT_INTERVAL_PAGES = 50

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
CATEGORY_MAPPING = {
    'Overwhelmingly Positive': '好评如潮', 'Very Positive': '特别好评',
    'Mostly Positive': '多半好评', 'Mixed': '褒贬不一', 'Mostly Negative': '多半差评',
    'Very Negative': '特别差评', 'Overwhelmingly Negative': '差评如潮',
    'No Reviews': '暂无评测'
}

# --- Part 1: Data Fetching (Unchanged) ---

def get_recent_review_summary(appid: int) -> Optional[Dict[str, int]]:
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
    checkpoint_path = os.path.join(TEMP_FOLDER, f"{appid}_checkpoint.json")
    all_reviews: List[Dict[str, Any]] = []
    cursor = '*'
    
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

    params = {
        'json': '1', 'filter': 'updated', 'language': 'all', 'review_type': 'all', 
        'purchase_type': 'all', 'num_per_page': '100', **kwargs
    }
    page_count = len(all_reviews) // 100
    url = f"{BASE_URL}{appid}"
    delay_seconds = float(params.get('delay_seconds', 1.0))
    max_pages = params.get('max_pages')

    status_queue.put(f"Starting review collection for App ID: {appid}...")

    while not (max_pages is not None and page_count >= max_pages):
        if cancel_event.is_set():
            status_queue.put("Download cancelled by user.")
            break
        
        params['cursor'] = cursor
        try:
            query_string = urllib.parse.urlencode({k: v for k, v in params.items() if k not in ['delay_seconds', 'max_pages']})
            request_url = f"{url}?{query_string}"
            status_queue.put(f"Fetching page {page_count + 1}. ({len(all_reviews)} reviews collected)")

            response = requests.get(request_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success') != 1:
                status_queue.put(f"API call failed. Success code: {data.get('success')}")
                break

            reviews = data.get('reviews', [])
            if not reviews:
                status_queue.put("Finished: No more reviews returned.")
                break

            all_reviews.extend(reviews)
            page_count += 1
            next_cursor = data.get('cursor')

            if next_cursor and next_cursor != cursor:
                cursor = next_cursor
                if page_count % CHECKPOINT_INTERVAL_PAGES == 0:
                    os.makedirs(TEMP_FOLDER, exist_ok=True)
                    with open(checkpoint_path, 'w', encoding='utf-8') as f:
                        json.dump({'reviews': all_reviews, 'next_cursor': cursor}, f)
                    status_queue.put(f"Milestone saved ({len(all_reviews)} reviews).")
                
                if delay_seconds > 0: time.sleep(delay_seconds)
            else:
                status_queue.put("Finished: No new cursor returned.")
                break
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            status_queue.put(f"An error occurred: {e}")
            break
    
    final_data = {
        'metadata': {
            'appid': appid, 'total_reviews_collected': len(all_reviews),
            'pages_fetched': page_count, 'date_collected_utc': datetime.utcnow().isoformat(),
            'max_pages_requested': max_pages
        },
        'reviews': all_reviews
    }

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

# --- Part 2: Data Analysis (Updated) ---

def analyze_and_save_report(review_data: Dict[str, Any], status_queue, game_title: str = "N/A") -> Optional[List[Dict]]:
    """
    Wrapper function for backward compatibility.
    Uses the LanguageReportAnalyzer to generate reports.
    
    Args:
        review_data: Dictionary containing 'metadata' and 'reviews'
        status_queue: Queue for status updates
        game_title: Title of the game
        
    Returns:
        List of report row dictionaries, or None if no reviews
    """
    analyzer = LanguageReportAnalyzer(reports_folder=REPORTS_FOLDER)
    return analyzer.analyze(review_data, game_title=game_title, status_queue=status_queue)


