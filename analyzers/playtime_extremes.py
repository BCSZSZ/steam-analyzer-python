"""
Playtime Extremes Analyzer - identifies reviews with exceptional playtime values.

Finds the most extreme reviews (positive and negative) based on:
1. Playtime at review (hours played when review was written)
2. Total playtime (current total hours played)

Results are grouped by language for comparative analysis.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from .base_analyzer import BaseAnalyzer


class PlaytimeExtremesAnalyzer(BaseAnalyzer):
    """
    Analyzes reviews to find extreme playtime examples per language.
    
    For each language, identifies 4 key reviews:
    - Positive review with longest playtime at review time
    - Negative review with longest playtime at review time
    - Positive review with longest total playtime
    - Negative review with longest total playtime
    
    Uses single-pass O(n) algorithm for efficient processing of large datasets.
    """
    
    def __init__(self, output_base_dir: str = 'data/processed'):
        """
        Initialize the playtime extremes analyzer.
        
        Args:
            output_base_dir: Base directory for saving analysis results
        """
        super().__init__(output_base_dir)
    
    def analyze(self, json_data: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Identify extreme playtime reviews grouped by language.
        
        Uses a single-pass O(n) algorithm to efficiently group reviews by language
        and sentiment, then finds the maximum playtime values in each category.
        
        Args:
            json_data: Dictionary containing 'metadata' and 'reviews' keys
            **kwargs: Reserved for future parameters
            
        Returns:
            Dictionary containing:
            - metadata: Original metadata from input
            - analysis_date: Timestamp of analysis
            - total_reviews_analyzed: Count of processed reviews
            - languages_analyzed: List of all language codes found
            - extremes_by_language: Dictionary mapping language -> extreme reviews
            - saved_to: Path where results were saved
            
            Returns None if no reviews found.
        """
        all_reviews = self.get_reviews(json_data)
        metadata = self.get_metadata(json_data)
        
        if not all_reviews:
            return None
        
        # Single-pass grouping: partition reviews by language and sentiment
        # Time complexity: O(n) where n = number of reviews
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
        
        # Build results structure
        results = {
            'metadata': metadata,
            'analysis_date': datetime.utcnow().isoformat(),
            'total_reviews_analyzed': len(all_reviews),
            'languages_analyzed': list(language_groups.keys()),
            'extremes_by_language': {}
        }
        
        # Find extreme reviews for each language
        for lang, groups in language_groups.items():
            lang_extremes = {}
            
            # Find positive review with longest playtime at review time
            if groups['positive']:
                longest_playtime_review_pos = max(
                    groups['positive'], 
                    key=lambda r: r['author'].get('playtime_at_review', 0)
                )
                lang_extremes['longest_playtime_at_review_positive'] = longest_playtime_review_pos
            
            # Find negative review with longest playtime at review time
            if groups['negative']:
                longest_playtime_review_neg = max(
                    groups['negative'], 
                    key=lambda r: r['author'].get('playtime_at_review', 0)
                )
                lang_extremes['longest_playtime_at_review_negative'] = longest_playtime_review_neg
            
            # Find positive review with longest total playtime
            if groups['positive']:
                longest_playtime_forever_pos = max(
                    groups['positive'], 
                    key=lambda r: r['author'].get('playtime_forever', 0)
                )
                lang_extremes['longest_total_playtime_positive'] = longest_playtime_forever_pos
            
            # Find negative review with longest total playtime
            if groups['negative']:
                longest_playtime_forever_neg = max(
                    groups['negative'], 
                    key=lambda r: r['author'].get('playtime_forever', 0)
                )
                lang_extremes['longest_total_playtime_negative'] = longest_playtime_forever_neg
            
            # Include language-specific statistics
            lang_extremes['positive_count'] = len(groups['positive'])
            lang_extremes['negative_count'] = len(groups['negative'])
            lang_extremes['total_count'] = groups['total_count']
            
            results['extremes_by_language'][lang] = lang_extremes
        
        # Save analysis results to JSON file
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
