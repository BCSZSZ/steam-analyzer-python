"""
Base tab class with common functionality for all tabs.
"""

import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod


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
