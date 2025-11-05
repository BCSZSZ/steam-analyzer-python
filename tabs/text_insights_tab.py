"""
Text Insights Dashboard Tab - unified view of text analysis results.

Combines N-gram analysis, TF-IDF analysis, and word cloud visualization
in a single dashboard for quick insights.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import threading

from .base_tab import BaseTab
from analyzers.ngram_analyzer import NgramAnalyzer
from analyzers.tfidf_analyzer import TfidfAnalyzer
from memory_utils import clear_tab_data, estimate_memory_usage


class TextInsightsTab(BaseTab):
    """
    Dashboard tab combining multiple text analysis features.
    
    Provides:
    - Quick overview of top n-grams
    - Key distinctive terms from TF-IDF
    - Word cloud visualization (future)
    - Language selection affecting all panels
    """
    
    def __init__(self, frame, app):
        super().__init__(frame, app)
        self.ngram_analyzer = NgramAnalyzer()
        self.tfidf_analyzer = TfidfAnalyzer()
        self.current_data = None
        self.is_analyzing = False
    
    def get_tab_title(self) -> str:
        return "Text Insights"
    
    def create_ui(self):
        """Create all UI elements for the text insights dashboard."""
        # Dataset Information section (common across text analysis tabs)
        info_frame = ttk.LabelFrame(self.frame, text="Dataset Information", padding="10")
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.info_text = tk.StringVar(value="No data loaded")
        ttk.Label(info_frame, textvariable=self.info_text, justify=tk.LEFT).pack(anchor=tk.W)
        
        # Control panel for loading data and settings
        control_frame = ttk.Frame(self.frame, padding="10")
        control_frame.pack(fill=tk.X)
        
        ttk.Label(control_frame, text="Text Insights Dashboard", font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Load Raw JSON", command=self.load_raw_json).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Refresh Analysis", command=self.refresh_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Clear Data", command=self.clear_data).pack(side=tk.LEFT, padx=5)
        
        # Language selection
        ttk.Label(control_frame, text="Language:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(20, 5))
        
        self.language_var = tk.StringVar(value="english")
        ttk.Radiobutton(control_frame, text="English", variable=self.language_var, 
                       value="english", command=self.on_language_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(control_frame, text="Chinese", variable=self.language_var, 
                       value="schinese", command=self.on_language_change).pack(side=tk.LEFT, padx=5)
        
        # Main dashboard area with three panels
        dashboard_frame = ttk.Frame(self.frame, padding="10")
        dashboard_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Configure grid layout for 3 panels
        dashboard_frame.columnconfigure(0, weight=1)
        dashboard_frame.columnconfigure(1, weight=1)
        dashboard_frame.rowconfigure(0, weight=1)
        dashboard_frame.rowconfigure(1, weight=1)
        
        # Panel 1: Top N-grams Quick View
        ngram_panel = ttk.LabelFrame(dashboard_frame, text="🔤 Top 10 Bigrams", padding="10")
        ngram_panel.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        
        self.ngram_text = tk.Text(ngram_panel, height=10, wrap=tk.WORD, font=('Arial', 9))
        self.ngram_text.pack(fill=tk.BOTH, expand=True)
        self.ngram_text.insert('1.0', 'Load data to see top bigrams...')
        self.ngram_text.config(state=tk.DISABLED)
        
        ngram_btn_frame = ttk.Frame(ngram_panel)
        ngram_btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(ngram_btn_frame, text="Deep Dive →", command=self.open_ngram_tab).pack(side=tk.RIGHT)
        
        # Panel 2: Key Distinctive Terms
        tfidf_panel = ttk.LabelFrame(dashboard_frame, text="⭐ Distinctive Terms", padding="10")
        tfidf_panel.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        
        # Split into positive and negative columns
        tfidf_container = ttk.Frame(tfidf_panel)
        tfidf_container.pack(fill=tk.BOTH, expand=True)
        
        pos_frame = ttk.Frame(tfidf_container)
        pos_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        ttk.Label(pos_frame, text="Positive", font=('Arial', 9, 'bold'), foreground='green').pack()
        self.pos_terms_text = tk.Text(pos_frame, height=8, wrap=tk.WORD, font=('Arial', 9))
        self.pos_terms_text.pack(fill=tk.BOTH, expand=True)
        self.pos_terms_text.insert('1.0', 'Load data...')
        self.pos_terms_text.config(state=tk.DISABLED)
        
        neg_frame = ttk.Frame(tfidf_container)
        neg_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        ttk.Label(neg_frame, text="Negative", font=('Arial', 9, 'bold'), foreground='red').pack()
        self.neg_terms_text = tk.Text(neg_frame, height=8, wrap=tk.WORD, font=('Arial', 9))
        self.neg_terms_text.pack(fill=tk.BOTH, expand=True)
        self.neg_terms_text.insert('1.0', 'Load data...')
        self.neg_terms_text.config(state=tk.DISABLED)
        
        tfidf_btn_frame = ttk.Frame(tfidf_panel)
        tfidf_btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(tfidf_btn_frame, text="Deep Dive →", command=self.open_tfidf_tab).pack(side=tk.RIGHT)
        
        # Panel 3: Word Cloud Visualization (placeholder for future)
        wordcloud_panel = ttk.LabelFrame(dashboard_frame, text="☁️ Word Cloud", padding="10")
        wordcloud_panel.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)
        
        self.wordcloud_label = ttk.Label(
            wordcloud_panel, 
            text="Word cloud visualization will be available in Phase 4\n\nThis panel will display visual word clouds for positive and negative reviews",
            font=('Arial', 10),
            foreground='gray',
            justify=tk.CENTER
        )
        self.wordcloud_label.pack(expand=True)
        
        wordcloud_btn_frame = ttk.Frame(wordcloud_panel)
        wordcloud_btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(wordcloud_btn_frame, text="Generate Word Cloud", command=self.generate_wordcloud, state=tk.DISABLED).pack(side=tk.RIGHT)
    
    def load_raw_json(self):
        """Load raw review JSON file for analysis."""
        filepath = filedialog.askopenfilename(
            title="Select Raw Review JSON File",
            filetypes=[("JSON Files", "*.json")],
            initialdir="./data/raw"
        )
        if not filepath:
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Store data for analysis
            self.current_data = json_data
            
            # Update info display
            metadata = json_data.get('metadata', {})
            total_reviews = len(json_data.get('reviews', []))
            appid = metadata.get('appid', 'N/A')
            
            info_text = f"Loaded: {total_reviews:,} reviews | App ID: {appid} | Ready for analysis"
            self.info_text.set(info_text)
            
            # Trigger initial analysis
            self.refresh_analysis()
            
            messagebox.showinfo("Success", f"Loaded {total_reviews:,} reviews successfully!")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")
            self.current_data = None
    
    def refresh_analysis(self):
        """Refresh all analysis panels with current data and settings."""
        if self.current_data is None:
            messagebox.showwarning("No Data", "Please load data first.")
            return
        
        if self.is_analyzing:
            messagebox.showwarning("Busy", "Analysis already in progress.")
            return
        
        # Run analysis in background thread
        thread = threading.Thread(target=self._run_dashboard_analysis, daemon=True)
        thread.start()
    
    def _run_dashboard_analysis(self):
        """Run quick analysis for dashboard (background thread)."""
        self.is_analyzing = True
        
        try:
            language = self.language_var.get()
            
            # Update UI to show loading state
            self.frame.after(0, lambda: self._set_loading_state(True))
            
            # Run N-gram analysis (bigrams only, top 10)
            ngram_results = self.ngram_analyzer.analyze(
                self.current_data,
                language=language,
                sentiment='both',
                ngram_size=2,
                min_frequency=2,
                top_n=10
            )
            
            # Run TF-IDF analysis (bigrams, top 5 per sentiment)
            tfidf_results = self.tfidf_analyzer.analyze(
                self.current_data,
                language=language,
                top_n=5,
                ngram_range=(2, 2)
            )
            
            # Update UI with results
            self.frame.after(0, lambda: self._display_results(ngram_results, tfidf_results))
            
        except Exception as e:
            self.frame.after(0, lambda: messagebox.showerror("Error", f"Analysis failed:\n{str(e)}"))
        finally:
            self.is_analyzing = False
            self.frame.after(0, lambda: self._set_loading_state(False))
    
    def _set_loading_state(self, loading: bool):
        """Show/hide loading state in UI."""
        if loading:
            self._update_text_widget(self.ngram_text, "⏳ Analyzing bigrams...")
            self._update_text_widget(self.pos_terms_text, "⏳ Analyzing...")
            self._update_text_widget(self.neg_terms_text, "⏳ Analyzing...")
        # Loading off state handled by _display_results
    
    def _display_results(self, ngram_results, tfidf_results):
        """Display analysis results in dashboard panels."""
        # Update N-gram panel
        if ngram_results and ngram_results.get('top_ngrams'):
            lines = []
            for i, item in enumerate(ngram_results['top_ngrams'], 1):
                ngram = item['ngram']
                count = item['count']
                pct = item['percentage']
                lines.append(f"{i}. {ngram} ({count:,} times, {pct:.1f}%)")
            
            content = "\n".join(lines)
            self._update_text_widget(self.ngram_text, content)
        else:
            self._update_text_widget(self.ngram_text, "No bigrams found for selected language.")
        
        # Update TF-IDF panels
        if tfidf_results:
            # Positive terms
            pos_terms = tfidf_results.get('positive_distinctive_terms', [])
            if pos_terms:
                lines = []
                for i, item in enumerate(pos_terms, 1):
                    term = item['term']
                    score = item['score']
                    lines.append(f"{i}. {term} ({score:.3f})")
                pos_content = "\n".join(lines)
            else:
                pos_content = "No distinctive positive terms found."
            
            self._update_text_widget(self.pos_terms_text, pos_content)
            
            # Negative terms
            neg_terms = tfidf_results.get('negative_distinctive_terms', [])
            if neg_terms:
                lines = []
                for i, item in enumerate(neg_terms, 1):
                    term = item['term']
                    score = item['score']
                    lines.append(f"{i}. {term} ({score:.3f})")
                neg_content = "\n".join(lines)
            else:
                neg_content = "No distinctive negative terms found."
            
            self._update_text_widget(self.neg_terms_text, neg_content)
        else:
            self._update_text_widget(self.pos_terms_text, "Insufficient data for TF-IDF analysis.")
            self._update_text_widget(self.neg_terms_text, "Insufficient data for TF-IDF analysis.")
    
    def _update_text_widget(self, widget, content: str):
        """Helper to update a text widget safely."""
        widget.config(state=tk.NORMAL)
        widget.delete('1.0', tk.END)
        widget.insert('1.0', content)
        widget.config(state=tk.DISABLED)
    
    def on_language_change(self):
        """Handle language selection change."""
        if hasattr(self, 'current_data') and self.current_data is not None:
            self.refresh_analysis()
    
    def open_ngram_tab(self):
        """Navigate to N-gram Analysis tab for detailed view."""
        # Switch to N-gram Analysis tab (index 3, after Data Collection, Extreme Reviews, Text Insights)
        self.app.notebook.select(3)
    
    def open_tfidf_tab(self):
        """Navigate to TF-IDF Analysis tab for detailed view."""
        # Switch to TF-IDF Analysis tab (index 4)
        self.app.notebook.select(4)
    
    def clear_data(self):
        """Clear loaded data and free memory."""
        if clear_tab_data(self):
            self.info_text.set("No data loaded")
            self._update_text_widget(self.ngram_text, "Load data to see top bigrams...")
            self._update_text_widget(self.pos_terms_text, "Load data...")
            self._update_text_widget(self.neg_terms_text, "Load data...")
            messagebox.showinfo("Memory Freed", "Data cleared successfully. Memory has been freed.")
        else:
            messagebox.showinfo("No Data", "No data loaded to clear.")
    
    def generate_wordcloud(self):
        """Generate word cloud visualization."""
        # TODO: Implement word cloud generation (Phase 4)
        messagebox.showinfo("Coming Soon", "Word cloud generation will be implemented in Phase 4!")
