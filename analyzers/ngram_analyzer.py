"""
N-gram Analyzer - extracts and ranks n-gram frequencies from reviews.

Analyzes review text to find the most common word sequences (n-grams),
supporting both English and Chinese with language-specific preprocessing.
Results can be filtered by sentiment (positive/negative/both).
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from .base_analyzer import BaseAnalyzer
from .text_processor import TextProcessor, format_ngram
from utils import get_game_name


class NgramAnalyzer(BaseAnalyzer):
    """
    Analyzes reviews to extract n-gram frequencies.
    
    Supports:
    - Language-specific tokenization (English/Chinese)
    - Sentiment filtering (positive/negative/both)
    - Configurable n-gram size (1/2/3)
    - Minimum frequency threshold
    - Percentage calculation for top n-grams
    """
    
    def __init__(self, output_base_dir: str = 'data/processed'):
        """
        Initialize the n-gram analyzer.
        
        Args:
            output_base_dir: Base directory for saving analysis results
        """
        super().__init__(output_base_dir)
        self.text_processor = TextProcessor()
    
    def analyze(self, json_data: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Extract n-gram frequencies from reviews.
        
        Args:
            json_data: Dictionary containing 'metadata' and 'reviews' keys
            **kwargs: Analysis parameters:
                - language: 'english' or 'schinese' (required)
                - sentiment: 'positive', 'negative', or 'both' (default: 'both')
                - ngram_size: 1, 2, or 3 (default: 2)
                - min_frequency: Minimum count threshold (default: 2)
                - top_n: Number of top results to return (default: 100)
            
        Returns:
            Dictionary containing:
            - metadata: Original metadata from input
            - game_name: Game name from Steam API
            - analysis_params: Parameters used for analysis
            - analysis_date: Timestamp of analysis
            - total_reviews: Total reviews in dataset
            - filtered_reviews: Reviews matching language/sentiment filter
            - total_ngrams: Total n-gram instances found
            - unique_ngrams: Number of unique n-grams
            - top_ngrams: List of top n-grams with counts and percentages
            - saved_to: Path where results were saved
            
            Returns None if no matching reviews found.
        """
        all_reviews = self.get_reviews(json_data)
        metadata = self.get_metadata(json_data)
        
        if not all_reviews:
            return None
        
        # Extract parameters with defaults
        language = kwargs.get('language', 'english')
        sentiment = kwargs.get('sentiment', 'both')
        ngram_size = kwargs.get('ngram_size', 2)
        min_frequency = kwargs.get('min_frequency', 2)
        top_n = kwargs.get('top_n', 100)
        
        # Get game name using utility function
        appid = metadata.get('appid', 0)
        if isinstance(appid, str):
            appid = int(appid)
        game_name = get_game_name(appid)
        
        # Filter reviews by language and sentiment
        filtered_reviews = self._filter_reviews(all_reviews, language, sentiment)
        
        if not filtered_reviews:
            return None
        
        # Extract all n-grams from filtered reviews
        all_ngrams = []
        for review in filtered_reviews:
            review_text = review.get('review', '')
            if not review_text:
                continue
            
            # Tokenize text (pass appid for game-specific stopwords)
            tokens = self.text_processor.tokenize(review_text, language, remove_stopwords=True, appid=appid)
            
            # Generate n-grams (with repetitive n-gram filtering for n >= 2)
            # This filters out patterns like ('难评', '难评') or ('peak', 'peak')
            ngrams = self.text_processor.generate_ngrams(tokens, n=ngram_size, remove_repetitive=True)
            all_ngrams.extend(ngrams)
        
        if not all_ngrams:
            return None
        
        # Count n-gram frequencies
        ngram_counts = self.text_processor.count_ngrams(all_ngrams, min_frequency=min_frequency)
        
        # Calculate statistics
        total_ngrams = len(all_ngrams)
        unique_ngrams = len(ngram_counts)
        
        # Get top N results with percentages
        top_ngrams = []
        for ngram, count in ngram_counts[:top_n]:
            percentage = (count / total_ngrams) * 100
            top_ngrams.append({
                'ngram': format_ngram(ngram),
                'ngram_tuple': ngram,  # Keep tuple for reference
                'count': count,
                'percentage': round(percentage, 2)
            })
        
        # Build results structure
        results = {
            'metadata': metadata,
            'game_name': game_name,
            'analysis_params': {
                'language': language,
                'sentiment': sentiment,
                'ngram_size': ngram_size,
                'min_frequency': min_frequency,
                'top_n': top_n
            },
            'analysis_date': datetime.utcnow().isoformat(),
            'total_reviews': len(all_reviews),
            'filtered_reviews': len(filtered_reviews),
            'total_ngrams': total_ngrams,
            'unique_ngrams': unique_ngrams,
            'top_ngrams': top_ngrams
        }
        
        # Save analysis results to JSON file
        date_str = datetime.utcnow().strftime('%Y-%m-%d')
        sentiment_str = sentiment if sentiment != 'both' else 'all'
        ngram_type = self._get_ngram_type_name(ngram_size)
        filename = f"{appid}_{game_name.replace(' ', '_')}_{language}_{sentiment_str}_{ngram_type}_{date_str}.json"
        
        # Sanitize filename (remove invalid characters)
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        insights_folder = os.path.join(self.output_base_dir, 'insights')
        os.makedirs(insights_folder, exist_ok=True)
        filepath = os.path.join(insights_folder, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        
        results['saved_to'] = filepath
        
        return results
    
    def _filter_reviews(self, reviews: List[Dict], language: str, sentiment: str) -> List[Dict]:
        """
        Filter reviews by language and sentiment.
        
        Args:
            reviews: List of review dictionaries
            language: Target language code
            sentiment: 'positive', 'negative', or 'both'
            
        Returns:
            Filtered list of reviews
        """
        filtered = []
        
        for review in reviews:
            # Check language
            if review.get('language') != language:
                continue
            
            # Check sentiment
            if sentiment != 'both':
                is_positive = review.get('voted_up', False)
                if sentiment == 'positive' and not is_positive:
                    continue
                if sentiment == 'negative' and is_positive:
                    continue
            
            filtered.append(review)
        
        return filtered
    
    def _get_ngram_type_name(self, n: int) -> str:
        """
        Get human-readable name for n-gram size.
        
        Args:
            n: N-gram size
            
        Returns:
            Name string (e.g., 'unigrams', 'bigrams', 'trigrams')
        """
        names = {
            1: 'unigrams',
            2: 'bigrams',
            3: 'trigrams'
        }
        return names.get(n, f'{n}grams')


# Need to import re for filename sanitization
import re
