import json
import csv
import os
import requests
import time
import urllib.parse
from typing import List, Dict, Any, Optional, Callable

# --- Mappings and Categorization ---

LANGUAGE_MAPPING = {
    'All Languages Combined': '全部语言', 'english': '英语', 'schinese': '简体中文',
    'tchinese': '繁体中文', 'japanese': '日语', 'koreana': '韩语', 'russian': '俄语',
    'german': '德语', 'french': '法语', 'spanish': '西班牙语', 'latam': '拉丁美洲西班牙语',
    'portuguese': '葡萄牙语', 'brazilian': '巴西葡萄牙语', 'polish': '波兰语',
    'turkish': '土耳其语', 'thai': '泰语', 'italian': '意大利语', 'dutch': '荷兰语',
    'danish': '丹麦语', 'swedish': '瑞典语', 'finnish': '芬兰语', 'norwegian': '挪威语',
    'hungarian': '匈牙利语', 'czech': '捷克语', 'romanian': '罗马尼亚语',
    'bulgarian': '保加利亚语', 'greek': '希腊语', 'vietnamese': '越南语',
    'ukrainian': '乌克兰语', 'türkce': '土耳其语', 'arabic': '阿拉伯语',
    'unknown_language': '未知语言'
}

CATEGORY_MAPPING = {
    'Overwhelmingly Positive': '好评如潮', 'Very Positive': '特别好评',
    'Mostly Positive': '多半好评', 'Mixed': '褒贬不一', 'Mostly Negative': '多半差评',
    'Very Negative': '特别差评', 'Overwhelmingly Negative': '差评如潮',
    'No Reviews': '暂无评测'
}

def categorize_score(positive_rate: float) -> str:
    """Assigns a Steam-like review category based on the positive review percentage."""
    if positive_rate >= 95.0: return "Overwhelmingly Positive"
    if positive_rate >= 80.0: return "Very Positive"
    if positive_rate >= 70.0: return "Mostly Positive"
    if positive_rate >= 40.0: return "Mixed"
    if positive_rate >= 20.0: return "Mostly Negative"
    return "Very Negative"

def calculate_review_metrics(reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculates review metrics for a list of reviews."""
    total = len(reviews)
    if total == 0:
        return {'total': 0, 'positive': 0, 'rate': 0.00, 'category': 'No Reviews'}
    positive_count = sum(1 for r in reviews if r.get('voted_up') is True)
    positive_rate = (positive_count / total) * 100
    return {
        'total': total, 'positive': positive_count, 'rate': positive_rate,
        'category': categorize_score(positive_rate)
    }

def analyze_and_report(input_json_filename: str, output_csv_filename: str, log_callback: Callable):
    """Reads JSON data, analyzes reviews, and writes results to a CSV file."""
    log_callback(f"Starting analysis of '{os.path.basename(input_json_filename)}'...")
    if not os.path.exists(input_json_filename):
        log_callback(f"Error: Input file not found: {input_json_filename}")
        return

    try:
        with open(input_json_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        all_reviews = data.get('reviews', [])
    except (json.JSONDecodeError, IOError) as e:
        log_callback(f"Error reading or decoding JSON file: {e}")
        return

    if not all_reviews:
        log_callback("No reviews found in the JSON file. Analysis aborted.")
        return

    reviews_by_language: Dict[str, List[Dict[str, Any]]] = {}
    for review in all_reviews:
        lang = review.get('language', 'unknown_language')
        reviews_by_language.setdefault(lang, []).append(review)

    overall_metrics = calculate_review_metrics(all_reviews)
    report_rows = [{
        'Language': 'All Languages Combined',
        'Language_CN': LANGUAGE_MAPPING['All Languages Combined'],
        'Total Reviews': overall_metrics['total'],
        'Positive Reviews': overall_metrics['positive'],
        'Positive Rate': f"{overall_metrics['rate']:.2f}%",
        'Category': overall_metrics['category'],
        'Category_CN': CATEGORY_MAPPING.get(overall_metrics['category'], overall_metrics['category'])
    }]

    for lang_code, reviews in reviews_by_language.items():
        lang_metrics = calculate_review_metrics(reviews)
        category_en = lang_metrics['category']
        report_rows.append({
            'Language': lang_code,
            'Language_CN': LANGUAGE_MAPPING.get(lang_code, lang_code),
            'Total Reviews': lang_metrics['total'],
            'Positive Reviews': lang_metrics['positive'],
            'Positive Rate': f"{lang_metrics['rate']:.2f}%",
            'Category': category_en,
            'Category_CN': CATEGORY_MAPPING.get(category_en, category_en)
        })

    fieldnames = ['Language', 'Language_CN', 'Total Reviews', 'Positive Reviews', 'Positive Rate', 'Category', 'Category_CN']
    try:
        with open(output_csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(report_rows)
        log_callback(f"Analysis complete. Report saved to '{os.path.basename(output_csv_filename)}'")
    except IOError as e:
        log_callback(f"Error writing CSV file: {e}")


# --- Steam API Fetching Logic ---

def get_all_steam_reviews(
    appid: int,
    log_callback: Callable,
    max_pages: Optional[int] = None,
    language: str = 'all',
    review_type: str = 'all',
    purchase_type: str = 'all',
    num_per_page: int = 100,
    delay_seconds: float = 1.0 # Safety default
) -> Optional[Dict[str, Any]]:
    """Fetches user reviews for a specified Steam App ID."""
    all_reviews: List[Dict[str, Any]] = []
    cursor = '*'
    page_count = 0
    url = f"https://store.steampowered.com/appreviews/{appid}"
    
    # Using 'recent' filter is more reliable for deep pagination
    params = {
        'json': 1, 'filter': 'recent', 'language': language,
        'review_type': review_type, 'purchase_type': purchase_type,
        'num_per_page': num_per_page
    }

    log_callback(f"Starting review collection for App ID: {appid}")
    
    while True:
        if max_pages is not None and page_count >= max_pages:
            log_callback(f"Page limit reached: Stopping after {page_count} pages.")
            break
            
        params['cursor'] = urllib.parse.quote(cursor)
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            log_callback(f"Error during API request: {e}")
            return None
        except json.JSONDecodeError:
            log_callback("Error: Could not decode JSON response.")
            return None

        if data.get('success') != 1:
            log_callback(f"API call failed. Success code: {data.get('success')}. Please check App ID.")
            return None

        page_count += 1
        reviews = data.get('reviews', [])
        
        if not reviews:
            log_callback("Finished collecting reviews: Review list is empty.")
            break
            
        all_reviews.extend(reviews)
        log_callback(f"Fetched page {page_count}. Total reviews collected: {len(all_reviews)}")

        next_cursor = data.get('cursor')
        if next_cursor and next_cursor != cursor:
            cursor = next_cursor
            time.sleep(delay_seconds)
        else:
            log_callback("Finished collecting reviews: No new cursor.")
            break
            
    return {
        'metadata': { 'appid': appid, 'total_reviews_collected': len(all_reviews), 'pages_fetched': page_count},
        'reviews': all_reviews
    }
