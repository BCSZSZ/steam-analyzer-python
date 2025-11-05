"""
Steam Review Analysis Tool - Main Application
Multi-tab GUI for fetching, analyzing, and visualizing Steam review data.
"""

import tkinter as tk
from tkinter import ttk
import queue
import threading

# Import tab modules
from tabs.data_collection_tab import DataCollectionTab
from tabs.extreme_reviews_tab import ExtremeReviewsTab
from tabs.text_insights_tab import TextInsightsTab
from tabs.ngram_analysis_tab import NgramAnalysisTab
from tabs.tfidf_analysis_tab import TfidfAnalysisTab


class SteamReviewApp:
    """Main application class for Steam Review Analysis Tool."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Steam Review Analysis Tool")
        self.root.geometry("1400x750")
        
        # Shared state
        self.status_queue = queue.Queue()
        self.sort_by = None
        self.sort_reverse = False
        self.fetch_all_var = tk.BooleanVar(value=False)
        self.cancel_event = threading.Event()
        
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.data_collection_tab = DataCollectionTab(self.notebook, self)
        self.extreme_reviews_tab = ExtremeReviewsTab(self.notebook, self)
        self.text_insights_tab = TextInsightsTab(self.notebook, self)
        self.ngram_analysis_tab = NgramAnalysisTab(self.notebook, self)
        self.tfidf_analysis_tab = TfidfAnalysisTab(self.notebook, self)
        
        # Start queue processing
        self.process_queue()

    def process_queue(self):
        """Process messages from the status queue."""
        try:
            message = self.status_queue.get_nowait()
            if isinstance(message, dict):
                msg_type = message.get('type')
                if msg_type == 'report':
                    self.data_collection_tab.populate_table(message['data'])
                    self.data_collection_tab.update_info_display(message['metadata'])
                elif msg_type == 'done':
                    self.data_collection_tab.fetch_button.config(state=tk.NORMAL)
                    self.data_collection_tab.import_button.config(state=tk.NORMAL)
                    self.data_collection_tab.analyze_json_button.config(state=tk.NORMAL)
                    self.data_collection_tab.cancel_button.config(state=tk.DISABLED)
                    if not self.cancel_event.is_set():
                        self.data_collection_tab.status_label.config(text="Process finished.")
            else:
                self.data_collection_tab.status_label.config(text=message)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)


if __name__ == "__main__":
    root = tk.Tk()
    app = SteamReviewApp(root)
    root.mainloop()
