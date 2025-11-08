"""
Timeline Analyzer - analyzes review sentiment and volume over time.

Generates time-series data for visualizing:
- Rolling average positive rate (configurable window)
- Cumulative positive rate evolution
- Review volume by date
"""

from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any
from .base_analyzer import BaseAnalyzer


class TimelineAnalyzer(BaseAnalyzer):
    """
    Analyzes review data over time to generate timeline visualizations.
    
    Features:
    - Daily aggregation of reviews
    - Rolling window average calculation
    - Cumulative positive rate tracking
    - Language-specific filtering
    """
    
    def __init__(self):
        """Initialize timeline analyzer."""
        super().__init__()
    
    def analyze(self, json_data: Dict[str, Any], language: str = 'all', 
                rolling_window: int = None) -> Dict[str, Any]:
        """
        Analyze review timeline data.
        
        Args:
            json_data: Raw review data from Steam API
            language: Language filter ('all' or specific language code)
            rolling_window: Number of days for rolling average (None = auto-determine, default)
        
        Returns:
            Dictionary with timeline data and metadata
        """
        reviews = self.get_reviews(json_data)
        metadata = self.get_metadata(json_data)
        
        if not reviews:
            return {'error': 'No reviews found in data'}
        
        # Filter by language if specified
        if language != 'all':
            reviews = [r for r in reviews if r.get('language') == language]
        
        if not reviews:
            return {'error': f'No reviews found for language: {language}'}
        
        # Group reviews by date
        daily_data = self._group_by_date(reviews)
        
        # Auto-determine rolling window if not specified
        if rolling_window is None or rolling_window == 0:
            rolling_window = self._auto_determine_window(daily_data)
        
        # Calculate cumulative metrics
        timeline_data = self._calculate_timeline_metrics(
            daily_data, 
            rolling_window=rolling_window
        )
        
        # Calculate overall statistics
        total_positive = sum(1 for r in reviews if r.get('voted_up'))
        total_reviews = len(reviews)
        overall_rate = (total_positive / total_reviews * 100) if total_reviews > 0 else 0
        
        results = {
            'metadata': {
                'total_reviews': total_reviews,
                'total_positive': total_positive,
                'total_negative': total_reviews - total_positive,
                'overall_positive_rate': overall_rate,
                'language': language,
                'rolling_window': rolling_window,
                'date_range': {
                    'start': min(daily_data.keys()) if daily_data else None,
                    'end': max(daily_data.keys()) if daily_data else None
                },
                'analysis_date': datetime.now().isoformat()
            },
            'timeline': timeline_data
        }
        
        return results
    
    def _auto_determine_window(self, daily_data: Dict[str, Dict[str, int]]) -> int:
        """
        Auto-determine rolling window based on date range.
        
        Logic:
        - < 30 days: 3-day window
        - 30-90 days: 7-day window
        - 90-180 days: 14-day window
        - 180-365 days: 30-day window
        - > 365 days: 60-day window
        
        Args:
            daily_data: Dictionary of daily review statistics
        
        Returns:
            Recommended rolling window size in days
        """
        if not daily_data:
            return 7  # Default fallback
        
        sorted_dates = sorted(daily_data.keys())
        start_date = datetime.strptime(sorted_dates[0], '%Y-%m-%d')
        end_date = datetime.strptime(sorted_dates[-1], '%Y-%m-%d')
        
        timespan_days = (end_date - start_date).days
        
        if timespan_days < 30:
            return 3
        elif timespan_days < 90:
            return 7
        elif timespan_days < 180:
            return 14
        elif timespan_days < 365:
            return 30
        else:
            return 60
    
    def _group_by_date(self, reviews: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """
        Group reviews by calendar date.
        
        Args:
            reviews: List of review dictionaries
        
        Returns:
            Dictionary mapping date string to daily statistics
        """
        daily_data = defaultdict(lambda: {'positive': 0, 'negative': 0, 'total': 0})
        
        for review in reviews:
            timestamp = review.get('timestamp_created', 0)
            if timestamp <= 0:
                continue
            
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            voted_up = review.get('voted_up', False)
            
            daily_data[date_str]['total'] += 1
            if voted_up:
                daily_data[date_str]['positive'] += 1
            else:
                daily_data[date_str]['negative'] += 1
        
        return dict(daily_data)
    
    def _calculate_timeline_metrics(self, daily_data: Dict[str, Dict[str, int]], 
                                    rolling_window: int) -> List[Dict[str, Any]]:
        """
        Calculate timeline metrics including rolling averages and cumulative rates.
        
        Args:
            daily_data: Dictionary of daily review statistics
            rolling_window: Number of days for rolling average window
        
        Returns:
            List of daily data points with calculated metrics
        """
        if not daily_data:
            return []
        
        # Sort dates chronologically
        sorted_dates = sorted(daily_data.keys())
        
        # Fill gaps in date range (days with no reviews)
        start_date = datetime.strptime(sorted_dates[0], '%Y-%m-%d')
        end_date = datetime.strptime(sorted_dates[-1], '%Y-%m-%d')
        
        all_dates = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            all_dates.append(date_str)
            current_date += timedelta(days=1)
        
        # Calculate cumulative and rolling metrics
        timeline = []
        cumulative_positive = 0
        cumulative_total = 0
        previous_rolling_rate = None  # Failover for division by zero
        
        for i, date_str in enumerate(all_dates):
            day_data = daily_data.get(date_str, {'positive': 0, 'negative': 0, 'total': 0})
            
            # Update cumulative counts
            cumulative_positive += day_data['positive']
            cumulative_total += day_data['total']
            
            # Calculate cumulative positive rate
            cumulative_rate = (cumulative_positive / cumulative_total * 100) if cumulative_total > 0 else None
            
            # Calculate rolling average (look back N days)
            rolling_positive = 0
            rolling_total = 0
            
            for j in range(max(0, i - rolling_window + 1), i + 1):
                past_date = all_dates[j]
                past_data = daily_data.get(past_date, {'positive': 0, 'negative': 0, 'total': 0})
                rolling_positive += past_data['positive']
                rolling_total += past_data['total']
            
            # Calculate rolling rate with failover
            if rolling_total > 0:
                rolling_rate = (rolling_positive / rolling_total * 100)
                previous_rolling_rate = rolling_rate  # Save for future failover
            else:
                # Failover: use previous day's rolling rate if available
                rolling_rate = previous_rolling_rate
            
            # Daily positive rate
            daily_rate = (day_data['positive'] / day_data['total'] * 100) if day_data['total'] > 0 else None
            
            timeline.append({
                'date': date_str,
                'daily_total': day_data['total'],
                'daily_positive': day_data['positive'],
                'daily_negative': day_data['negative'],
                'daily_rate': daily_rate,
                'rolling_rate': rolling_rate,
                'rolling_window_total': rolling_total,
                'cumulative_total': cumulative_total,
                'cumulative_positive': cumulative_positive,
                'cumulative_rate': cumulative_rate
            })
        
        return timeline
    
    def get_available_languages(self, json_data: Dict[str, Any]) -> List[str]:
        """
        Get list of languages present in the review data.
        
        Args:
            json_data: Raw review data
        
        Returns:
            Sorted list of language codes
        """
        reviews = self.get_reviews(json_data)
        languages = set(r.get('language') for r in reviews if r.get('language'))
        return sorted(list(languages))
    
    def save_analysis(self, results: Dict[str, Any], appid: int, 
                     game_name: str, language: str) -> str:
        """
        Save timeline analysis results to JSON.
        
        Args:
            results: Analysis results dictionary
            appid: Steam App ID
            game_name: Game title
            language: Language filter used
        
        Returns:
            Path to saved file
        """
        date_str = datetime.now().strftime('%Y-%m-%d')
        rolling_window = results['metadata'].get('rolling_window', 7)
        
        filename = f"{appid}_{game_name}_{language}_timeline_w{rolling_window}_{date_str}.json"
        
        return self.save_output(results, 'insights', filename)
