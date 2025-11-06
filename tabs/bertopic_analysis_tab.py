"""
BERTopic Analysis Tab - UI for topic modeling with BERTopic.

Provides interface for discovering topics in Steam reviews using
state-of-the-art semantic embeddings and clustering algorithms.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import threading
from analyzers.bertopic_analyzer import BERTopicAnalyzer
from .base_tab import BaseTab
import webbrowser
import tempfile


class BERTopicAnalysisTab(BaseTab):
    """
    Tab for BERTopic topic modeling analysis.
    
    Features:
    - Language-specific analysis
    - Sentiment filtering
    - Configurable parameters
    - Interactive visualizations
    - Topic export
    """
    
    def get_tab_title(self):
        """Return the tab title."""
        return "BERTopic Analysis"
    
    def create_ui(self):
        """Create the BERTopic analysis UI."""
        # Main container with scrollbar
        main_container = ttk.Frame(self.frame)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for scrolling
        canvas = tk.Canvas(main_container)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            return "break"
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # === Data Loading Section ===
        load_frame = ttk.LabelFrame(scrollable_frame, text="Data Loading", padding="10")
        load_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(load_frame, text="Load Raw JSON", command=self.load_raw_json).pack(side='left', padx=5)
        
        self.data_info_label = ttk.Label(load_frame, text="No data loaded", foreground='gray')
        self.data_info_label.pack(side='left', padx=10)
        
        # === Analysis Parameters ===
        params_frame = ttk.LabelFrame(scrollable_frame, text="Analysis Parameters", padding="10")
        params_frame.pack(fill='x', padx=10, pady=5)
        
        # Language selection
        lang_frame = ttk.Frame(params_frame)
        lang_frame.pack(fill='x', pady=5)
        
        ttk.Label(lang_frame, text="Language:").pack(side='left', padx=(0, 5))
        self.language_var = tk.StringVar(value='english')
        lang_combo = ttk.Combobox(
            lang_frame, 
            textvariable=self.language_var,
            values=['english', 'schinese'],
            state='readonly',
            width=15
        )
        lang_combo.pack(side='left', padx=5)
        
        # Sentiment filter
        ttk.Label(lang_frame, text="Sentiment:").pack(side='left', padx=(20, 5))
        self.sentiment_var = tk.StringVar(value='all')
        sentiment_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.sentiment_var,
            values=['all', 'positive', 'negative'],
            state='readonly',
            width=12
        )
        sentiment_combo.pack(side='left', padx=5)
        
        # Min topic size
        topic_size_frame = ttk.Frame(params_frame)
        topic_size_frame.pack(fill='x', pady=5)
        
        ttk.Label(topic_size_frame, text="Min Topic Size:").pack(side='left', padx=(0, 5))
        self.min_topic_size_var = tk.IntVar(value=10)
        topic_size_spin = ttk.Spinbox(
            topic_size_frame,
            from_=5,
            to=100,
            textvariable=self.min_topic_size_var,
            width=10
        )
        topic_size_spin.pack(side='left', padx=5)
        ttk.Label(topic_size_frame, text="(smaller = more topics)", foreground='gray').pack(side='left', padx=5)
        
        # N-gram range
        ngram_frame = ttk.Frame(params_frame)
        ngram_frame.pack(fill='x', pady=5)
        
        ttk.Label(ngram_frame, text="N-gram Range:").pack(side='left', padx=(0, 5))
        self.ngram_start_var = tk.IntVar(value=1)
        self.ngram_end_var = tk.IntVar(value=2)
        
        ttk.Spinbox(ngram_frame, from_=1, to=3, textvariable=self.ngram_start_var, width=5).pack(side='left', padx=2)
        ttk.Label(ngram_frame, text="to").pack(side='left', padx=5)
        ttk.Spinbox(ngram_frame, from_=1, to=3, textvariable=self.ngram_end_var, width=5).pack(side='left', padx=2)
        ttk.Label(ngram_frame, text="(1-2 recommended)", foreground='gray').pack(side='left', padx=5)
        
        # Top N words
        words_frame = ttk.Frame(params_frame)
        words_frame.pack(fill='x', pady=5)
        
        ttk.Label(words_frame, text="Words per Topic:").pack(side='left', padx=(0, 5))
        self.top_n_words_var = tk.IntVar(value=10)
        ttk.Spinbox(words_frame, from_=5, to=20, textvariable=self.top_n_words_var, width=10).pack(side='left', padx=5)
        
        # === Action Buttons ===
        action_frame = ttk.Frame(params_frame)
        action_frame.pack(fill='x', pady=10)
        
        self.analyze_btn = ttk.Button(
            action_frame,
            text="Analyze Topics",
            command=self.analyze_topics,
            state='disabled'
        )
        self.analyze_btn.pack(side='left', padx=5)
        
        self.clear_btn = ttk.Button(
            action_frame,
            text="Clear Data",
            command=self.clear_data,
            state='disabled'
        )
        self.clear_btn.pack(side='left', padx=5)
        
        # Status label
        self.status_label = ttk.Label(params_frame, text="", foreground='blue')
        self.status_label.pack(pady=5)
        
        # === Results Section ===
        results_frame = ttk.LabelFrame(scrollable_frame, text="Topic Analysis Results", padding="10")
        results_frame.pack(fill='both', expand=False, padx=10, pady=5)
        
        # Summary info
        self.summary_label = ttk.Label(results_frame, text="No analysis performed yet", foreground='gray')
        self.summary_label.pack(pady=5)
        
        # Topic table
        table_frame = ttk.Frame(results_frame)
        table_frame.pack(fill='both', expand=True, pady=5)
        
        # Scrollbars for table
        table_scroll_y = ttk.Scrollbar(table_frame, orient='vertical')
        table_scroll_x = ttk.Scrollbar(table_frame, orient='horizontal')
        
        self.topic_tree = ttk.Treeview(
            table_frame,
            columns=('ID', 'Size', 'Top Words'),
            show='headings',
            yscrollcommand=table_scroll_y.set,
            xscrollcommand=table_scroll_x.set,
            height=12
        )
        
        table_scroll_y.config(command=self.topic_tree.yview)
        table_scroll_x.config(command=self.topic_tree.xview)
        
        # Configure columns
        self.topic_tree.heading('ID', text='Topic ID')
        self.topic_tree.heading('Size', text='Review Count')
        self.topic_tree.heading('Top Words', text='Top Words')
        
        self.topic_tree.column('ID', width=80, anchor='center')
        self.topic_tree.column('Size', width=100, anchor='center')
        self.topic_tree.column('Top Words', width=600, anchor='w')
        
        self.topic_tree.grid(row=0, column=0, sticky='nsew')
        table_scroll_y.grid(row=0, column=1, sticky='ns')
        table_scroll_x.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Bind double-click to show topic details
        self.topic_tree.bind('<Double-1>', self.show_topic_details)
        
        # === Visualization Section ===
        viz_frame = ttk.LabelFrame(scrollable_frame, text="Interactive Visualizations", padding="10")
        viz_frame.pack(fill='x', padx=10, pady=5)
        
        viz_btn_frame = ttk.Frame(viz_frame)
        viz_btn_frame.pack(pady=5)
        
        self.viz_topics_btn = ttk.Button(
            viz_btn_frame,
            text="📊 Visualize Topics",
            command=self.visualize_topics,
            state='disabled'
        )
        self.viz_topics_btn.pack(side='left', padx=5)
        
        self.viz_hierarchy_btn = ttk.Button(
            viz_btn_frame,
            text="🌳 Topic Hierarchy",
            command=self.visualize_hierarchy,
            state='disabled'
        )
        self.viz_hierarchy_btn.pack(side='left', padx=5)
        
        self.viz_barchart_btn = ttk.Button(
            viz_btn_frame,
            text="📈 Top Topics Chart",
            command=self.visualize_barchart,
            state='disabled'
        )
        self.viz_barchart_btn.pack(side='left', padx=5)
        
        ttk.Label(viz_frame, text="(Opens in browser)", foreground='gray').pack()
        
        # === Export Section ===
        export_frame = ttk.LabelFrame(scrollable_frame, text="Export", padding="10")
        export_frame.pack(fill='x', padx=10, pady=5)
        
        self.export_btn = ttk.Button(
            export_frame,
            text="Export Results (JSON)",
            command=self.export_results,
            state='disabled'
        )
        self.export_btn.pack(side='left', padx=5)
        
        # Store state
        self.current_data = None
        self.current_results = None
        self.analyzer = BERTopicAnalyzer()
    
    def load_raw_json(self):
        """Load raw review JSON file."""
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
            
            self.current_data = json_data
            self.current_results = None
            
            # Update UI
            metadata = json_data.get('metadata', {})
            total_reviews = len(json_data.get('reviews', []))
            appid = metadata.get('appid', 'N/A')
            
            self.data_info_label.config(
                text=f"Loaded: {total_reviews:,} reviews | App ID: {appid}",
                foreground='green'
            )
            
            self.analyze_btn.config(state='normal')
            self.clear_btn.config(state='normal')
            
            messagebox.showinfo("Success", f"Loaded {total_reviews:,} reviews")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")
    
    def analyze_topics(self):
        """Run BERTopic analysis in background thread."""
        if not self.current_data:
            messagebox.showwarning("No Data", "Please load a JSON file first.")
            return
        
        # Get parameters
        language = self.language_var.get()
        sentiment = self.sentiment_var.get()
        sentiment_filter = None if sentiment == 'all' else sentiment
        min_topic_size = self.min_topic_size_var.get()
        ngram_start = self.ngram_start_var.get()
        ngram_end = self.ngram_end_var.get()
        ngram_range = (ngram_start, ngram_end)
        top_n_words = self.top_n_words_var.get()
        
        # Disable UI
        self.analyze_btn.config(state='disabled')
        self.status_label.config(text="Analyzing... This may take a few minutes.", foreground='blue')
        
        def run_analysis():
            try:
                results = self.analyzer.analyze(
                    self.current_data,
                    language=language,
                    min_topic_size=min_topic_size,
                    ngram_range=ngram_range,
                    top_n_words=top_n_words,
                    sentiment_filter=sentiment_filter
                )
                
                self.frame.after(0, lambda: self.on_analysis_complete(results))
            
            except Exception as e:
                error_msg = str(e)
                self.frame.after(0, lambda: self.on_analysis_error(error_msg))
        
        thread = threading.Thread(target=run_analysis, daemon=True)
        thread.start()
    
    def on_analysis_complete(self, results):
        """Handle analysis completion."""
        if 'error' in results:
            messagebox.showerror("Analysis Error", results['error'])
            self.status_label.config(text="", foreground='blue')
            self.analyze_btn.config(state='normal')
            return
        
        self.current_results = results
        
        # Update summary
        metadata = results['metadata']
        summary_text = (
            f"Found {metadata['num_topics']} topics from {metadata['total_documents']:,} reviews | "
            f"Outliers: {results['outlier_count']}"
        )
        self.summary_label.config(text=summary_text, foreground='green')
        
        # Populate topic table
        self.topic_tree.delete(*self.topic_tree.get_children())
        
        for topic in results['topics']:
            top_words = ', '.join([w['word'] for w in topic['words'][:10]])
            self.topic_tree.insert('', 'end', values=(
                f"Topic {topic['topic_id']}",
                f"{topic['count']:,}",
                top_words
            ))
        
        # Enable buttons
        self.analyze_btn.config(state='normal')
        self.viz_topics_btn.config(state='normal')
        self.viz_hierarchy_btn.config(state='normal')
        self.viz_barchart_btn.config(state='normal')
        self.export_btn.config(state='normal')
        
        self.status_label.config(text="✓ Analysis complete!", foreground='green')
        
        messagebox.showinfo("Success", f"Analysis complete! Found {metadata['num_topics']} topics.")
    
    def on_analysis_error(self, error_msg):
        """Handle analysis error."""
        messagebox.showerror("Error", f"Analysis failed:\n{error_msg}")
        self.status_label.config(text="", foreground='blue')
        self.analyze_btn.config(state='normal')
    
    def show_topic_details(self, event):
        """Show detailed information for selected topic."""
        selection = self.topic_tree.selection()
        if not selection or not self.current_results:
            return
        
        item = self.topic_tree.item(selection[0])
        topic_id_str = item['values'][0]  # e.g., "Topic 0"
        topic_id = int(topic_id_str.split()[1])
        
        # Find topic in results
        topic = next((t for t in self.current_results['topics'] if t['topic_id'] == topic_id), None)
        if not topic:
            return
        
        # Create popup window
        popup = tk.Toplevel(self.frame)
        popup.title(f"Topic {topic_id} Details")
        popup.geometry("700x600")
        
        # Topic info
        info_frame = ttk.Frame(popup, padding="10")
        info_frame.pack(fill='x')
        
        ttk.Label(info_frame, text=f"Topic {topic_id}: {topic['name']}", font=('Arial', 12, 'bold')).pack(anchor='w')
        ttk.Label(info_frame, text=f"Review Count: {topic['count']:,}").pack(anchor='w', pady=2)
        
        # Top words
        words_frame = ttk.LabelFrame(popup, text="Top Words", padding="10")
        words_frame.pack(fill='x', padx=10, pady=5)
        
        words_text = tk.Text(words_frame, height=8, wrap='word')
        words_text.pack(fill='x')
        
        for i, word_info in enumerate(topic['words'], 1):
            words_text.insert('end', f"{i}. {word_info['word']} (score: {word_info['score']:.4f})\n")
        
        words_text.config(state='disabled')
        
        # Representative reviews
        docs_frame = ttk.LabelFrame(popup, text="Representative Reviews", padding="10")
        docs_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        docs_text = tk.Text(docs_frame, wrap='word')
        docs_scroll = ttk.Scrollbar(docs_frame, command=docs_text.yview)
        docs_text.configure(yscrollcommand=docs_scroll.set)
        
        docs_text.pack(side='left', fill='both', expand=True)
        docs_scroll.pack(side='right', fill='y')
        
        for i, doc in enumerate(topic['representative_docs'], 1):
            docs_text.insert('end', f"--- Example {i} ---\n{doc}\n\n")
        
        docs_text.config(state='disabled')
    
    def visualize_topics(self):
        """Generate and open intertopic distance map."""
        if not self.current_results:
            return
        
        self.status_label.config(text="Generating visualization...", foreground='blue')
        
        try:
            fig = self.analyzer.visualize_topics()
            if fig:
                self._open_plotly_in_browser(fig, "topic_visualization")
                self.status_label.config(text="✓ Visualization opened in browser", foreground='green')
            else:
                messagebox.showerror("Error", "Failed to generate visualization")
                self.status_label.config(text="", foreground='blue')
        except Exception as e:
            messagebox.showerror("Error", f"Visualization failed:\n{e}")
            self.status_label.config(text="", foreground='blue')
    
    def visualize_hierarchy(self):
        """Generate and open hierarchical clustering."""
        if not self.current_results:
            return
        
        self.status_label.config(text="Generating hierarchy...", foreground='blue')
        
        try:
            fig = self.analyzer.visualize_hierarchy()
            if fig:
                self._open_plotly_in_browser(fig, "topic_hierarchy")
                self.status_label.config(text="✓ Hierarchy opened in browser", foreground='green')
            else:
                messagebox.showerror("Error", "Failed to generate hierarchy")
                self.status_label.config(text="", foreground='blue')
        except Exception as e:
            messagebox.showerror("Error", f"Hierarchy failed:\n{e}")
            self.status_label.config(text="", foreground='blue')
    
    def visualize_barchart(self):
        """Generate and open top topics bar chart."""
        if not self.current_results:
            return
        
        self.status_label.config(text="Generating chart...", foreground='blue')
        
        try:
            fig = self.analyzer.visualize_barchart(top_n_topics=10)
            if fig:
                self._open_plotly_in_browser(fig, "topic_barchart")
                self.status_label.config(text="✓ Chart opened in browser", foreground='green')
            else:
                messagebox.showerror("Error", "Failed to generate chart")
                self.status_label.config(text="", foreground='blue')
        except Exception as e:
            messagebox.showerror("Error", f"Chart failed:\n{e}")
            self.status_label.config(text="", foreground='blue')
    
    def _open_plotly_in_browser(self, fig, filename):
        """Open Plotly figure in web browser."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8')
        fig.write_html(temp_file.name)
        temp_file.close()
        webbrowser.open('file://' + temp_file.name)
    
    def export_results(self):
        """Export analysis results to JSON."""
        if not self.current_results:
            messagebox.showwarning("No Results", "Please run analysis first.")
            return
        
        # Get metadata for filename
        metadata = self.current_results['metadata']
        appid = self.current_data.get('metadata', {}).get('appid', 'unknown')
        game_name = self.current_data.get('metadata', {}).get('game_name', 'unknown')
        language = metadata['language']
        sentiment = metadata.get('sentiment_filter', 'all')
        
        default_filename = f"{appid}_{game_name}_{language}_{sentiment}_bertopic.json"
        
        filepath = filedialog.asksaveasfilename(
            title="Export Analysis Results",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialdir="./data/processed/insights",
            initialfile=default_filename
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.current_results, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Success", f"Results exported to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export:\n{e}")
    
    def clear_data(self):
        """Clear loaded data and results."""
        self.current_data = None
        self.current_results = None
        self.analyzer = BERTopicAnalyzer()
        
        self.data_info_label.config(text="No data loaded", foreground='gray')
        self.summary_label.config(text="No analysis performed yet", foreground='gray')
        self.status_label.config(text="", foreground='blue')
        
        self.topic_tree.delete(*self.topic_tree.get_children())
        
        self.analyze_btn.config(state='disabled')
        self.clear_btn.config(state='disabled')
        self.viz_topics_btn.config(state='disabled')
        self.viz_hierarchy_btn.config(state='disabled')
        self.viz_barchart_btn.config(state='disabled')
        self.export_btn.config(state='disabled')
