"""
N-gram Analysis Tab - explores common phrases and word combinations.

Analyzes reviews to find frequently occurring n-grams (unigrams, bigrams, trigrams)
in English and Chinese reviews, separated by sentiment.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
import threading
from PIL import Image, ImageTk

from .base_tab import BaseTab
from analyzers.ngram_analyzer import NgramAnalyzer
from analyzers.wordcloud_generator import WordCloudGenerator
from memory_utils import clear_tab_data


class NgramAnalysisTab(BaseTab):
    """
    Tab for N-gram analysis of review text.
    
    Provides:
    - Language selection (English/Chinese)
    - Sentiment filtering (Positive/Negative/Both)
    - N-gram size selection (1-3)
    - Frequency threshold filtering
    - Results table with rankings and statistics
    """
    
    def get_tab_title(self) -> str:
        return "N-gram Analysis"
    
    def create_ui(self):
        """Create all UI elements for the N-gram analysis tab."""
        # Dataset Information section (common across text analysis tabs)
        info_frame = ttk.LabelFrame(self.frame, text="Dataset Information", padding="10")
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.info_text = tk.StringVar(value="No data loaded")
        ttk.Label(info_frame, textvariable=self.info_text, justify=tk.LEFT).pack(anchor=tk.W)
        
        # Control panel for loading data and settings
        control_frame = ttk.Frame(self.frame, padding="10")
        control_frame.pack(fill=tk.X)
        
        ttk.Label(control_frame, text="N-gram Analysis", font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=5)
        
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
        
        # Sentiment selection
        sentiment_frame = ttk.Frame(settings_frame)
        sentiment_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(sentiment_frame, text="Sentiment:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.sentiment_var = tk.StringVar(value="positive")
        ttk.Radiobutton(sentiment_frame, text="Positive", variable=self.sentiment_var, value="positive").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(sentiment_frame, text="Negative", variable=self.sentiment_var, value="negative").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(sentiment_frame, text="Both", variable=self.sentiment_var, value="both").pack(side=tk.LEFT, padx=10)
        
        # N-gram size selection
        ngram_frame = ttk.Frame(settings_frame)
        ngram_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(ngram_frame, text="N-gram Size:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.ngram_size_var = tk.IntVar(value=2)
        ttk.Radiobutton(ngram_frame, text="2-gram (bigrams)", variable=self.ngram_size_var, value=2).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(ngram_frame, text="3-gram (trigrams)", variable=self.ngram_size_var, value=3).pack(side=tk.LEFT, padx=10)
        
        # Minimum frequency threshold
        threshold_frame = ttk.Frame(settings_frame)
        threshold_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(threshold_frame, text="Min Frequency:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.min_freq_entry = ttk.Entry(threshold_frame, width=10)
        self.min_freq_entry.pack(side=tk.LEFT, padx=5)
        self.min_freq_entry.insert(0, "5")
        
        ttk.Button(threshold_frame, text="Analyze", command=self.run_analysis).pack(side=tk.LEFT, padx=20)
        self.export_button = ttk.Button(threshold_frame, text="Export Results", command=self.export_results, state=tk.DISABLED)
        self.export_button.pack(side=tk.LEFT, padx=5)
        
        # Results display area
        results_frame = ttk.LabelFrame(self.frame, text="Analysis Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
        
        # Results table
        columns = ('rank', 'ngram', 'count', 'percentage')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=12)
        
        self.results_tree.heading('rank', text='Rank')
        self.results_tree.heading('ngram', text='N-gram')
        self.results_tree.heading('count', text='Count')
        self.results_tree.heading('percentage', text='Percentage')
        
        self.results_tree.column('rank', width=60, anchor=tk.CENTER)
        self.results_tree.column('ngram', width=300, anchor=tk.W)
        self.results_tree.column('count', width=100, anchor=tk.CENTER)
        self.results_tree.column('percentage', width=100, anchor=tk.CENTER)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Placeholder message
        self.results_tree.insert('', tk.END, values=('', 'Load data and click "Analyze" to see results', '', ''))
        
        # Store current results for export
        self.current_results = None
        
        # Word Cloud Section (Always visible)
        self.wordcloud_generator = WordCloudGenerator()
        self.wordcloud_image = None
        
        # Word cloud frame
        wordcloud_frame = ttk.LabelFrame(self.frame, text="Word Cloud Visualization", padding="10")
        wordcloud_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
        
        # Button to generate
        btn_frame = ttk.Frame(wordcloud_frame)
        btn_frame.pack(pady=5)
        
        self.generate_wordcloud_btn = ttk.Button(
            btn_frame, 
            text="Generate Word Cloud", 
            command=self.generate_wordcloud,
            state=tk.DISABLED
        )
        self.generate_wordcloud_btn.pack(side=tk.LEFT, padx=5)
        
        # Word cloud display
        self.wordcloud_label = ttk.Label(wordcloud_frame, text="Load data and analyze to generate word cloud (opens in popup with save button)")
        self.wordcloud_label.pack(pady=10)
    
    def generate_wordcloud(self):
        """Generate and display word cloud in popup window."""
        if not self.current_results:
            messagebox.showwarning("No Data", "Please run analysis first.")
            return
        
        try:
            top_ngrams = self.current_results.get('top_ngrams', [])
            if not top_ngrams:
                messagebox.showwarning("No Data", "No n-grams available for word cloud")
                return
            
            # Get language from current results
            params = self.current_results.get('analysis_params', {})
            language = params.get('language', 'english')
            
            # Show generating message
            self.wordcloud_label.config(text="Generating word cloud...")
            self.frame.update()
            
            # Generate word cloud with language parameter
            image = self.wordcloud_generator.generate_from_ngrams(
                top_ngrams,
                max_words=100,
                colormap='viridis',
                language=language
            )
            
            if image:
                # Store image for saving
                self.wordcloud_image = image
                
                # Show in popup window
                self._show_wordcloud_popup(image, "N-gram Word Cloud")
                
                # Update label
                self.wordcloud_label.config(text="Word cloud generated! (Shown in popup window with save button)")
            else:
                self.wordcloud_label.config(text="Failed to generate word cloud")
        
        except Exception as e:
            self.wordcloud_label.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to generate word cloud:\n{str(e)}")
    
    def _show_wordcloud_popup(self, image, title):
        """Show word cloud in a popup window with save functionality."""
        popup = tk.Toplevel(self.frame)
        popup.title(title)
        popup.geometry("1250x700")
        
        # Button frame at top
        btn_frame = ttk.Frame(popup)
        btn_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        ttk.Label(btn_frame, text=title, font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        
        save_btn = ttk.Button(
            btn_frame, 
            text="Save Image", 
            command=lambda: self._save_popup_image(image)
        )
        save_btn.pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(btn_frame, text="(Right-click image to save)", foreground='gray').pack(side=tk.RIGHT, padx=10)
        
        # Create canvas with scrollbars
        canvas = tk.Canvas(popup)
        v_scrollbar = ttk.Scrollbar(popup, orient=tk.VERTICAL, command=canvas.yview)
        h_scrollbar = ttk.Scrollbar(popup, orient=tk.HORIZONTAL, command=canvas.xview)
        
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Convert to PhotoImage and display
        photo = ImageTk.PhotoImage(image)
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        canvas.image = photo  # Keep reference
        
        # Right-click to save
        canvas.bind("<Button-3>", lambda e: self._save_popup_image(image))
        
        # Update scroll region
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def _save_popup_image(self, image):
        """Save word cloud image from popup."""
        # Generate default filename from current results
        import os
        default_filename = "ngram_wordcloud.png"
        if self.current_results:
            from datetime import datetime
            metadata = self.current_results.get('metadata', {})
            game_name = self.current_results.get('game_name', '').replace(' ', '_').replace("'", '')
            appid = metadata.get('appid', '')
            params = self.current_results.get('analysis_params', {})
            language = params.get('language', 'unknown')
            sentiment = params.get('sentiment', 'all')
            ngram_size = params.get('ngram_size', 2)
            date_str = datetime.now().strftime('%Y-%m-%d')
            
            default_filename = f"{appid}_{game_name}_{language}_{sentiment}_{ngram_size}gram_wordcloud_{date_str}.png"
        
        # Use absolute path for initialdir
        initial_dir = os.path.abspath("./data/processed")
        
        filepath = filedialog.asksaveasfilename(
            title="Save Word Cloud Image",
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            initialdir=initial_dir,
            initialfile=default_filename
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
        """Load previously saved N-gram analysis results."""
        filepath = filedialog.askopenfilename(
            title="Select N-gram Analysis Results",
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
            filtered_reviews = results.get('filtered_reviews', 0)
            params = results.get('analysis_params', {})
            
            info_text = f"Loaded: {game_name} | {total_reviews:,} total reviews | {filtered_reviews:,} analyzed ({params.get('language', 'N/A')}, {params.get('sentiment', 'N/A')})"
            self.info_text.set(info_text)
            
            # Display results
            self._display_results(results)
            
            # Enable export
            self.export_button.config(state=tk.NORMAL)
            
            messagebox.showinfo("Success", f"Loaded analysis results for {game_name}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load results:\n{e}")
    
    def clear_data(self):
        """Clear loaded data and free memory."""
        if clear_tab_data(self):
            self.info_text.set("No data loaded")
            self.results_text.config(state=tk.NORMAL)
            self.results_text.delete('1.0', tk.END)
            self.results_text.insert('1.0', 'Load data and click "Analyze" to see results...')
            self.results_text.config(state=tk.DISABLED)
            self.export_button.config(state=tk.DISABLED)
            messagebox.showinfo("Memory Freed", "Data cleared successfully. Memory has been freed.")
        else:
            messagebox.showinfo("No Data", "No data loaded to clear.")
    
    def run_analysis(self):
        """Run N-gram analysis on loaded data."""
        if not hasattr(self, 'current_data') or self.current_data is None:
            messagebox.showwarning("No Data", "Please load data first before running analysis.")
            return
        
        # Validate min frequency input
        try:
            min_freq = int(self.min_freq_entry.get())
            if min_freq < 1:
                messagebox.showerror("Invalid Input", "Minimum frequency must be at least 1.")
                return
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for minimum frequency.")
            return
        
        # Get analysis parameters
        language = self.language_var.get()
        sentiment = self.sentiment_var.get()
        ngram_size = self.ngram_size_var.get()
        
        # Show progress message
        self.results_tree.delete(*self.results_tree.get_children())
        self.results_tree.insert('', tk.END, values=('', 'Analyzing... Please wait...', '', ''))
        
        # Run analysis in background thread to keep UI responsive
        def analyze_thread():
            try:
                analyzer = NgramAnalyzer()
                results = analyzer.analyze(
                    self.current_data,
                    language=language,
                    sentiment=sentiment,
                    ngram_size=ngram_size,
                    min_frequency=min_freq,
                    top_n=100  # Get top 100 results
                )
                
                if results is None:
                    self.frame.after(0, lambda: messagebox.showwarning(
                        "No Results", 
                        f"No {language} reviews found with {sentiment} sentiment."
                    ))
                    self.frame.after(0, lambda: self.results_tree.delete(*self.results_tree.get_children()))
                    return
                
                # Store results
                self.current_results = results
                
                # Update UI in main thread
                self.frame.after(0, lambda: self._display_results(results))
                self.frame.after(0, lambda: self.export_button.config(state=tk.NORMAL))
                
                # Show success message
                game_name = results.get('game_name', 'Unknown')
                unique_ngrams = results.get('unique_ngrams', 0)
                filtered_reviews = results.get('filtered_reviews', 0)
                saved_to = results.get('saved_to', 'N/A')
                
                self.frame.after(0, lambda: messagebox.showinfo(
                    "Analysis Complete",
                    f"Game: {game_name}\n"
                    f"Analyzed: {filtered_reviews:,} reviews\n"
                    f"Found: {unique_ngrams:,} unique n-grams\n\n"
                    f"Results saved to:\n{saved_to}"
                ))
            
            except Exception as e:
                self.frame.after(0, lambda: messagebox.showerror(
                    "Analysis Error",
                    f"An error occurred during analysis:\n{str(e)}"
                ))
                self.frame.after(0, lambda: self.results_tree.delete(*self.results_tree.get_children()))
        
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
        sentiment = params.get('sentiment', 'all')
        ngram_size = params.get('ngram_size', 2)
        
        default_name = f"{game_name}_{language}_{sentiment}_{ngram_size}gram_analysis.csv"
        
        filepath = filedialog.asksaveasfilename(
            title="Export N-gram Analysis Results",
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
                writer.writerow(['Rank', 'N-gram', 'Count', 'Percentage'])
                
                # Write data
                top_ngrams = self.current_results.get('top_ngrams', [])
                for i, item in enumerate(top_ngrams, 1):
                    writer.writerow([
                        i,
                        item['ngram'],
                        item['count'],
                        f"{item['percentage']}%"
                    ])
            
            messagebox.showinfo("Success", f"Results exported to:\n{filepath}")
        
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results:\n{e}")
    
    def _display_results(self, results: dict):
        """
        Display analysis results in the tree view.
        
        Args:
            results: Analysis results dictionary
        """
        # Clear existing results
        self.results_tree.delete(*self.results_tree.get_children())
        
        # Get top n-grams
        top_ngrams = results.get('top_ngrams', [])
        
        if not top_ngrams:
            self.results_tree.insert('', tk.END, values=('', 'No results found', '', ''))
            return
        
        # Update info display
        game_name = results.get('game_name', 'Unknown')
        total_reviews = results.get('total_reviews', 0)
        filtered_reviews = results.get('filtered_reviews', 0)
        params = results.get('analysis_params', {})
        
        info_text = (f"{game_name} | {total_reviews:,} total reviews | "
                    f"{filtered_reviews:,} analyzed ({params.get('language', 'N/A')}, "
                    f"{params.get('sentiment', 'N/A')}, {params.get('ngram_size', 2)}-gram)")
        self.info_text.set(info_text)
        
        # Populate tree view
        for i, item in enumerate(top_ngrams, 1):
            self.results_tree.insert('', tk.END, values=(
                i,
                item['ngram'],
                f"{item['count']:,}",
                f"{item['percentage']}%"
            ))
        
        # Enable word cloud generation button
        self.generate_wordcloud_btn.config(state=tk.NORMAL)
