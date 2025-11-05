"""
Extreme Reviews Tab - visualizes reviews with exceptional playtime values.

Displays per-language comparisons of extreme reviews:
- Battle 1: Longest playtime when review was written
- Battle 2: Longest total playtime (current)

Each battle shows positive vs negative review with highest values,
with winners highlighted in yellow.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
from datetime import datetime

import utils
from analyzers.playtime_extremes import PlaytimeExtremesAnalyzer
from .base_tab import BaseTab


class ExtremeReviewsTab(BaseTab):
    """
    Tab for analyzing and displaying extreme playtime reviews.
    
    Provides:
    - Loading raw JSON or pre-analyzed results
    - Language filtering (default: English and Chinese)
    - Visual comparison cards with winner highlighting
    - Per-language statistics and Steam categories
    """
    
    def get_tab_title(self) -> str:
        return "Extreme Reviews"
    
    def create_ui(self):
        """Create all UI elements for the extreme reviews tab."""
        # Control panel with load buttons and language filter
        control_frame = ttk.Frame(self.frame, padding="10")
        control_frame.pack(fill=tk.X)
        
        ttk.Label(control_frame, text="Extreme Review Analysis", font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Load Raw JSON", command=self.load_raw_json_for_extremes).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Load Saved Results", command=self.load_extreme_results).pack(side=tk.LEFT, padx=5)
        
        # Language filter (comma-separated list)
        ttk.Label(control_frame, text="Languages:", font=('Arial', 10)).pack(side=tk.LEFT, padx=(20, 5))
        
        self.language_filter_var = tk.StringVar(value="english,schinese")
        self.language_filter_entry = ttk.Entry(control_frame, textvariable=self.language_filter_var, width=30)
        self.language_filter_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Apply Filter", command=self.apply_language_filter).pack(side=tk.LEFT, padx=5)
        
        self.current_results = None
        
        # Information display showing dataset metadata and filter status
        info_frame = ttk.LabelFrame(self.frame, text="Dataset Information", padding="10")
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.extreme_info_text = tk.StringVar(value="No data loaded")
        ttk.Label(info_frame, textvariable=self.extreme_info_text, justify=tk.LEFT).pack(anchor=tk.W)
        
        self.language_info_text = tk.StringVar(value="")
        ttk.Label(info_frame, textvariable=self.language_info_text, justify=tk.LEFT, foreground='blue').pack(anchor=tk.W)
        
        # Scrollable canvas for displaying review battle cards
        canvas_frame = ttk.Frame(self.frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.extreme_canvas = tk.Canvas(canvas_frame, bg='#f0f0f0')
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.extreme_canvas.yview)
        self.extreme_scrollable_frame = ttk.Frame(self.extreme_canvas)
        
        self.extreme_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.extreme_canvas.configure(scrollregion=self.extreme_canvas.bbox("all"))
        )
        
        self.extreme_canvas.create_window((0, 0), window=self.extreme_scrollable_frame, anchor=tk.NW)
        self.extreme_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mouse wheel scrolling for canvas
        def _on_canvas_mousewheel(event):
            self.extreme_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.extreme_canvas.bind_all("<MouseWheel>", _on_canvas_mousewheel)
        
        self.extreme_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Placeholder text for empty state
        ttk.Label(
            self.extreme_scrollable_frame, 
            text="Load a raw JSON file to analyze extreme reviews\n\nDefault: Shows English and Chinese reviews\nEdit 'Languages' filter to show others (comma-separated)",
            font=('Arial', 10),
            foreground='gray',
            justify=tk.CENTER
        ).pack(pady=50)
    
    def load_raw_json_for_extremes(self):
        """
        Load raw review JSON and perform extreme playtime analysis.
        
        Runs PlaytimeExtremesAnalyzer on the data, saves results to insights folder,
        and displays with default language filter (English and Chinese).
        """
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
            
            analyzer = PlaytimeExtremesAnalyzer()
            results = analyzer.analyze(json_data)
            
            if results:
                self.current_results = results
                self.apply_language_filter()
                messagebox.showinfo("Success", f"Extreme reviews analyzed and saved to:\n{results.get('saved_to', 'Unknown')}")
            else:
                messagebox.showwarning("No Data", "No reviews found in the JSON file.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze file:\n{e}")
    
    def load_extreme_results(self):
        """
        Load previously saved extreme review analysis results.
        
        Loads pre-analyzed results from insights folder and displays with
        default language filter.
        """
        filepath = filedialog.askopenfilename(
            title="Select Extreme Review Results JSON",
            filetypes=[("JSON Files", "*.json")],
            initialdir="./data/processed/insights"
        )
        if not filepath:
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            self.current_results = results
            self.apply_language_filter()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load results:\n{e}")
    
    def get_steam_category(self, positive_count: int, negative_count: int) -> str:
        """
        Determine Steam review category from review counts.
        
        Args:
            positive_count: Number of positive reviews
            negative_count: Number of negative reviews
            
        Returns:
            Steam category string (e.g., "Very Positive", "Mixed")
        """
        total = positive_count + negative_count
        if total == 0:
            return "No Reviews"
        
        positive_percentage = (positive_count / total) * 100
        
        if positive_percentage >= 95:
            return "Overwhelmingly Positive"
        elif positive_percentage >= 80:
            return "Very Positive"
        elif positive_percentage >= 70:
            return "Mostly Positive"
        elif positive_percentage >= 40:
            return "Mixed"
        elif positive_percentage >= 20:
            return "Mostly Negative"
        elif positive_percentage > 0:
            return "Very Negative"
        else:
            return "Overwhelmingly Negative"
    
    def apply_language_filter(self):
        """
        Filter and display extreme reviews for selected languages.
        
        Parses the comma-separated language filter input, validates against
        available languages in the dataset, and renders the battle cards.
        """
        if not self.current_results:
            messagebox.showwarning("No Data", "Please load data first before applying filter.")
            return
        
        filter_text = self.language_filter_var.get().strip()
        if not filter_text:
            messagebox.showwarning("Invalid Filter", "Please specify at least one language.")
            return
        
        selected_languages = [lang.strip().lower() for lang in filter_text.split(',')]
        
        extremes_by_language = self.current_results.get('extremes_by_language', {})
        if not extremes_by_language:
            messagebox.showwarning("Old Format", "This file uses old format. Please re-analyze from raw JSON.")
            return
        
        available_languages = list(extremes_by_language.keys())
        filtered_languages = [lang for lang in selected_languages if lang in available_languages]
        
        if not filtered_languages:
            messagebox.showwarning("No Match", 
                f"None of the selected languages found.\nAvailable: {', '.join(available_languages)}")
            return
        
        self.display_extreme_reviews_filtered(filtered_languages, extremes_by_language)
    
    def display_extreme_reviews(self, results: dict):
        """
        Display extreme reviews in two-battle layout (legacy method).
        
        Note: This method is kept for backward compatibility but is no longer
        used. The new per-language display uses display_extreme_reviews_filtered().
        
        Args:
            results: Dictionary with 'extremes' and 'metadata' keys
        """
        for widget in self.extreme_scrollable_frame.winfo_children():
            widget.destroy()
        
        metadata = results.get('metadata', {})
        appid = metadata.get('appid', 'N/A')
        game_title = utils.get_game_name(appid) if isinstance(appid, int) else metadata.get('game_title', 'N/A')
        total_reviews = results.get('total_reviews_analyzed', 0)
        positive_count = results.get('positive_reviews_count', 0)
        negative_count = results.get('negative_reviews_count', 0)
        date_collected = metadata.get('date_collected_utc', 'N/A')
        if isinstance(date_collected, str):
            date_collected = date_collected[:10]
        
        info_text = (
            f"Game: {game_title} (App ID: {appid})  |  "
            f"Total Reviews: {total_reviews:,} "
            f"(👍 {positive_count:,}, 👎 {negative_count:,})  |  "
            f"Fetched: {date_collected}"
        )
        self.extreme_info_text.set(info_text)
        
        extremes = results.get('extremes', {})
        
        # Battle 1: Longest Playtime @ Review (Positive vs Negative)
        battle1_title = ttk.Label(
            self.extreme_scrollable_frame,
            text="⚔️ BATTLE 1: Longest Playtime @ Review",
            font=('Arial', 13, 'bold')
        )
        battle1_title.pack(pady=(10, 5))
        
        battle1_frame = ttk.Frame(self.extreme_scrollable_frame)
        battle1_frame.pack(fill=tk.X, padx=10, pady=5)
        
        pos_review_1 = extremes.get('longest_playtime_at_review_positive')
        neg_review_1 = extremes.get('longest_playtime_at_review_negative')
        
        # Determine winner for battle 1
        if pos_review_1 and neg_review_1:
            pos_time_1 = pos_review_1['author'].get('playtime_at_review', 0)
            neg_time_1 = neg_review_1['author'].get('playtime_at_review', 0)
            winner_1_is_pos = pos_time_1 >= neg_time_1
        elif pos_review_1:
            winner_1_is_pos = True
        else:
            winner_1_is_pos = False
        
        # Create side-by-side cards for battle 1
        if pos_review_1:
            pos_card_1 = tk.Frame(battle1_frame)
            pos_card_1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            self.create_review_card(pos_card_1, "👍 Positive Review", pos_review_1, True, winner_1_is_pos, 'playtime_at_review')
        
        if neg_review_1:
            neg_card_1 = tk.Frame(battle1_frame)
            neg_card_1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            self.create_review_card(neg_card_1, "👎 Negative Review", neg_review_1, False, not winner_1_is_pos, 'playtime_at_review')
        
        # Separator
        ttk.Separator(self.extreme_scrollable_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=20)
        
        # Battle 2: Longest Total Playtime (Positive vs Negative)
        battle2_title = ttk.Label(
            self.extreme_scrollable_frame,
            text="⚔️ BATTLE 2: Longest Total Playtime",
            font=('Arial', 13, 'bold')
        )
        battle2_title.pack(pady=(10, 5))
        
        battle2_frame = ttk.Frame(self.extreme_scrollable_frame)
        battle2_frame.pack(fill=tk.X, padx=10, pady=5)
        
        pos_review_2 = extremes.get('longest_playtime_forever_positive')
        neg_review_2 = extremes.get('longest_playtime_forever_negative')
        
        # Determine winner for battle 2
        if pos_review_2 and neg_review_2:
            pos_time_2 = pos_review_2['author'].get('playtime_forever', 0)
            neg_time_2 = neg_review_2['author'].get('playtime_forever', 0)
            winner_2_is_pos = pos_time_2 >= neg_time_2
        elif pos_review_2:
            winner_2_is_pos = True
        else:
            winner_2_is_pos = False
        
        # Create side-by-side cards for battle 2
        if pos_review_2:
            pos_card_2 = tk.Frame(battle2_frame)
            pos_card_2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            self.create_review_card(pos_card_2, "👍 Positive Review", pos_review_2, True, winner_2_is_pos, 'playtime_forever')
        
        if neg_review_2:
            neg_card_2 = tk.Frame(battle2_frame)
            neg_card_2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            self.create_review_card(neg_card_2, "👎 Negative Review", neg_review_2, False, not winner_2_is_pos, 'playtime_forever')
    
    def create_review_card(self, parent, title, review, is_positive, is_winner, metric_type):
        """
        Create a visually styled card displaying a single review.
        
        Winners are highlighted with yellow background. The metric being compared
        (playtime_at_review or playtime_forever) is marked with a star emoji.
        
        Args:
            parent: Parent widget to attach the card to
            title: Card title (e.g., "👍 Positive Review")
            review: Review dictionary from Steam API
            is_positive: Whether this is a positive review
            is_winner: Whether this review won the battle (highest playtime)
            metric_type: 'playtime_at_review' or 'playtime_forever' - determines which stat to highlight
        """
        if is_winner:
            bg_color = '#fff9c4'  # Light yellow for winner
            border_color = '#fdd835'  # Darker yellow
        else:
            bg_color = '#f5f5f5'  # Light gray
            border_color = '#bdbdbd'  # Medium gray
        
        card = tk.Frame(parent, bg=border_color, padx=2, pady=2)
        card.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        inner_frame = tk.Frame(card, bg=bg_color, padx=10, pady=10)
        inner_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title bar (winner status shown by background color only)
        title_frame = tk.Frame(inner_frame, bg=bg_color)
        title_frame.pack(fill=tk.X)
        
        tk.Label(
            title_frame, 
            text=title, 
            font=('Arial', 11, 'bold'),
            bg=bg_color,
            fg='#2e7d32' if is_positive else '#c62828'
        ).pack(anchor=tk.W)
        
        # Playtime statistics from author data
        author_data = review.get('author', {})
        playtime_at_review = author_data.get('playtime_at_review', 0)
        playtime_forever = author_data.get('playtime_forever', 0)
        num_games = author_data.get('num_games_owned', 0)
        
        # Highlight the metric being compared (marked with star emoji)
        if metric_type == 'playtime_at_review':
            stats_text = (
                f"⏱️ Playtime @ Review: {playtime_at_review / 60:.1f} hrs 🌟  |  "
                f"📊 Total Playtime: {playtime_forever / 60:.1f} hrs  |  "
                f"🎮 Games Owned: {num_games}"
            )
        else:  # playtime_forever
            stats_text = (
                f"⏱️ Playtime @ Review: {playtime_at_review / 60:.1f} hrs  |  "
                f"📊 Total Playtime: {playtime_forever / 60:.1f} hrs 🌟  |  "
                f"🎮 Games Owned: {num_games}"
            )
        
        tk.Label(
            inner_frame,
            text=stats_text,
            font=('Arial', 9),
            bg=bg_color,
            fg='#424242'
        ).pack(anchor=tk.W, pady=(5, 5))
        
        # Scrollable review text area
        review_text = review.get('review', 'No review text available')
        text_widget = scrolledtext.ScrolledText(
            inner_frame,
            wrap=tk.WORD,
            height=6,
            font=('Arial', 9),
            bg='white',
            relief=tk.FLAT
        )
        text_widget.insert('1.0', review_text)
        
        # Make read-only while preserving scrollability
        # Keep state=NORMAL for scrolling, but block all editing events
        text_widget.config(state=tk.NORMAL)
        text_widget.bind("<Key>", lambda e: "break")
        text_widget.bind("<Button-2>", lambda e: "break")
        text_widget.bind("<Button-3>", lambda e: "break")
        
        text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Handle mouse wheel: scroll text widget and prevent event propagation to canvas
        def _on_text_mousewheel(event):
            text_widget.yview_scroll(int(-1*(event.delta/120)), "units")
            return "break"  # Stop event from reaching canvas
        
        text_widget.bind("<MouseWheel>", _on_text_mousewheel)
        
        # Review metadata footer
        timestamp = review.get('timestamp_created', 0)
        date_posted = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d') if timestamp else 'Unknown'
        votes_up = review.get('votes_up', 0)
        votes_funny = review.get('votes_funny', 0)
        
        footer_text = f"📅 Posted: {date_posted}  |  👍 Helpful: {votes_up}  |  😄 Funny: {votes_funny}"
        
        tk.Label(
            inner_frame,
            text=footer_text,
            font=('Arial', 8),
            bg=bg_color,
            fg='#757575'
        ).pack(anchor=tk.W)
    
    def display_extreme_reviews_filtered(self, filtered_languages: list, extremes_by_language: dict):
        """
        Render extreme review battles for selected languages.
        
        Creates a scrollable display with per-language sections, each showing:
        - Language header with statistics and Steam category
        - Battle 1: Longest playtime @ review (positive vs negative)
        - Battle 2: Longest total playtime (positive vs negative)
        
        Args:
            filtered_languages: List of language codes to display
            extremes_by_language: Dictionary mapping language -> extreme review data
        """
        for widget in self.extreme_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Update dataset information panel
        metadata = self.current_results.get('metadata', {})
        appid = metadata.get('appid', 'N/A')
        game_title = utils.get_game_name(appid) if isinstance(appid, int) else metadata.get('game_title', 'N/A')
        total_reviews = self.current_results.get('total_reviews_analyzed', 0)
        date_collected = metadata.get('date_collected_utc', 'N/A')
        if isinstance(date_collected, str):
            date_collected = date_collected[:10]
        
        info_text = (
            f"Game: {game_title} (App ID: {appid})  |  "
            f"Total Reviews: {total_reviews:,}  |  "
            f"Fetched: {date_collected}"
        )
        self.extreme_info_text.set(info_text)
        
        # Update language filter status
        all_languages = list(extremes_by_language.keys())
        language_info = f"Showing {len(filtered_languages)} of {len(all_languages)} languages: {', '.join(filtered_languages)}"
        self.language_info_text.set(language_info)
        
        # Render battles for each selected language
        for lang in filtered_languages:
            lang_extremes = extremes_by_language.get(lang, {})
            if not lang_extremes:
                continue
            
            # Language header
            lang_display = lang.upper()
            positive_count = lang_extremes.get('positive_count', 0)
            negative_count = lang_extremes.get('negative_count', 0)
            total_count = lang_extremes.get('total_count', 0)
            
            # Calculate percentage and category
            positive_percentage = (positive_count / total_count * 100) if total_count > 0 else 0
            steam_category = self.get_steam_category(positive_count, negative_count)
            
            lang_header = ttk.Label(
                self.extreme_scrollable_frame,
                text=f"🌐 {lang_display} ({total_count:,} reviews: 👍 {positive_count:,}, 👎 {negative_count:,}) | {positive_percentage:.1f}% Positive | {steam_category}",
                font=('Arial', 12, 'bold'),
                foreground='#1976D2'
            )
            lang_header.pack(pady=(20, 10))
            
            # Comparison 1: Longest Playtime @ Review (Positive vs Negative)
            comp1_title = ttk.Label(
                self.extreme_scrollable_frame,
                text="Longest Playtime @ Review - Positive vs Negative",
                font=('Arial', 11, 'bold')
            )
            comp1_title.pack(pady=(10, 5))
            
            battle1_frame = ttk.Frame(self.extreme_scrollable_frame)
            battle1_frame.pack(fill=tk.X, padx=10, pady=5)
            
            pos_review_1 = lang_extremes.get('longest_playtime_at_review_positive')
            neg_review_1 = lang_extremes.get('longest_playtime_at_review_negative')
            
            # Determine winner for comparison 1
            winner1 = None
            if pos_review_1 and neg_review_1:
                pos_time = pos_review_1.get('author', {}).get('playtime_at_review', 0)
                neg_time = neg_review_1.get('author', {}).get('playtime_at_review', 0)
                winner1 = 'positive' if pos_time > neg_time else 'negative'
            
            # Display side by side - Comparison 1
            if pos_review_1:
                pos_card_1 = tk.Frame(battle1_frame)
                pos_card_1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
                self.create_review_card(pos_card_1, "👍 Positive Review", pos_review_1, True, 
                                       winner1 == 'positive', 'playtime_at_review')
            if neg_review_1:
                neg_card_1 = tk.Frame(battle1_frame)
                neg_card_1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
                self.create_review_card(neg_card_1, "👎 Negative Review", neg_review_1, False, 
                                       winner1 == 'negative', 'playtime_at_review')
            
            # Comparison 2: Longest Total Playtime (Positive vs Negative)
            comp2_title = ttk.Label(
                self.extreme_scrollable_frame,
                text="Longest Total Playtime - Positive vs Negative",
                font=('Arial', 11, 'bold')
            )
            comp2_title.pack(pady=(20, 5))
            
            battle2_frame = ttk.Frame(self.extreme_scrollable_frame)
            battle2_frame.pack(fill=tk.X, padx=10, pady=5)
            
            pos_review_2 = lang_extremes.get('longest_total_playtime_positive')
            neg_review_2 = lang_extremes.get('longest_total_playtime_negative')
            
            # Determine winner for comparison 2
            winner2 = None
            if pos_review_2 and neg_review_2:
                pos_time = pos_review_2.get('author', {}).get('playtime_forever', 0)
                neg_time = neg_review_2.get('author', {}).get('playtime_forever', 0)
                winner2 = 'positive' if pos_time > neg_time else 'negative'
            
            # Display side by side - Comparison 2
            if pos_review_2:
                pos_card_2 = tk.Frame(battle2_frame)
                pos_card_2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
                self.create_review_card(pos_card_2, "👍 Positive Review", pos_review_2, True, 
                                       winner2 == 'positive', 'playtime_forever')
            if neg_review_2:
                neg_card_2 = tk.Frame(battle2_frame)
                neg_card_2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
                self.create_review_card(neg_card_2, "👎 Negative Review", neg_review_2, False, 
                                       winner2 == 'negative', 'playtime_forever')
            
            # Separator between languages
            ttk.Separator(self.extreme_scrollable_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=20)

