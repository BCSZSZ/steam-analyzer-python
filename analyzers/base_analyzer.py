"""
Base analyzer class for all review analyzers.
Provides common functionality for saving outputs and accessing metadata.
"""

from abc import ABC, abstractmethod
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional


class BaseAnalyzer(ABC):
    """Abstract base class for all analyzers."""
    
    def __init__(self, output_base_dir: str = 'data/processed'):
        """
        Initialize the analyzer.
        
        Args:
            output_base_dir: Base directory for output files
        """
        self.output_base_dir = output_base_dir
    
    @abstractmethod
    def analyze(self, json_data: Dict[str, Any], **kwargs) -> Any:
        """
        Perform analysis on the review data.
        
        Args:
            json_data: Dictionary containing 'metadata' and 'reviews' keys
            **kwargs: Additional analyzer-specific parameters
            
        Returns:
            Analysis results (format depends on the analyzer)
        """
        pass
    
    def save_output(self, data: Any, subfolder: str, filename: str) -> str:
        """
        Save analysis results to a file.
        
        Args:
            data: Data to save (will be JSON serialized)
            subfolder: Subfolder within output_base_dir
            filename: Name of the output file
            
        Returns:
            Full path to the saved file
        """
        output_dir = os.path.join(self.output_base_dir, subfolder)
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        return filepath
    
    def get_metadata(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from review data.
        
        Args:
            json_data: Review data dictionary
            
        Returns:
            Metadata dictionary
        """
        return json_data.get('metadata', {})
    
    def get_reviews(self, json_data: Dict[str, Any]) -> list:
        """
        Extract reviews list from review data.
        
        Args:
            json_data: Review data dictionary
            
        Returns:
            List of review dictionaries
        """
        return json_data.get('reviews', [])
