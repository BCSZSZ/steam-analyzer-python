"""
Playtime Extremes Analyzer - finds reviews with the longest playtime.
Identifies extreme reviews by playtime at review and total playtime.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from .base_analyzer import BaseAnalyzer


class PlaytimeExtremesAnalyzer(BaseAnalyzer):
    """Finds reviews with extreme playtime values."""
    
    def __init__(self, output_base_dir: str = 'data/processed'):
        """Initialize the playtime extremes analyzer."""
        super().__init__(output_base_dir)
    
    def analyze(self, json_data: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Find the reviews with longest playtime, overall and per language.
        
        Args:
            json_data: Dictionary containing 'metadata' and 'reviews'
            
        Returns:
            Dictionary with extreme reviews (overall and per-language) and metadata, or None if no reviews
        """
        all_reviews = self.get_reviews(json_data)
        metadata = self.get_metadata(json_data)
        
        if not all_reviews:
            return None
        
        # Single-pass algorithm: process all reviews once and group by language
        # This is O(n) instead of O(n*m) where n=reviews, m=languages
        language_groups = {}
        
        for review in all_reviews:
            lang = review.get('language', 'unknown')
            is_positive = review.get('voted_up', False)
            
            if lang not in language_groups:
                language_groups[lang] = {
                    'positive': [],
                    'negative': [],
                    'total_count': 0
                }
            
            language_groups[lang]['total_count'] += 1
            
            if is_positive:
                language_groups[lang]['positive'].append(review)
            else:
                language_groups[lang]['negative'].append(review)
        
        # Prepare results structure
        results = {
            'metadata': metadata,
            'analysis_date': datetime.utcnow().isoformat(),
            'total_reviews_analyzed': len(all_reviews),
            'languages_analyzed': list(language_groups.keys()),
            'extremes_by_language': {}
        }
        
        # Find extremes for each language
        for lang, groups in language_groups.items():
            lang_extremes = {}
            
            # Longest playtime at review (positive)
            if groups['positive']:
                longest_playtime_review_pos = max(
                    groups['positive'], 
                    key=lambda r: r['author'].get('playtime_at_review', 0)
                )
                lang_extremes['longest_playtime_at_review_positive'] = longest_playtime_review_pos
            
            # Longest playtime at review (negative)
            if groups['negative']:
                longest_playtime_review_neg = max(
                    groups['negative'], 
                    key=lambda r: r['author'].get('playtime_at_review', 0)
                )
                lang_extremes['longest_playtime_at_review_negative'] = longest_playtime_review_neg
            
            # Longest total playtime (positive)
            if groups['positive']:
                longest_playtime_forever_pos = max(
                    groups['positive'], 
                    key=lambda r: r['author'].get('playtime_forever', 0)
                )
                lang_extremes['longest_total_playtime_positive'] = longest_playtime_forever_pos
            
            # Longest total playtime (negative)
            if groups['negative']:
                longest_playtime_forever_neg = max(
                    groups['negative'], 
                    key=lambda r: r['author'].get('playtime_forever', 0)
                )
                lang_extremes['longest_total_playtime_negative'] = longest_playtime_forever_neg
            
            # Add language stats
            lang_extremes['positive_count'] = len(groups['positive'])
            lang_extremes['negative_count'] = len(groups['negative'])
            lang_extremes['total_count'] = groups['total_count']
            
            results['extremes_by_language'][lang] = lang_extremes
        
        # Save to file
        appid = metadata.get('appid', 'unknown')
        date_str = datetime.utcnow().strftime('%Y-%m-%d')
        filename = f"{appid}_extreme_reviews_by_language_{date_str}.json"
        
        insights_folder = os.path.join(self.output_base_dir, 'insights')
        os.makedirs(insights_folder, exist_ok=True)
        filepath = os.path.join(insights_folder, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        
        results['saved_to'] = filepath
        
        return results
