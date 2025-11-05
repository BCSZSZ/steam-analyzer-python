"""
Data Collection Tab - handles fetching reviews from Steam and generating reports.
This is the original main functionality of the application.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import queue
import threading
import math
import csv
import os
import re
import json

import backend
import utils
from .base_tab import BaseTab


class DataCollectionTab(BaseTab):
    """Tab for collecting and analyzing Steam review data."""
    
    def get_tab_title(self) -> str:
        return "Data Collection"
    
    def create_ui(self):
        """Create all UI elements for data collection tab."""
        # Input controls for fetching reviews
        input_frame = ttk.Frame(self.frame, padding="10")
        input_frame.pack(fill=tk.X)

        ttk.Label(input_frame, text="App ID:").pack(side=tk.LEFT, padx=5)
        self.appid_entry = ttk.Entry(input_frame, width=10)
        self.appid_entry.pack(side=tk.LEFT, padx=5)
        self.appid_entry.insert(0, "1022980")

        self.fetch_all_checkbox = ttk.Checkbutton(
            input_frame, text="Fetch all available reviews", 
            variable=self.app.fetch_all_var, command=self.toggle_max_reviews_entry
        )
        self.fetch_all_checkbox.pack(side=tk.LEFT, padx=(20, 5))

        self.reviews_entry = ttk.Entry(input_frame, width=15)
        self.reviews_entry.pack(side=tk.LEFT, padx=5)
        self.reviews_entry.insert(0, "2000")

        self.fetch_button = ttk.Button(input_frame, text="Fetch & Analyze", command=self.start_analysis_thread)
        self.fetch_button.pack(side=tk.LEFT, padx=10)

        self.analyze_json_button = ttk.Button(input_frame, text="Analyze from JSON", command=self.start_json_analysis_thread)
        self.analyze_json_button.pack(side=tk.LEFT, padx=5)

        self.import_button = ttk.Button(input_frame, text="Import Report (CSV)", command=self.import_csv_report)
        self.import_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = ttk.Button(input_frame, text="Cancel", command=self.cancel_download, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # Information display showing current dataset metadata
        info_frame = ttk.LabelFrame(self.frame, text="Current Data Information", padding="10")
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.info_title = tk.StringVar(value="Game Title: N/A")
        self.info_appid = tk.StringVar(value="App ID: N/A")
        self.info_total_reviews = tk.StringVar(value="Total Reviews: N/A")
        self.info_date = tk.StringVar(value="Fetched Date: N/A")
        
        ttk.Label(info_frame, textvariable=self.info_title).pack(side=tk.LEFT, padx=20)
        ttk.Label(info_frame, textvariable=self.info_appid).pack(side=tk.LEFT, padx=20)
        ttk.Label(info_frame, textvariable=self.info_total_reviews).pack(side=tk.LEFT, padx=20)
        ttk.Label(info_frame, textvariable=self.info_date).pack(side=tk.LEFT, padx=20)

        # Report table showing analysis results grouped by language
        table_frame = ttk.Frame(self.frame, padding="10")
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('lang', 'lang_cn', 'total', 'positive', 'rate', 'category', 'category_cn', 
                   'avg_games_pos', 'avg_games_neg', 'avg_play_review_pos', 'avg_play_review_neg', 
                   'avg_play_forever_pos', 'avg_play_forever_neg')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        headings = {
            'lang': ('Language', 120), 'lang_cn': ('语言', 100), 
            'total': ('Total', 80), 'positive': ('Positive', 80), 
            'rate': ('Rate', 80), 'category': ('Category', 130), 
            'category_cn': ('评价', 100),
            'avg_games_pos': ('Avg Games (Pos)', 110),
            'avg_games_neg': ('Avg Games (Neg)', 110),
            'avg_play_review_pos': ('Play @ Review (Pos, hrs)', 130),
            'avg_play_review_neg': ('Play @ Review (Neg, hrs)', 130),
            'avg_play_forever_pos': ('Total Play (Pos, hrs)', 120),
            'avg_play_forever_neg': ('Total Play (Neg, hrs)', 120)
        }
        
        numeric_cols = ['total', 'positive', 'rate', 'avg_games_pos', 'avg_games_neg', 
                        'avg_play_review_pos', 'avg_play_review_neg', 
                        'avg_play_forever_pos', 'avg_play_forever_neg']

        for key, (text, width) in headings.items():
            self.tree.heading(key, text=text, command=lambda _col=key: self.sort_column(_col, numeric_cols))
            self.tree.column(key, width=width, anchor=tk.CENTER if key in numeric_cols or key in ['lang_cn', 'category_cn'] else tk.W)

        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Status label for operation feedback
        log_frame = ttk.Frame(self.frame, padding="10")
        log_frame.pack(fill=tk.X)
        self.status_label = ttk.Label(log_frame, text="Ready.", anchor=tk.W)
        self.status_label.pack(fill=tk.X)

    def cancel_download(self):
        """Signal cancellation of ongoing download operation."""
        self.status_label.config(text="Cancelling... please wait for the current request to finish.")
        self.app.cancel_event.set()
        self.cancel_button.config(state=tk.DISABLED)

    def toggle_max_reviews_entry(self):
        """Enable/disable review count entry based on 'fetch all' checkbox."""
        self.reviews_entry.config(state=tk.DISABLED if self.app.fetch_all_var.get() else tk.NORMAL)

    def import_csv_report(self):
        """
        Load and display a previously generated CSV report.
        
        Parses filename to extract app ID and metadata, then fetches game name
        from cache or Steam API. Populates the report table with imported data.
        """
        filepath = filedialog.askopenfilename(
            title="Select a CSV Report File", filetypes=[("CSV Files", "*.csv")], initialdir="./data/processed/reports"
        )
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                report_data = list(reader)

            if not report_data:
                messagebox.showwarning("Empty File", "The selected CSV file is empty.")
                return
            
            self.tree.delete(*self.tree.get_children())
            
            for row in report_data:
                values = [
                    row.get('Language', ''), row.get('Language_CN', ''),
                    row.get('Total Reviews', ''), row.get('Positive Reviews', ''),
                    row.get('Positive Rate', ''), row.get('Category', ''), row.get('Category_CN', ''),
                    row.get('Avg Games (Pos)', ''), row.get('Avg Games (Neg)', ''),
                    row.get('Avg Playtime@Review (Pos, hrs)', ''), row.get('Avg Playtime@Review (Neg, hrs)', ''),
                    row.get('Avg Playtime Total (Pos, hrs)', ''), row.get('Avg Playtime Total (Neg, hrs)', '')
                ]
                self.tree.insert('', tk.END, values=values)

            filename = os.path.basename(filepath)
            # Parse filename: {appid}_{title}_{date}_{count}_report.csv
            match = re.match(r"(\d+)_(.*)_(\d{4}-\d{2}-\d{2})_(\w+)_report\.csv", filename)
            
            if match:
                appid, title_from_name, date, reviews_str = match.groups()
                appid = int(appid)  # Convert string to integer for utils.get_game_name()
                title = title_from_name.replace('_', ' ')
                reviews = reviews_str.replace('max', '') if 'max' in reviews_str else 'all'
                
                self.update_info_display({
                    'game_title': title, 
                    'appid': appid, 
                    'total_reviews_collected': reviews, 
                    'date_collected_utc': date
                })
            else:
                # Fallback for legacy filename format
                match_old = re.match(r"(.+)_(\d{4}-\d{2}-\d{2})_(\w+)_report\.csv", filename)
                if match_old:
                    title_or_appid, date, reviews_str = match_old.groups()
                    reviews = reviews_str.replace('max', '') if 'max' in reviews_str else 'all'
                    is_appid_only = all(c.isdigit() for c in title_or_appid)
                    
                    appid = int(title_or_appid) if is_appid_only else 'N/A'
                    title = '' if is_appid_only else title_or_appid.replace('_', ' ')

                    self.update_info_display({
                        'game_title': title, 'appid': appid,
                        'total_reviews_collected': reviews, 'date_collected_utc': date
                    })
                else:
                    self.update_info_display({})

            self.status_label.config(text=f"Successfully imported report: {filename}")
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to read CSV.\n\nError: {e}")
            
    def update_info_display(self, metadata):
        """
        Update the information panel with dataset metadata.
        
        Automatically fetches game name from cache or Steam API if app ID is available.
        Falls back to metadata-provided title for legacy data.
        
        Args:
            metadata: Dictionary with 'appid', 'game_title', 'total_reviews_collected', etc.
        """
        appid = metadata.get('appid', 'N/A')
        game_title = utils.get_game_name(appid) if isinstance(appid, int) else metadata.get('game_title', 'N/A')
        total_reviews = metadata.get('total_reviews_collected', 'N/A')
        date_str = metadata.get('date_collected_utc', 'N/A')
        if isinstance(date_str, str): date_str = date_str[:10]
        self.info_title.set(f"Game Title: {game_title}")
        self.info_appid.set(f"App ID: {appid}")
        self.info_total_reviews.set(f"Total Reviews: {total_reviews}")
        self.info_date.set(f"Fetched Date: {date_str}")

    def sort_column(self, col, numeric_cols):
        """
        Sort table by clicked column header.
        
        Handles both numeric and text columns. Toggles sort direction on repeated clicks.
        
        Args:
            col: Column identifier to sort by
            numeric_cols: List of column identifiers that should be sorted numerically
        """
        if col == self.app.sort_by: self.app.sort_reverse = not self.app.sort_reverse
        else: self.app.sort_by, self.app.sort_reverse = col, False
        
        data = [(self.tree.set(item_id, col), item_id) for item_id in self.tree.get_children('')]
        
        def get_sort_key(item):
            value_str = item[0]
            if col in numeric_cols:
                value_str = value_str.strip('%')
                try:
                    return float(value_str)
                except ValueError:
                    return 0.0
            return str(value_str).lower()

        data.sort(key=get_sort_key, reverse=self.app.sort_reverse)
        for index, (_, item_id) in enumerate(data): self.tree.move(item_id, '', index)

    def start_analysis_thread(self):
        """
        Initiate review fetching and analysis in a background thread.
        
        Validates input, checks for resume capability, and spawns a worker thread
        to avoid blocking the UI during long-running operations.
        """
        try:
            appid = int(self.appid_entry.get())
            game_title = utils.get_game_name(appid)

            if self.app.fetch_all_var.get():
                max_pages = None
            else:
                max_reviews = int(self.reviews_entry.get())
                max_pages = math.ceil(max_reviews / 100) if max_reviews > 0 else None
        except (ValueError, tk.TclError):
            messagebox.showerror("Invalid Input", "Please enter a valid number for App ID.")
            return
        
        # Check for checkpoint file to enable resume
        self.app.cancel_event.clear()
        resume = False
        checkpoint_path = os.path.join(backend.TEMP_FOLDER, f"{appid}_checkpoint.json")
        if os.path.exists(checkpoint_path):
            if messagebox.askyesno("Resume Download?", f"An incomplete download was found for App ID {appid}. Would you like to resume?"):
                resume = True
        
        self.fetch_button.config(state=tk.DISABLED)
        self.import_button.config(state=tk.DISABLED)
        self.analyze_json_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.tree.delete(*self.tree.get_children())
        
        thread = threading.Thread(target=self.run_backend_job, args=(appid, max_pages, resume, game_title), daemon=True)
        thread.start()

    def run_backend_job(self, appid, max_pages, resume, game_title):
        """
        Background worker that fetches reviews and generates reports.
        
        Orchestrates the full pipeline: fetch → save JSON → analyze → save CSV.
        Sends results back to UI via status queue.
        
        Args:
            appid: Steam application ID
            max_pages: Maximum pages to fetch (None = all)
            resume: Whether to resume from checkpoint
            game_title: Game name for report generation
        """
        scraped_data = backend.get_all_steam_reviews(
            appid, status_queue=self.app.status_queue, max_pages=max_pages, 
            cancel_event=self.app.cancel_event, resume=resume
        )
        if scraped_data and scraped_data.get('reviews'):
            scraped_data['metadata']['game_title'] = game_title
            backend.save_reviews_to_json(scraped_data, self.app.status_queue)
            report_data = backend.analyze_and_save_report(scraped_data, self.app.status_queue, game_title=game_title)
            if report_data:
                self.app.status_queue.put({'type': 'report', 'data': report_data, 'metadata': scraped_data.get('metadata', {})})
        elif not self.app.cancel_event.is_set():
             self.app.status_queue.put("No reviews were collected. Cannot generate a report.")
        self.app.status_queue.put({'type': 'done'})

    def start_json_analysis_thread(self):
        """
        Analyze a previously saved raw JSON file.
        
        Loads raw review data and generates a new CSV report without re-fetching from Steam.
        """
        filepath = filedialog.askopenfilename(
            title="Select a Raw Review JSON File",
            filetypes=[("JSON Files", "*.json")],
            initialdir="./data/raw"
        )
        if not filepath:
            return
        
        self.fetch_button.config(state=tk.DISABLED)
        self.import_button.config(state=tk.DISABLED)
        self.analyze_json_button.config(state=tk.DISABLED)
        self.tree.delete(*self.tree.get_children())
        
        thread = threading.Thread(target=self.run_json_analysis_job, args=(filepath,), daemon=True)
        thread.start()

    def run_json_analysis_job(self, filepath):
        """
        Background worker for analyzing existing JSON files.
        
        Reads raw review data, fetches game name, generates CSV report,
        and updates UI with results.
        
        Args:
            filepath: Path to the raw review JSON file
        """
        try:
            self.app.status_queue.put(f"Loading and analyzing {os.path.basename(filepath)}...")
            with open(filepath, 'r', encoding='utf-8') as f:
                review_data = json.load(f)

            if review_data and review_data.get('reviews'):
                appid = review_data.get('metadata', {}).get('appid', 'N/A')
                final_title = utils.get_game_name(appid) if isinstance(appid, int) else f"AppID_{appid}"

                if 'metadata' not in review_data: review_data['metadata'] = {}
                review_data['metadata']['game_title'] = final_title
                
                report_data = backend.analyze_and_save_report(review_data, self.app.status_queue, game_title=final_title)
                if report_data:
                    self.app.status_queue.put({'type': 'report', 'data': report_data, 'metadata': review_data.get('metadata', {})})
            else:
                self.app.status_queue.put("JSON file is invalid or contains no reviews.")

        except json.JSONDecodeError:
            self.app.status_queue.put("Error: Invalid JSON format.")
            messagebox.showerror("JSON Error", "The selected file is not a valid JSON file.")
        except Exception as e:
            self.app.status_queue.put(f"An error occurred: {e}")
            messagebox.showerror("Analysis Error", f"An unexpected error occurred:\n\n{e}")
        finally:
            self.app.status_queue.put({'type': 'done'})
    
    def populate_table(self, report_data):
        """
        Display report data in the table view.
        
        Args:
            report_data: List of dictionaries, each representing a row in the report
        """
        self.tree.delete(*self.tree.get_children())
        for row_dict in report_data:
            values = list(row_dict.values())
            self.tree.insert('', tk.END, values=values)
