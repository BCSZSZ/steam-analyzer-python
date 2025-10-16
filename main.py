import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import queue
import threading
import math
import csv
import os
import re
import json

# Import the backend logic
import backend

class SteamReviewApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Steam Review Analysis Tool")
        self.root.geometry("1400x700") # Increased window size for new columns
        self.status_queue = queue.Queue()
        self.sort_by = None
        self.sort_reverse = False
        self.fetch_all_var = tk.BooleanVar(value=False)
        self.cancel_event = threading.Event()
        self.create_widgets()
        self.process_queue()

    def create_widgets(self):
        # --- Input Frame ---
        input_frame = ttk.Frame(self.root, padding="10")
        input_frame.pack(fill=tk.X)

        ttk.Label(input_frame, text="App ID:").pack(side=tk.LEFT, padx=5)
        self.appid_entry = ttk.Entry(input_frame, width=15)
        self.appid_entry.pack(side=tk.LEFT, padx=5)
        self.appid_entry.insert(0, "1022980") # Silksong

        self.fetch_all_checkbox = ttk.Checkbutton(
            input_frame, text="Fetch all available reviews", 
            variable=self.fetch_all_var, command=self.toggle_max_reviews_entry
        )
        self.fetch_all_checkbox.pack(side=tk.LEFT, padx=(20, 5))

        self.reviews_entry = ttk.Entry(input_frame, width=15)
        self.reviews_entry.pack(side=tk.LEFT, padx=5)
        self.reviews_entry.insert(0, "2000")

        self.fetch_button = ttk.Button(input_frame, text="Fetch & Analyze", command=self.start_analysis_thread)
        self.fetch_button.pack(side=tk.LEFT, padx=10)

        # --- NEW: Standalone Analyze from JSON button ---
        self.analyze_json_button = ttk.Button(input_frame, text="Analyze from JSON", command=self.start_json_analysis_thread)
        self.analyze_json_button.pack(side=tk.LEFT, padx=5)

        self.import_button = ttk.Button(input_frame, text="Import Report (CSV)", command=self.import_csv_report)
        self.import_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = ttk.Button(input_frame, text="Cancel", command=self.cancel_download, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # --- Information Display Frame ---
        info_frame = ttk.LabelFrame(self.root, text="Current Data Information", padding="10")
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.info_appid = tk.StringVar(value="App ID: N/A")
        self.info_total_reviews = tk.StringVar(value="Total Reviews: N/A")
        self.info_date = tk.StringVar(value="Fetched Date: N/A")
        
        ttk.Label(info_frame, textvariable=self.info_appid).pack(side=tk.LEFT, padx=20)
        ttk.Label(info_frame, textvariable=self.info_total_reviews).pack(side=tk.LEFT, padx=20)
        ttk.Label(info_frame, textvariable=self.info_date).pack(side=tk.LEFT, padx=20)

        # --- Report Table Frame ---
        table_frame = ttk.Frame(self.root, padding="10")
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
            'avg_play_review_pos': ('Play @ Review (Pos)', 120),
            'avg_play_review_neg': ('Play @ Review (Neg)', 120),
            'avg_play_forever_pos': ('Total Play (Pos)', 110),
            'avg_play_forever_neg': ('Total Play (Neg)', 110)
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

        # --- Status Log Frame ---
        log_frame = ttk.Frame(self.root, padding="10")
        log_frame.pack(fill=tk.X)
        self.status_label = ttk.Label(log_frame, text="Ready.", anchor=tk.W)
        self.status_label.pack(fill=tk.X)

    def cancel_download(self):
        self.status_label.config(text="Cancelling... please wait for the current request to finish.")
        self.cancel_event.set()
        self.cancel_button.config(state=tk.DISABLED)

    def toggle_max_reviews_entry(self):
        self.reviews_entry.config(state=tk.DISABLED if self.fetch_all_var.get() else tk.NORMAL)

    def import_csv_report(self):
        filepath = filedialog.askopenfilename(
            title="Select a CSV Report File", filetypes=[("CSV Files", "*.csv")], initialdir="./reports"
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
            
            # Use the full list of columns to handle old and new CSVs gracefully
            # Missing columns will just be blank, which is the desired behavior
            all_cols = self.tree['columns']
            for row in report_data:
                values = [row.get(col_name, '') for col_name in reader.fieldnames]
                self.tree.insert('', tk.END, values=values)

            filename = os.path.basename(filepath)
            match = re.match(r"(\d+)_(\d{4}-\d{2}-\d{2})_(\w+)_report\.csv", filename)
            if match:
                appid, date, reviews_str = match.groups()
                reviews = reviews_str.replace('max', '') if 'max' in reviews_str else 'all'
                self.update_info_display({'appid': appid, 'total_reviews_collected': reviews, 'date_collected_utc': date})
            else: self.update_info_display({})
            self.status_label.config(text=f"Successfully imported report: {filename}")
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to read CSV.\n\nError: {e}")
            
    def update_info_display(self, metadata):
        appid = metadata.get('appid', 'N/A')
        total_reviews = metadata.get('total_reviews_collected', 'N/A')
        date_str = metadata.get('date_collected_utc', 'N/A')
        if isinstance(date_str, str): date_str = date_str[:10]
        self.info_appid.set(f"App ID: {appid}")
        self.info_total_reviews.set(f"Total Reviews: {total_reviews}")
        self.info_date.set(f"Fetched Date: {date_str}")

    def sort_column(self, col, numeric_cols):
        if col == self.sort_by: self.sort_reverse = not self.sort_reverse
        else: self.sort_by, self.sort_reverse = col, False
        
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

        data.sort(key=get_sort_key, reverse=self.sort_reverse)
        for index, (_, item_id) in enumerate(data): self.tree.move(item_id, '', index)

    def start_analysis_thread(self):
        try:
            appid = int(self.appid_entry.get())
            if self.fetch_all_var.get():
                max_pages = None
            else:
                max_reviews = int(self.reviews_entry.get())
                max_pages = math.ceil(max_reviews / 100) if max_reviews > 0 else None
        except (ValueError, tk.TclError):
            messagebox.showerror("Invalid Input", "Please enter a valid number for App ID.")
            return
        
        self.cancel_event.clear()
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
        
        thread = threading.Thread(target=self.run_backend_job, args=(appid, max_pages, resume), daemon=True)
        thread.start()

    def run_backend_job(self, appid, max_pages, resume):
        scraped_data = backend.get_all_steam_reviews(
            appid, status_queue=self.status_queue, max_pages=max_pages, 
            cancel_event=self.cancel_event, resume=resume
        )
        if scraped_data and scraped_data.get('reviews'):
            backend.save_reviews_to_json(scraped_data, self.status_queue)
            report_data = backend.analyze_and_save_report(scraped_data, self.status_queue)
            if report_data:
                self.status_queue.put({'type': 'report', 'data': report_data, 'metadata': scraped_data.get('metadata', {})})
        elif not self.cancel_event.is_set():
             self.status_queue.put("No reviews were collected. Cannot generate a report.")
        self.status_queue.put({'type': 'done'})

    def start_json_analysis_thread(self):
        """Opens a file dialog to select a JSON and starts the analysis in a thread."""
        filepath = filedialog.askopenfilename(
            title="Select a Raw Review JSON File",
            filetypes=[("JSON Files", "*.json")],
            initialdir="./json" # Start in the json folder
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
        """Loads a JSON file and runs the analysis backend job."""
        try:
            self.status_queue.put(f"Loading and analyzing {os.path.basename(filepath)}...")
            with open(filepath, 'r', encoding='utf-8') as f:
                review_data = json.load(f)

            if review_data and review_data.get('reviews'):
                report_data = backend.analyze_and_save_report(review_data, self.status_queue)
                if report_data:
                    self.status_queue.put({'type': 'report', 'data': report_data, 'metadata': review_data.get('metadata', {})})
            else:
                self.status_queue.put("JSON file is invalid or contains no reviews.")

        except json.JSONDecodeError:
            self.status_queue.put("Error: Invalid JSON format.")
            messagebox.showerror("JSON Error", "The selected file is not a valid JSON file.")
        except Exception as e:
            self.status_queue.put(f"An error occurred: {e}")
            messagebox.showerror("Analysis Error", f"An unexpected error occurred:\n\n{e}")
        finally:
            self.status_queue.put({'type': 'done'})

    def process_queue(self):
        try:
            message = self.status_queue.get_nowait()
            if isinstance(message, dict):
                msg_type = message.get('type')
                if msg_type == 'report':
                    self.populate_table(message['data'])
                    self.update_info_display(message['metadata'])
                elif msg_type == 'done':
                    self.fetch_button.config(state=tk.NORMAL)
                    self.import_button.config(state=tk.NORMAL)
                    self.analyze_json_button.config(state=tk.NORMAL)
                    self.cancel_button.config(state=tk.DISABLED)
                    if not self.cancel_event.is_set():
                        self.status_label.config(text="Process finished.")
            else:
                self.status_label.config(text=message)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def populate_table(self, report_data):
        self.tree.delete(*self.tree.get_children())
        for row_dict in report_data:
            values = list(row_dict.values())
            self.tree.insert('', tk.END, values=values)

if __name__ == "__main__":
    root = tk.Tk()
    app = SteamReviewApp(root)
    root.mainloop()
