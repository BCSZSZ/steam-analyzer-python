"""
Tab modules for the Steam Review Analysis Tool.
Each tab is a self-contained module with its own UI and logic.
"""

from .data_collection_tab import DataCollectionTab
from .extreme_reviews_tab import ExtremeReviewsTab

__all__ = ['DataCollectionTab', 'ExtremeReviewsTab']
