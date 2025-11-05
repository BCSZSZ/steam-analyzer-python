"""
Memory Management Improvements for Steam Analyzer

PROBLEM IDENTIFIED:
- Each tab loads and stores full 300MB+ JSON files independently
- 3 tabs with 300MB data = ~1.3GB RAM usage
- No cleanup mechanism when switching tabs

SOLUTION IMPLEMENTED:
1. Add "Clear Data" button to each analysis tab
2. Explicit memory cleanup with garbage collection
3. User can free memory when done with a dataset

FUTURE IMPROVEMENTS (if needed):
1. Centralized data store in main app (shared reference)
2. Automatic cleanup when loading new data
3. Lazy loading with caching
"""

import gc


def clear_tab_data(tab_instance):
    """
    Clear loaded data from a tab and trigger garbage collection.
    
    Args:
        tab_instance: Tab object with current_data attribute
    
    Returns:
        bool: True if data was cleared, False if no data to clear
    """
    if hasattr(tab_instance, 'current_data') and tab_instance.current_data is not None:
        # Clear the reference
        tab_instance.current_data = None
        
        # Trigger garbage collection to free memory immediately
        gc.collect()
        
        return True
    return False


def estimate_memory_usage(json_data):
    """
    Estimate memory usage of loaded JSON data.
    
    Args:
        json_data: Loaded JSON dictionary
    
    Returns:
        tuple: (reviews_count, estimated_mb)
    """
    if not json_data:
        return 0, 0
    
    reviews = json_data.get('reviews', [])
    reviews_count = len(reviews)
    
    # Rough estimation: ~1.5KB per review on average
    estimated_mb = (reviews_count * 1.5) / 1024
    
    return reviews_count, estimated_mb
