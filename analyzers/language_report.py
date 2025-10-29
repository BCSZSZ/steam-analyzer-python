"""
Language Report Analyzer - generates CSV reports grouped by language.
This is the original analysis functionality from backend.py.
"""

import csv
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from .base_analyzer import BaseAnalyzer


# Language and category mappings
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


class LanguageReportAnalyzer(BaseAnalyzer):
    """Generates CSV reports analyzing reviews by language and sentiment."""
    
    def __init__(self, reports_folder: str = 'data/processed/reports'):
        """
        Initialize the language report analyzer.
        
        Args:
            reports_folder: Folder to save CSV reports
        """
        super().__init__()
        self.reports_folder = reports_folder
    
    def categorize_score(self, positive_rate: float) -> str:
        """
        Assigns a Steam-like review category based on the positive review percentage.
        
        Args:
            positive_rate: The percentage of positive reviews (0.0 to 100.0)
            
        Returns:
            The corresponding review category string
        """
        if positive_rate >= 95.0:
            return "Overwhelmingly Positive"
        if positive_rate >= 80.0:
            return "Very Positive"
        if positive_rate >= 70.0:
            return "Mostly Positive"
        if positive_rate >= 40.0:
            return "Mixed"
        if positive_rate >= 20.0:
            return "Mostly Negative"
        return "Very Negative"
    
    def calculate_review_metrics(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates metrics for a list of reviews.
        
        Args:
            reviews: List of review dictionaries
            
        Returns:
            Dictionary containing total, positive count, rate, category, and averages
        """
        total_reviews = len(reviews)
        if total_reviews == 0:
            return {
                'total': 0, 'positive': 0, 'rate': 0.0, 'category': 'No Reviews',
                'avg_games_pos': 0, 'avg_games_neg': 0, 'avg_playtime_review_pos': 0,
                'avg_playtime_review_neg': 0, 'avg_playtime_forever_pos': 0, 'avg_playtime_forever_neg': 0
            }

        pos_reviews = [r for r in reviews if r.get('voted_up')]
        neg_reviews = [r for r in reviews if not r.get('voted_up')]

        pos_count = len(pos_reviews)
        neg_count = len(neg_reviews)
        
        rate = (pos_count / total_reviews) * 100 if total_reviews > 0 else 0
        category = self.categorize_score(rate)

        # Calculate averages for positive reviews
        if pos_count > 0:
            avg_games_pos = sum(r['author'].get('num_games_owned', 0) for r in pos_reviews) / pos_count
            avg_playtime_review_pos = (sum(r['author'].get('playtime_at_review', 0) for r in pos_reviews) / pos_count) / 60
            avg_playtime_forever_pos = (sum(r['author'].get('playtime_forever', 0) for r in pos_reviews) / pos_count) / 60
        else:
            avg_games_pos, avg_playtime_review_pos, avg_playtime_forever_pos = 0, 0, 0

        # Calculate averages for negative reviews
        if neg_count > 0:
            avg_games_neg = sum(r['author'].get('num_games_owned', 0) for r in neg_reviews) / neg_count
            avg_playtime_review_neg = (sum(r['author'].get('playtime_at_review', 0) for r in neg_reviews) / neg_count) / 60
            avg_playtime_forever_neg = (sum(r['author'].get('playtime_forever', 0) for r in neg_reviews) / neg_count) / 60
        else:
            avg_games_neg, avg_playtime_review_neg, avg_playtime_forever_neg = 0, 0, 0

        return {
            'total': total_reviews, 'positive': pos_count, 'rate': rate, 'category': category,
            'avg_games_pos': avg_games_pos, 'avg_games_neg': avg_games_neg,
            'avg_playtime_review_pos': avg_playtime_review_pos, 'avg_playtime_review_neg': avg_playtime_review_neg,
            'avg_playtime_forever_pos': avg_playtime_forever_pos, 'avg_playtime_forever_neg': avg_playtime_forever_neg
        }
    
    def analyze(self, json_data: Dict[str, Any], game_title: str = "N/A", 
                status_queue=None) -> Optional[List[Dict]]:
        """
        Analyze reviews and generate a language-based report.
        
        Args:
            json_data: Dictionary containing 'metadata' and 'reviews'
            game_title: Title of the game (for filename)
            status_queue: Optional queue for status updates
            
        Returns:
            List of report row dictionaries, or None if no reviews
        """
        all_reviews = self.get_reviews(json_data)
        if not all_reviews:
            if status_queue:
                status_queue.put("No reviews found for analysis.")
            return None

        # Group reviews by language
        reviews_by_language = {}
        for review in all_reviews:
            lang = review.get('language', 'unknown_language')
            reviews_by_language.setdefault(lang, []).append(review)

        # Build report rows
        report_rows = []
        
        # Overall metrics
        overall_metrics = self.calculate_review_metrics(all_reviews)
        report_rows.append({
            'Language': 'All Languages Combined',
            'Language_CN': LANGUAGE_MAPPING['All Languages Combined'],
            'Total Reviews': overall_metrics['total'],
            'Positive Reviews': overall_metrics['positive'],
            'Positive Rate': f"{overall_metrics['rate']:.2f}%",
            'Category': overall_metrics['category'],
            'Category_CN': CATEGORY_MAPPING.get(overall_metrics['category']),
            'Avg Games (Pos)': f"{overall_metrics['avg_games_pos']:.1f}",
            'Avg Games (Neg)': f"{overall_metrics['avg_games_neg']:.1f}",
            'Avg Playtime@Review (Pos, hrs)': f"{overall_metrics['avg_playtime_review_pos']:.1f}",
            'Avg Playtime@Review (Neg, hrs)': f"{overall_metrics['avg_playtime_review_neg']:.1f}",
            'Avg Playtime Total (Pos, hrs)': f"{overall_metrics['avg_playtime_forever_pos']:.1f}",
            'Avg Playtime Total (Neg, hrs)': f"{overall_metrics['avg_playtime_forever_neg']:.1f}"
        })

        # Per-language metrics
        for lang_code, reviews in sorted(reviews_by_language.items()):
            lang_metrics = self.calculate_review_metrics(reviews)
            report_rows.append({
                'Language': lang_code,
                'Language_CN': LANGUAGE_MAPPING.get(lang_code, lang_code),
                'Total Reviews': lang_metrics['total'],
                'Positive Reviews': lang_metrics['positive'],
                'Positive Rate': f"{lang_metrics['rate']:.2f}%",
                'Category': lang_metrics['category'],
                'Category_CN': CATEGORY_MAPPING.get(lang_metrics['category']),
                'Avg Games (Pos)': f"{lang_metrics['avg_games_pos']:.1f}",
                'Avg Games (Neg)': f"{lang_metrics['avg_games_neg']:.1f}",
                'Avg Playtime@Review (Pos, hrs)': f"{lang_metrics['avg_playtime_review_pos']:.1f}",
                'Avg Playtime@Review (Neg, hrs)': f"{lang_metrics['avg_playtime_review_neg']:.1f}",
                'Avg Playtime Total (Pos, hrs)': f"{lang_metrics['avg_playtime_forever_pos']:.1f}",
                'Avg Playtime Total (Neg, hrs)': f"{lang_metrics['avg_playtime_forever_neg']:.1f}"
            })
        
        # Save to CSV
        metadata = self.get_metadata(json_data)
        appid = metadata['appid']
        
        # Sanitize title for filename
        sanitized_title = ""
        if game_title and game_title != "N/A" and not game_title.startswith("AppID_"):
            sanitized_title = re.sub(r'[^\w\-\.]', '_', game_title)

        total_reviews = metadata['total_reviews_collected']
        today_str = datetime.utcnow().strftime('%Y-%m-%d')
        count_str = "all" if metadata.get('max_pages_requested') is None else f"{total_reviews}max"

        report_filename = f"{appid}_{sanitized_title}_{today_str}_{count_str}_report.csv"
        
        os.makedirs(self.reports_folder, exist_ok=True)
        filepath = os.path.join(self.reports_folder, report_filename)

        fieldnames = list(report_rows[0].keys())
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(report_rows)
            if status_queue:
                status_queue.put(f"Analysis complete. Report saved to {filepath}")
        except IOError as e:
            if status_queue:
                status_queue.put(f"Error writing CSV report: {e}")
        
        return report_rows
