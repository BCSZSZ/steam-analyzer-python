"""
TF-IDF Analyzer - identifies distinctive terms in positive vs negative reviews.

Uses TF-IDF (Term Frequency-Inverse Document Frequency) to find terms that
are characteristic of positive reviews vs negative reviews. This reveals
what makes each sentiment group unique.
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer

from .base_analyzer import BaseAnalyzer
from .text_processor import TextProcessor
from utils import get_game_name


class TfidfAnalyzer(BaseAnalyzer):
    """
    Analyzes reviews using TF-IDF to find distinctive terms.
    
    TF-IDF = Term Frequency × Inverse Document Frequency
    - High TF: Term appears frequently in a document
    - Low IDF: Term is rare across all documents
    - High TF-IDF: Term is frequent in THIS document but rare in OTHERS
    
    For sentiment analysis:
    - Compare positive reviews (as one corpus) vs negative reviews (as another)
    - High TF-IDF in positive = distinctive positive sentiment terms
    - High TF-IDF in negative = distinctive negative sentiment terms
    """
    
    def __init__(self, output_base_dir: str = 'data/processed'):
        """
        Initialize the TF-IDF analyzer.
        
        Args:
            output_base_dir: Base directory for saving analysis results
        """
        super().__init__(output_base_dir)
        self.text_processor = TextProcessor()
    
    def analyze(self, json_data: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Identify distinctive terms using TF-IDF comparison.
        
        Process:
        1. Filter reviews by language
        2. Split into positive and negative groups
        3. Combine each group's reviews into a single document
        4. Calculate TF-IDF scores for each group
        5. Extract top distinctive terms for each sentiment
        
        Args:
            json_data: Dictionary containing 'metadata' and 'reviews' keys
            **kwargs: Analysis parameters:
                - language: 'english' or 'schinese' (required)
                - top_n: Number of top terms to return (default: 50)
                - max_features: Maximum vocabulary size (default: 5000)
                - min_df: Minimum document frequency (default: 2)
                - ngram_range: Tuple (min_n, max_n) for n-gram extraction (default: (1, 2))
            
        Returns:
            Dictionary containing:
            - metadata: Original metadata from input
            - game_name: Game name from Steam API
            - analysis_params: Parameters used for analysis
            - analysis_date: Timestamp of analysis
            - total_reviews: Total reviews in dataset
            - positive_reviews_count: Number of positive reviews analyzed
            - negative_reviews_count: Number of negative reviews analyzed
            - positive_distinctive_terms: List of top positive terms with scores
            - negative_distinctive_terms: List of top negative terms with scores
            - saved_to: Path where results were saved
            
            Returns None if insufficient data for analysis.
        """
        all_reviews = self.get_reviews(json_data)
        metadata = self.get_metadata(json_data)
        
        if not all_reviews:
            return None
        
        # Extract parameters with defaults
        language = kwargs.get('language', 'english')
        top_n = kwargs.get('top_n', 50)
        max_features = kwargs.get('max_features', 5000)
        min_df = kwargs.get('min_df', 2)
        ngram_range = kwargs.get('ngram_range', (1, 2))
        
        # Get game name using utility function
        appid = metadata.get('appid', 0)
        if isinstance(appid, str):
            appid = int(appid)
        game_name = get_game_name(appid)
        
        # Filter and group reviews by sentiment
        positive_reviews = []
        negative_reviews = []
        
        for review in all_reviews:
            if review.get('language') != language:
                continue
            
            review_text = review.get('review', '')
            if not review_text:
                continue
            
            # Preprocess: tokenize and join back (for TF-IDF vectorizer)
            # Both English and Chinese need space-separated tokens for TF-IDF
            tokens = self.text_processor.tokenize(review_text, language, remove_stopwords=True, appid=appid)
            processed_text = ' '.join(tokens)
            
            if not processed_text:
                continue
            
            if review.get('voted_up', False):
                positive_reviews.append(processed_text)
            else:
                negative_reviews.append(processed_text)
        
        # Check if we have enough data
        if len(positive_reviews) < 5 or len(negative_reviews) < 5:
            return None
        
        # Build corpus: each review is a separate document
        # This is CRITICAL for TF-IDF to work correctly!
        corpus = positive_reviews + negative_reviews
        labels = [1] * len(positive_reviews) + [0] * len(negative_reviews)  # 1=positive, 0=negative
        
        # Create TF-IDF vectorizer with configurable ngram_range
        if language == 'schinese':
            vectorizer = TfidfVectorizer(
                max_features=max_features,
                min_df=min_df,
                ngram_range=ngram_range,  # Configurable: (1,1), (1,2), or (2,2)
                token_pattern=r'(?u)\b\w+\b',
                lowercase=False  # Chinese doesn't have case
            )
        else:
            vectorizer = TfidfVectorizer(
                max_features=max_features,
                min_df=min_df,
                ngram_range=ngram_range,  # Configurable: (1,1), (1,2), or (2,2)
                token_pattern=r'(?u)\b\w+\b',
                lowercase=True
            )
        
        # Fit and transform the entire corpus
        tfidf_matrix = vectorizer.fit_transform(corpus)
        feature_names = vectorizer.get_feature_names_out()
        
        # Calculate average TF-IDF scores for each sentiment group
        # Positive reviews: indices 0 to len(positive_reviews)-1
        # Negative reviews: indices len(positive_reviews) to end
        positive_indices = list(range(len(positive_reviews)))
        negative_indices = list(range(len(positive_reviews), len(corpus)))
        
        # Average TF-IDF across all positive reviews
        positive_tfidf_avg = tfidf_matrix[positive_indices].mean(axis=0).A1
        
        # Average TF-IDF across all negative reviews
        negative_tfidf_avg = tfidf_matrix[negative_indices].mean(axis=0).A1
        
        # Calculate DISTINCTIVE scores (difference between groups)
        # Positive distinctive = terms more common in positive than negative
        positive_distinctive = positive_tfidf_avg - negative_tfidf_avg
        
        # Negative distinctive = terms more common in negative than positive
        negative_distinctive = negative_tfidf_avg - positive_tfidf_avg
        
        # Get top distinctive terms for each sentiment
        # Only include terms with positive distinctiveness (filter out negative scores)
        positive_terms = self._get_top_distinctive_terms(feature_names, positive_distinctive, top_n)
        negative_terms = self._get_top_distinctive_terms(feature_names, negative_distinctive, top_n)
        
        # Build results structure
        results = {
            'metadata': metadata,
            'game_name': game_name,
            'analysis_params': {
                'language': language,
                'top_n': top_n,
                'max_features': max_features,
                'min_df': min_df
            },
            'analysis_date': datetime.utcnow().isoformat(),
            'total_reviews': len(all_reviews),
            'positive_reviews_count': len(positive_reviews),
            'negative_reviews_count': len(negative_reviews),
            'positive_distinctive_terms': positive_terms,
            'negative_distinctive_terms': negative_terms
        }
        
        # Save analysis results to JSON file
        date_str = datetime.utcnow().strftime('%Y-%m-%d')
        filename = f"{appid}_{game_name.replace(' ', '_')}_{language}_tfidf_{date_str}.json"
        
        # Sanitize filename (remove invalid characters)
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        insights_folder = os.path.join(self.output_base_dir, 'insights')
        os.makedirs(insights_folder, exist_ok=True)
        filepath = os.path.join(insights_folder, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        
        results['saved_to'] = filepath
        
        return results
    
    def _get_top_terms(self, feature_names: List[str], tfidf_scores: List[float], 
                       top_n: int) -> List[Dict[str, Any]]:
        """
        Extract top N terms with highest TF-IDF scores.
        
        Args:
            feature_names: List of all feature (term) names
            tfidf_scores: TF-IDF scores for each feature
            top_n: Number of top terms to return
            
        Returns:
            List of dictionaries with 'term' and 'score' keys, sorted by score descending
        """
        # Pair terms with scores and sort
        term_scores = [(feature_names[i], tfidf_scores[i]) 
                      for i in range(len(feature_names))]
        term_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get top N and format
        top_terms = []
        for i, (term, score) in enumerate(term_scores[:top_n], 1):
            top_terms.append({
                'rank': i,
                'term': term,
                'score': round(float(score), 4)
            })
        
        return top_terms
    
    def _get_top_distinctive_terms(self, feature_names: List[str], 
                                   distinctive_scores: List[float], 
                                   top_n: int) -> List[Dict[str, Any]]:
        """
        Extract top N terms with highest DISTINCTIVE scores.
        
        Only includes terms where the distinctive score is positive
        (meaning they appear MORE in this group than the other).
        
        Args:
            feature_names: List of all feature (term) names
            distinctive_scores: Difference scores (group1_avg - group2_avg)
            top_n: Number of top terms to return
            
        Returns:
            List of dictionaries with 'term' and 'score' keys, sorted by distinctiveness
        """
        # Pair terms with scores and filter positive scores only
        term_scores = [(feature_names[i], distinctive_scores[i]) 
                      for i in range(len(feature_names))
                      if distinctive_scores[i] > 0]  # Only terms distinctive to THIS group
        
        # Sort by distinctiveness (highest positive difference first)
        term_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get top N and format
        top_terms = []
        for i, (term, score) in enumerate(term_scores[:top_n], 1):
            top_terms.append({
                'rank': i,
                'term': term,
                'score': round(float(score), 4)
            })
        
        return top_terms
