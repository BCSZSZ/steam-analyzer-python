"""
TF-IDF Analysis Tab - identifies distinctive terms in reviews.

Uses Term Frequency-Inverse Document Frequency to find terms that
strongly characterize positive vs negative reviews in each language.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
import threading
from PIL import Image, ImageTk

from .base_tab import BaseTab
from analyzers.tfidf_analyzer import TfidfAnalyzer
from analyzers.wordcloud_generator import WordCloudGenerator
from memory_utils import clear_tab_data


class TfidfAnalysisTab(BaseTab):
    """
    Tab for TF-IDF analysis of review text.
    
    Provides:
    - Language selection (English/Chinese)
    - Configurable number of top terms
    - Side-by-side comparison of positive vs negative distinctive terms
    - Term detail view with scores and frequencies
    """
    
    def get_tab_title(self) -> str:
        return "TF-IDF Analysis"
    
    def create_ui(self):
        """Create all UI elements for the TF-IDF analysis tab."""
        # Dataset Information section (common across text analysis tabs)
        info_frame = ttk.LabelFrame(self.frame, text="Dataset Information", padding="10")
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.info_text = tk.StringVar(value="No data loaded")
        ttk.Label(info_frame, textvariable=self.info_text, justify=tk.LEFT).pack(anchor=tk.W)
        
        # Control panel for loading data and settings
        control_frame = ttk.Frame(self.frame, padding="10")
        control_frame.pack(fill=tk.X)
        
        ttk.Label(control_frame, text="TF-IDF Analysis", font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Load Raw JSON", command=self.load_raw_json).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Load Saved Results", command=self.load_saved_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Clear Data", command=self.clear_data).pack(side=tk.LEFT, padx=5)
        
        # Analysis settings panel
        settings_frame = ttk.LabelFrame(self.frame, text="Analysis Settings", padding="10")
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Language selection
        lang_frame = ttk.Frame(settings_frame)
        lang_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(lang_frame, text="Language:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.language_var = tk.StringVar(value="english")
        ttk.Radiobutton(lang_frame, text="English", variable=self.language_var, value="english").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(lang_frame, text="Chinese", variable=self.language_var, value="schinese").pack(side=tk.LEFT, padx=10)
        
        # N-gram range selection
        ngram_frame = ttk.Frame(settings_frame)
        ngram_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(ngram_frame, text="N-gram Range:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.ngram_var = tk.StringVar(value="2,2")
        ttk.Radiobutton(ngram_frame, text="Bigrams (2-word phrases)", variable=self.ngram_var, value="2,2").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(ngram_frame, text="Trigrams (3-word phrases)", variable=self.ngram_var, value="3,3").pack(side=tk.LEFT, padx=10)
        
        # Top N terms selection
        topn_frame = ttk.Frame(settings_frame)
        topn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(topn_frame, text="Top N Terms:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.top_n_entry = ttk.Entry(topn_frame, width=10)
        self.top_n_entry.pack(side=tk.LEFT, padx=5)
        self.top_n_entry.insert(0, "50")
        
        ttk.Button(topn_frame, text="Analyze", command=self.run_analysis).pack(side=tk.LEFT, padx=20)
        self.export_button = ttk.Button(topn_frame, text="Export Results", command=self.export_results, state=tk.DISABLED)
        self.export_button.pack(side=tk.LEFT, padx=5)
        
        # Results display area - side by side comparison
        results_container = ttk.Frame(self.frame, padding="10")
        results_container.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
        
        # Left panel: Positive distinctive terms
        positive_frame = ttk.LabelFrame(results_container, text="Positive Distinctive Terms", padding="10")
        positive_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        columns_pos = ('rank', 'term', 'score')
        self.positive_tree = ttk.Treeview(positive_frame, columns=columns_pos, show='headings', height=12)
        
        self.positive_tree.heading('rank', text='Rank')
        self.positive_tree.heading('term', text='Term')
        self.positive_tree.heading('score', text='TF-IDF Score')
        
        self.positive_tree.column('rank', width=60, anchor=tk.CENTER)
        self.positive_tree.column('term', width=200, anchor=tk.W)
        self.positive_tree.column('score', width=120, anchor=tk.CENTER)
        
        self.positive_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        pos_scrollbar = ttk.Scrollbar(positive_frame, orient=tk.VERTICAL, command=self.positive_tree.yview)
        self.positive_tree.configure(yscroll=pos_scrollbar.set)
        pos_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right panel: Negative distinctive terms
        negative_frame = ttk.LabelFrame(results_container, text="Negative Distinctive Terms", padding="10")
        negative_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        columns_neg = ('rank', 'term', 'score')
        self.negative_tree = ttk.Treeview(negative_frame, columns=columns_neg, show='headings', height=12)
        
        self.negative_tree.heading('rank', text='Rank')
        self.negative_tree.heading('term', text='Term')
        self.negative_tree.heading('score', text='TF-IDF Score')
        
        self.negative_tree.column('rank', width=60, anchor=tk.CENTER)
        self.negative_tree.column('term', width=200, anchor=tk.W)
        self.negative_tree.column('score', width=120, anchor=tk.CENTER)
        
        self.negative_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        neg_scrollbar = ttk.Scrollbar(negative_frame, orient=tk.VERTICAL, command=self.negative_tree.yview)
        self.negative_tree.configure(yscroll=neg_scrollbar.set)
        neg_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Placeholder messages
        self.positive_tree.insert('', tk.END, values=('', 'Load data and click "Analyze"', ''))
        self.negative_tree.insert('', tk.END, values=('', 'Load data and click "Analyze"', ''))
        
        # Store current results for export
        self.current_results = None
        
        # Word Cloud Section (Always visible)
        self.wordcloud_generator = WordCloudGenerator()
        self.positive_wordcloud_image = None
        self.negative_wordcloud_image = None
        
        # Word cloud frame
        wordcloud_frame = ttk.LabelFrame(self.frame, text="Word Cloud Visualization", padding="10")
        wordcloud_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
        
        # Generate button
        btn_frame = ttk.Frame(wordcloud_frame)
        btn_frame.pack(pady=5)
        
        self.generate_wordclouds_btn = ttk.Button(
            btn_frame, 
            text="Generate Word Clouds", 
            command=self.generate_wordclouds,
            state=tk.DISABLED
        )
        self.generate_wordclouds_btn.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.wordcloud_status_label = ttk.Label(
            wordcloud_frame, 
            text="Load data and analyze to generate word clouds (opens in popups with save buttons)"
        )
        self.wordcloud_status_label.pack(pady=10)
    
    def generate_wordclouds(self):
        """Generate and display dual word clouds in popup windows."""
        if not self.current_results:
            messagebox.showwarning("No Data", "Please run analysis first.")
            return
        
        try:
            positive_terms = self.current_results.get('positive_distinctive_terms', [])
            negative_terms = self.current_results.get('negative_distinctive_terms', [])
            
            if not positive_terms and not negative_terms:
                messagebox.showwarning("No Data", "No terms available for word cloud")
                return
            
            # Get language from current results
            params = self.current_results.get('analysis_params', {})
            language = params.get('language', 'english')
            
            # Show generating message
            self.wordcloud_status_label.config(text="Generating word clouds...")
            self.frame.update()
            
            # Generate both word clouds with language parameter
            pos_image, neg_image = self.wordcloud_generator.generate_dual_tfidf(
                positive_terms,
                negative_terms,
                max_words=50,
                language=language
            )
            
            # Store images and show in single popup
            if pos_image or neg_image:
                self.positive_wordcloud_image = pos_image
                self.negative_wordcloud_image = neg_image
                self._show_dual_wordcloud_popup(pos_image, neg_image)
                self.wordcloud_status_label.config(text="Word clouds generated! (Shown in popup with save buttons)")
            else:
                self.wordcloud_status_label.config(text="No terms available for word clouds")
        
        except Exception as e:
            self.wordcloud_status_label.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to generate word clouds:\n{str(e)}")
    
    def _show_dual_wordcloud_popup(self, pos_image, neg_image):
        """Show both word clouds side by side in a single popup window."""
        popup = tk.Toplevel(self.frame)
        popup.title("TF-IDF Distinctive Terms - Word Clouds")
        popup.geometry("1300x700")
        
        # Button frame at top
        btn_frame = ttk.Frame(popup)
        btn_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        ttk.Label(btn_frame, text="TF-IDF Distinctive Terms", font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        
        # Save buttons
        if pos_image:
            save_pos_btn = ttk.Button(
                btn_frame,
                text="Save Positive",
                command=lambda: self._save_popup_image(pos_image, 'positive')
            )
            save_pos_btn.pack(side=tk.RIGHT, padx=5)
        
        if neg_image:
            save_neg_btn = ttk.Button(
                btn_frame,
                text="Save Negative",
                command=lambda: self._save_popup_image(neg_image, 'negative')
            )
            save_neg_btn.pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(btn_frame, text="(Right-click images to save)", foreground='gray').pack(side=tk.RIGHT, padx=10)
        
        # Main container for both word clouds
        main_container = ttk.Frame(popup)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left side - Positive word cloud
        if pos_image:
            left_frame = ttk.LabelFrame(main_container, text="Positive Distinctive Terms", padding="5")
            left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
            
            left_canvas = tk.Canvas(left_frame, bg='white')
            left_canvas.pack(fill=tk.BOTH, expand=True)
            
            pos_photo = ImageTk.PhotoImage(pos_image)
            left_canvas.create_image(0, 0, anchor=tk.NW, image=pos_photo)
            left_canvas.image = pos_photo  # Keep reference
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))
            
            # Right-click to save
            left_canvas.bind("<Button-3>", lambda e: self._save_popup_image(pos_image, 'positive'))
        
        # Right side - Negative word cloud
        if neg_image:
            right_frame = ttk.LabelFrame(main_container, text="Negative Distinctive Terms", padding="5")
            right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
            
            right_canvas = tk.Canvas(right_frame, bg='white')
            right_canvas.pack(fill=tk.BOTH, expand=True)
            
            neg_photo = ImageTk.PhotoImage(neg_image)
            right_canvas.create_image(0, 0, anchor=tk.NW, image=neg_photo)
            right_canvas.image = neg_photo  # Keep reference
            right_canvas.configure(scrollregion=right_canvas.bbox("all"))
            
            # Right-click to save
            right_canvas.bind("<Button-3>", lambda e: self._save_popup_image(neg_image, 'negative'))
    
    def _save_popup_image(self, image, sentiment):
        """Save word cloud image from popup."""
        filepath = filedialog.asksaveasfilename(
            title=f"Save {sentiment.capitalize()} Word Cloud",
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            initialdir="./data/processed"
        )
        
        if filepath:
            try:
                success = self.wordcloud_generator.save_image(image, filepath)
                if success:
                    messagebox.showinfo("Success", f"Word cloud saved to:\n{filepath}")
                else:
                    messagebox.showerror("Error", "Failed to save word cloud image.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image:\n{e}")
    
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
            
            messagebox.showinfo("Success", f"Loaded {total_reviews:,} reviews successfully!")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")
            self.current_data = None
    
    def load_saved_results(self):
        """Load previously saved TF-IDF analysis results."""
        filepath = filedialog.askopenfilename(
            title="Select TF-IDF Analysis Results",
            filetypes=[("JSON Files", "*.json")],
            initialdir="./data/processed/insights"
        )
        if not filepath:
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # Store results
            self.current_results = results
            
            # Update info display
            game_name = results.get('game_name', 'Unknown')
            total_reviews = results.get('total_reviews', 0)
            pos_count = results.get('positive_reviews_count', 0)
            neg_count = results.get('negative_reviews_count', 0)
            params = results.get('analysis_params', {})
            
            info_text = (f"Loaded: {game_name} | {total_reviews:,} total reviews | "
                        f"{pos_count:,} positive, {neg_count:,} negative ({params.get('language', 'N/A')})")
            self.info_text.set(info_text)
            
            # Display results
            self._display_results(results)
            
            # Enable export
            self.export_button.config(state=tk.NORMAL)
            
            messagebox.showinfo("Success", f"Loaded TF-IDF analysis results for {game_name}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load results:\n{e}")
    
    def clear_data(self):
        """Clear loaded data and free memory."""
        if clear_tab_data(self):
            self.info_text.set("No data loaded")
            self._clear_results_display()
            self.export_button.config(state=tk.DISABLED)
            messagebox.showinfo("Memory Freed", "Data cleared successfully. Memory has been freed.")
        else:
            messagebox.showinfo("No Data", "No data loaded to clear.")
    
    def run_analysis(self):
        """Run TF-IDF analysis on loaded data."""
        if not hasattr(self, 'current_data') or self.current_data is None:
            messagebox.showwarning("No Data", "Please load data first before running analysis.")
            return
        
        # Validate top N input
        try:
            top_n = int(self.top_n_entry.get())
            if top_n < 1:
                messagebox.showerror("Invalid Input", "Top N must be at least 1.")
                return
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for Top N terms.")
            return
        
        # Get analysis parameters
        language = self.language_var.get()
        
        # Parse ngram range
        ngram_str = self.ngram_var.get()
        ngram_min, ngram_max = map(int, ngram_str.split(','))
        ngram_range = (ngram_min, ngram_max)
        
        # Show progress message
        self.positive_tree.delete(*self.positive_tree.get_children())
        self.negative_tree.delete(*self.negative_tree.get_children())
        self.positive_tree.insert('', tk.END, values=('', 'Analyzing... Please wait...', ''))
        self.negative_tree.insert('', tk.END, values=('', 'Analyzing... Please wait...', ''))
        
        # Run analysis in background thread to keep UI responsive
        def analyze_thread():
            try:
                analyzer = TfidfAnalyzer()
                results = analyzer.analyze(
                    self.current_data,
                    language=language,
                    top_n=top_n,
                    max_features=5000,
                    min_df=2,
                    ngram_range=ngram_range
                )
                
                if results is None:
                    self.frame.after(0, lambda: messagebox.showwarning(
                        "Insufficient Data", 
                        f"Not enough {language} reviews for TF-IDF analysis.\n"
                        f"Need at least 5 positive and 5 negative reviews."
                    ))
                    self.frame.after(0, lambda: self.positive_tree.delete(*self.positive_tree.get_children()))
                    self.frame.after(0, lambda: self.negative_tree.delete(*self.negative_tree.get_children()))
                    return
                
                # Store results
                self.current_results = results
                
                # Update UI in main thread
                self.frame.after(0, lambda: self._display_results(results))
                self.frame.after(0, lambda: self.export_button.config(state=tk.NORMAL))
                
                # Show success message
                game_name = results.get('game_name', 'Unknown')
                pos_count = results.get('positive_reviews_count', 0)
                neg_count = results.get('negative_reviews_count', 0)
                saved_to = results.get('saved_to', 'N/A')
                
                self.frame.after(0, lambda: messagebox.showinfo(
                    "Analysis Complete",
                    f"Game: {game_name}\n"
                    f"Analyzed: {pos_count:,} positive, {neg_count:,} negative reviews\n"
                    f"Top {top_n} distinctive terms identified for each sentiment\n\n"
                    f"Results saved to:\n{saved_to}"
                ))
            
            except Exception as e:
                self.frame.after(0, lambda: messagebox.showerror(
                    "Analysis Error",
                    f"An error occurred during analysis:\n{str(e)}"
                ))
                self.frame.after(0, lambda: self.positive_tree.delete(*self.positive_tree.get_children()))
                self.frame.after(0, lambda: self.negative_tree.delete(*self.negative_tree.get_children()))
        
        # Start analysis thread
        thread = threading.Thread(target=analyze_thread, daemon=True)
        thread.start()
    
    def export_results(self):
        """Export analysis results to CSV."""
        if self.current_results is None:
            messagebox.showwarning("No Results", "No results to export. Please run analysis first.")
            return
        
        # Generate default filename
        game_name = self.current_results.get('game_name', 'Unknown').replace(' ', '_')
        params = self.current_results.get('analysis_params', {})
        language = params.get('language', 'unknown')
        
        default_name = f"{game_name}_{language}_tfidf_analysis.csv"
        
        filepath = filedialog.asksaveasfilename(
            title="Export TF-IDF Analysis Results",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile=default_name
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['Sentiment', 'Rank', 'Term', 'TF-IDF Score'])
                
                # Write positive terms
                positive_terms = self.current_results.get('positive_distinctive_terms', [])
                for item in positive_terms:
                    writer.writerow([
                        'Positive',
                        item['rank'],
                        item['term'],
                        item['score']
                    ])
                
                # Write negative terms
                negative_terms = self.current_results.get('negative_distinctive_terms', [])
                for item in negative_terms:
                    writer.writerow([
                        'Negative',
                        item['rank'],
                        item['term'],
                        item['score']
                    ])
            
            messagebox.showinfo("Success", f"Results exported to:\n{filepath}")
        
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results:\n{e}")
    
    def _display_results(self, results: dict):
        """
        Display TF-IDF analysis results in both tree views.
        
        Args:
            results: Analysis results dictionary
        """
        # Clear existing results
        self.positive_tree.delete(*self.positive_tree.get_children())
        self.negative_tree.delete(*self.negative_tree.get_children())
        
        # Get terms
        positive_terms = results.get('positive_distinctive_terms', [])
        negative_terms = results.get('negative_distinctive_terms', [])
        
        if not positive_terms and not negative_terms:
            self.positive_tree.insert('', tk.END, values=('', 'No results found', ''))
            self.negative_tree.insert('', tk.END, values=('', 'No results found', ''))
            return
        
        # Update info display
        game_name = results.get('game_name', 'Unknown')
        total_reviews = results.get('total_reviews', 0)
        pos_count = results.get('positive_reviews_count', 0)
        neg_count = results.get('negative_reviews_count', 0)
        params = results.get('analysis_params', {})
        
        info_text = (f"{game_name} | {total_reviews:,} total reviews | "
                    f"{pos_count:,} positive, {neg_count:,} negative ({params.get('language', 'N/A')})")
        self.info_text.set(info_text)
        
        # Populate positive terms tree
        for item in positive_terms:
            self.positive_tree.insert('', tk.END, values=(
                item['rank'],
                item['term'],
                f"{item['score']:.4f}"
            ))
        
        # Populate negative terms tree
        for item in negative_terms:
            self.negative_tree.insert('', tk.END, values=(
                item['rank'],
                item['term'],
                f"{item['score']:.4f}"
            ))
        
        # Enable word cloud generation button
        self.generate_wordclouds_btn.config(state=tk.NORMAL)
