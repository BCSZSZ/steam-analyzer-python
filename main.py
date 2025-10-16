import customtkinter as ctk
import tkinter.ttk as ttk
from tkinter import messagebox
import threading
import queue
import time
import datetime
import os
import json

# Import the backend logic
import backend

# --- GUI Application Class ---

class SteamReviewerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Steam Review Fetcher & Analyzer")
        self.geometry("1200x700")
        self.minsize(900, 600)
        ctk.set_appearance_mode("System")

        self.grid_columnconfigure(0, weight=1, minsize=280)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # --- Left Frame ---
        self.left_frame = ctk.CTkFrame(self, width=300, corner_radius=10)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.left_frame.grid_propagate(False)
        self.left_frame.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(self.left_frame, text="Control Panel", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(10, 20), sticky="ew")

        ctk.CTkLabel(self.left_frame, text="Steam App ID:").grid(row=1, column=0, padx=20, pady=(10, 5), sticky="w")
        self.appid_entry = ctk.CTkEntry(self.left_frame, placeholder_text="e.g., 570")
        self.appid_entry.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(self.left_frame, text="Number of Reviews:").grid(row=3, column=0, padx=20, pady=(10, 5), sticky="w")
        review_options = [str(i * 1000) for i in range(1, 11)] + ["All"]
        self.reviews_combobox = ctk.CTkComboBox(self.left_frame, values=review_options)
        self.reviews_combobox.set("1000")
        self.reviews_combobox.grid(row=4, column=0, padx=20, pady=5, sticky="new")
        
        self.start_button = ctk.CTkButton(self.left_frame, text="Fetch & Analyze", command=self.start_processing_thread)
        self.start_button.grid(row=5, column=0, padx=20, pady=20, sticky="ew")

        ctk.CTkLabel(self.left_frame, text="Logs:").grid(row=6, column=0, padx=20, pady=(10, 5), sticky="w")
        self.log_textbox = ctk.CTkTextbox(self.left_frame, state="disabled")
        self.log_textbox.grid(row=7, column=0, padx=20, pady=(5, 20), sticky="nsew")
        self.left_frame.grid_rowconfigure(7, weight=1)

        # --- Right Frame ---
        self.right_frame = ctk.CTkFrame(self, corner_radius=10)
        self.right_frame.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        self.setup_treeview()
        
        # --- Threading Queue ---
        self.queue = queue.Queue()
        self.after(100, self.process_queue)

    def setup_treeview(self):
        style = ttk.Style(self)
        is_dark = ctk.get_appearance_mode() == "Dark"

        # --- Define Colors ---
        bg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        text_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        header_bg = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        
        # Subtle stripe colors
        stripe1 = bg_color
        stripe2 = "#EAECEE" if not is_dark else "#2E2E2E"

        style.theme_use("default")
        style.configure("Treeview", background=bg_color, foreground=text_color, fieldbackground=bg_color, borderwidth=0, rowheight=25)
        style.configure("Treeview.Heading", background=header_bg, foreground=text_color, relief="flat", font=('Calibri', 10, 'bold'))
        style.map("Treeview.Heading", background=[('active', ctk.ThemeManager.theme["CTkButton"]["hover_color"])])

        # --- Create Treeview ---
        columns = ('lang_cn', 'total', 'positive', 'rate', 'cat_cn')
        self.tree = ttk.Treeview(self.right_frame, columns=columns, show='headings', style="Treeview")
        
        # --- Define Tags directly on the Treeview widget (more robust) ---
        self.tree.tag_configure("oddrow", background=stripe1)
        self.tree.tag_configure("evenrow", background=stripe2)

        bold_font = ctk.CTkFont(weight="bold")
        category_colors = {
            "OverwhelminglyPositive": "#1a9657", "VeryPositive": "#56a14d",
            "MostlyPositive": "#80b918", "Mixed": "#f9c74f",
            "MostlyNegative": "#f8961e", "VeryNegative": "#f3722c",
            "OverwhelminglyNegative": "#f94144", "NoReviews": text_color
        }
        for category, color in category_colors.items():
            self.tree.tag_configure(category, foreground=color, font=bold_font)

        # --- Configure Columns ---
        headings = {
            'lang_cn': ('Language', 150), 'total': ('Total', 80), 
            'positive': ('Positive', 80), 'rate': ('Rate', 80), 
            'cat_cn': ('Category', 120)
        }
        for col, (text, width) in headings.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor='center')

        self.tree.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    def log_message(self, message):
        self.queue.put(("log", message))

    def process_queue(self):
        try:
            msg_type, data = self.queue.get_nowait()
            if msg_type == "log":
                self.log_textbox.configure(state="normal")
                self.log_textbox.insert("end", data + "\n")
                self.log_textbox.see("end")
                self.log_textbox.configure(state="disabled")
            elif msg_type == "analysis_complete":
                self.populate_treeview(data)
            elif msg_type == "processing_finished":
                self.start_button.configure(state="normal", text="Fetch & Analyze")
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def start_processing_thread(self):
        appid_str = self.appid_entry.get()
        if not appid_str.isdigit():
            messagebox.showerror("Invalid Input", "App ID must be a number.")
            return

        self.start_button.configure(state="disabled", text="Working...")
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        
        for i in self.tree.get_children():
            self.tree.delete(i)

        thread = threading.Thread(target=self.worker_task, daemon=True)
        thread.start()

    def worker_task(self):
        try:
            appid = int(self.appid_entry.get())
            num_reviews_str = self.reviews_combobox.get()
            
            max_pages = None
            if num_reviews_str.isdigit():
                max_pages = int(num_reviews_str) // 100
                
            scraped_data = backend.get_all_steam_reviews(appid, self.log_message, max_pages)
            
            if not scraped_data or not scraped_data.get('reviews'):
                self.log_message("Failed to retrieve reviews or no reviews found.")
                return

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"reviews_{appid}_{num_reviews_str}_{timestamp}.json"
            csv_filename = f"analysis_{appid}_{num_reviews_str}_{timestamp}.csv"

            try:
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(scraped_data, f, ensure_ascii=False, indent=4)
                self.log_message(f"Successfully saved {len(scraped_data['reviews'])} reviews to '{os.path.basename(json_filename)}'")
            except IOError as e:
                self.log_message(f"Error saving JSON file: {e}")
                return

            backend.analyze_and_report(json_filename, csv_filename, self.log_message)
            if os.path.exists(csv_filename):
                self.queue.put(("analysis_complete", csv_filename))
            
            os.remove(json_filename)
            self.log_message(f"Cleaned up temporary file: {os.path.basename(json_filename)}")

        except Exception as e:
            self.log_message(f"An unexpected error occurred: {e}")
        finally:
            self.queue.put(("processing_finished", None))
            
    def populate_treeview(self, csv_filepath):
        try:
            with open(csv_filepath, 'r', encoding='utf-8-sig') as f:
                reader = backend.csv.DictReader(f)
                for i, row in enumerate(reader):
                    values = (
                        row['Language_CN'], row['Total Reviews'],
                        row['Positive Reviews'], row['Positive Rate'],
                        row['Category_CN']
                    )
                    
                    stripe_tag = "evenrow" if i % 2 == 0 else "oddrow"
                    category_tag = row['Category'].replace(' ', '')
                    
                    self.tree.insert('', 'end', values=values, tags=(stripe_tag, category_tag))
            self.log_message(f"Displayed report from '{os.path.basename(csv_filepath)}'")
        except Exception as e:
            self.log_message(f"Failed to read or display CSV file: {e}")

if __name__ == "__main__":
    app = SteamReviewerApp()
    app.mainloop()

