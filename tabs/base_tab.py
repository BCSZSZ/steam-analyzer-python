"""
Base tab class with common functionality for all tabs.
"""

import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod
from datetime import datetime


class BaseTab(ABC):
    """Abstract base class for all tab implementations."""
    
    def __init__(self, notebook: ttk.Notebook, app_instance):
        """
        Initialize the tab.
        
        Args:
            notebook: The parent notebook widget
            app_instance: Reference to the main app instance for shared resources
        """
        self.notebook = notebook
        self.app = app_instance
        self.frame = ttk.Frame(notebook)
        
        # Date filter entries (initialized by create_date_filter)
        self.start_date_entry = None
        self.end_date_entry = None
        
        # Create the tab content
        self.create_ui()
        
        # Add to notebook
        notebook.add(self.frame, text=self.get_tab_title())
    
    @abstractmethod
    def get_tab_title(self) -> str:
        """Return the title to display on the tab."""
        pass
    
    @abstractmethod
    def create_ui(self):
        """Create the UI elements for this tab."""
        pass
    
    def create_date_filter(self, parent_frame):
        """
        Add date range filter UI to a parent frame.
        
        Args:
            parent_frame: The ttk.Frame to add date filter widgets into.
        """
        date_frame = ttk.Frame(parent_frame)
        date_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(date_frame, text="Date Range:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(date_frame, text="From:").pack(side=tk.LEFT, padx=(5, 2))
        self.start_date_entry = ttk.Entry(date_frame, width=12)
        self.start_date_entry.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(date_frame, text="To:").pack(side=tk.LEFT, padx=(10, 2))
        self.end_date_entry = ttk.Entry(date_frame, width=12)
        self.end_date_entry.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(date_frame, text="(YYYY-MM-DD, leave empty for no limit)", foreground='gray').pack(side=tk.LEFT, padx=5)
    
    def get_date_filtered_data(self, json_data):
        """
        Return a copy of json_data with reviews filtered by the date range.
        
        If no date filter entries exist or both are empty, returns the original data unchanged.
        
        Args:
            json_data: Dictionary with 'metadata' and 'reviews' keys.
            
        Returns:
            json_data (original or filtered copy).
            
        Raises:
            ValueError: If date format is invalid.
        """
        if self.start_date_entry is None and self.end_date_entry is None:
            return json_data
        
        start_str = self.start_date_entry.get().strip() if self.start_date_entry else ""
        end_str = self.end_date_entry.get().strip() if self.end_date_entry else ""
        
        if not start_str and not end_str:
            return json_data
        
        # Parse dates
        start_ts = 0
        end_ts = float('inf')
        
        if start_str:
            start_ts = datetime.strptime(start_str, "%Y-%m-%d").timestamp()
        if end_str:
            # End date is inclusive: set to end of day (23:59:59)
            end_ts = datetime.strptime(end_str, "%Y-%m-%d").timestamp() + 86399
        
        reviews = json_data.get('reviews', [])
        filtered = [r for r in reviews if start_ts <= r.get('timestamp_created', 0) <= end_ts]
        
        # Return a new dict with filtered reviews (preserve metadata)
        return {**json_data, 'reviews': filtered}
