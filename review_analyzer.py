import json
import csv
import os
from typing import List, Dict, Any

# --- Mappings for Chinese Output ---

# Mapping Steam language codes to their Chinese names
LANGUAGE_MAPPING = {
    'All Languages Combined': '全部语言',
    'english': '英语',
    'schinese': '简体中文',
    'tchinese': '繁体中文',
    'japanese': '日语',
    'koreana': '韩语',
    'russian': '俄语',
    'german': '德语',
    'french': '法语',
    'spanish': '西班牙语',
    'latam': '拉丁美洲西班牙语',
    'portuguese': '葡萄牙语',
    'brazilian': '巴西葡萄牙语',
    'polish': '波兰语',
    'turkish': '土耳其语',
    'thai': '泰语',
    'italian': '意大利语',
    'dutch': '荷兰语',
    'danish': '丹麦语',
    'swedish': '瑞典语',
    'finnish': '芬兰语',
    'norwegian': '挪威语',
    'hungarian': '匈牙利语',
    'czech': '捷克语',
    'romanian': '罗马尼亚语',
    'bulgarian': '保加利亚语',
    'greek': '希腊语',
    'vietnamese': '越南语',
    'ukrainian': '乌克兰语',
    'türkce': '土耳其语',  # Alias
    'arabic': '阿拉伯语',
    # Default for any language code not explicitly mapped
    'unknown_language': '未知语言' 
}

# Mapping Steam review categories to their Chinese names
CATEGORY_MAPPING = {
    'Overwhelmingly Positive': '好评如潮',
    'Very Positive': '特别好评',
    'Mostly Positive': '多半好评',
    'Mixed': '褒贬不一',
    'Mostly Negative': '多半差评',
    'Very Negative': '特别差评',
    'Overwhelmingly Negative': '差评如潮', 
    'No Reviews': '暂无评测'
}


def categorize_score(positive_rate: float) -> str:
    """
    Assigns a Steam-like review category based on the positive review percentage.
    This uses common community-observed thresholds for high review counts.
    
    Args:
        positive_rate: The percentage of positive reviews (0.0 to 100.0).

    Returns:
        The corresponding review category string.
    """
    if positive_rate >= 95.0:
        return "Overwhelmingly Positive"
    elif positive_rate >= 80.0:
        return "Very Positive"
    elif positive_rate >= 70.0:
        return "Mostly Positive"
    elif positive_rate >= 40.0:
        return "Mixed"
    elif positive_rate >= 20.0:
        return "Mostly Negative"
    else:
        return "Very Negative"

def calculate_review_metrics(reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates the total, positive count, positive rate, and category for a list of reviews.
    """
    total = len(reviews)
    if total == 0:
        return {
            'total': 0,
            'positive': 0,
            'rate': 0.00,
            'category': 'No Reviews'
        }
    
    # Review structure uses 'voted_up': True for positive
    positive_count = sum(1 for review in reviews if review.get('voted_up') is True)
    
    positive_rate = (positive_count / total) * 100
    category = categorize_score(positive_rate)
    
    return {
        'total': total,
        'positive': positive_count,
        'rate': positive_rate,
        'category': category
    }

def analyze_and_report(input_json_filename: str, output_csv_filename: str) -> None:
    """
    Reads JSON data, analyzes reviews overall and by language, and writes results to CSV.
    """
    if not os.path.exists(input_json_filename):
        print(f"Error: Input file not found at {input_json_filename}")
        print("Please ensure you have run the scraper and update the INPUT_JSON_FILENAME.")
        return

    try:
        with open(input_json_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_reviews = data.get('reviews', [])
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {input_json_filename}. Check file integrity.")
        return
    except IOError as e:
        print(f"Error reading file: {e}")
        return

    if not all_reviews:
        print("No reviews found in the JSON file. Analysis aborted.")
        return

    # 1. Group reviews by language
    reviews_by_language: Dict[str, List[Dict[str, Any]]] = {}
    for review in all_reviews:
        # The 'language' key contains the Steam language code (e.g., 'schinese', 'english')
        lang = review.get('language', 'unknown_language')
        if lang not in reviews_by_language:
            reviews_by_language[lang] = []
        reviews_by_language[lang].append(review)

    # 2. Analyze all languages combined (Overall)
    overall_metrics = calculate_review_metrics(all_reviews)
    
    overall_category_en = overall_metrics['category']
    overall_category_cn = CATEGORY_MAPPING.get(overall_category_en, overall_category_en)
    
    report_rows: List[Dict[str, Any]] = [{
        'Language': 'All Languages Combined',
        'Language_CN': LANGUAGE_MAPPING.get('All Languages Combined', '全部语言'),
        'Total Reviews': overall_metrics['total'],
        'Positive Reviews': overall_metrics['positive'],
        'Positive Rate': f"{overall_metrics['rate']:.2f}%",
        'Category': overall_category_en,
        'Category_CN': overall_category_cn
    }]

    # 3. Analyze each individual language
    for lang_code, reviews in reviews_by_language.items():
        lang_metrics = calculate_review_metrics(reviews)
        
        # Determine Chinese names
        # Use .get() with the lang_code as the fallback to ensure all keys are present,
        # even if not explicitly mapped.
        lang_name_cn = LANGUAGE_MAPPING.get(lang_code, lang_code) 
        category_en = lang_metrics['category']
        category_cn = CATEGORY_MAPPING.get(category_en, category_en)
        
        report_rows.append({
            'Language': lang_code,
            'Language_CN': lang_name_cn,
            'Total Reviews': lang_metrics['total'],
            'Positive Reviews': lang_metrics['positive'],
            'Positive Rate': f"{lang_metrics['rate']:.2f}%",
            'Category': category_en,
            'Category_CN': category_cn
        })

    # 4. Write to CSV
    fieldnames = [
        'Language', 'Language_CN', 
        'Total Reviews', 'Positive Reviews', 
        'Positive Rate', 
        'Category', 'Category_CN'
    ]
    try:
        # NOTE: Using 'utf-8' encoding for CSV output is correct, but requires
        # explicit "From Text/CSV" import in Excel for Chinese characters to render properly.
        with open(output_csv_filename, 'w', newline='', encoding='utf-8') as csvfile: 
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(report_rows)
            
        print("-" * 50)
        print(f"Analysis complete. Report saved to {output_csv_filename}")
        print(f"Total rows in report: {len(report_rows)}")
        print("-" * 50)
    except IOError as e:
        print(f"Error writing CSV file: {e}")


if __name__ == "__main__":
    # --- Configuration ---
    # !!! IMPORTANT: Update this to match the JSON file created by the scraper !!!
    # Example format: steam_reviews_570_p20_r2000.json
    INPUT_JSON_FILENAME = "steam_reviews_570_p20_r2000.json"
    OUTPUT_CSV_FILENAME = "review_analysis_report.csv"
    
    print("--- Steam Review Analyzer ---")
    analyze_and_report(INPUT_JSON_FILENAME, OUTPUT_CSV_FILENAME)
