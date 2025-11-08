"""
Stopwords Manager Tab - UI for managing custom stopwords.

Provides interface for editing universal and game-specific stopwords
used across all text analysis features (N-gram, TF-IDF, BERTopic).
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from .base_tab import BaseTab


class BERTopicStopwordsTab(BaseTab):
    """
    Tab for managing custom stopwords across all text analysis features.
    
    Features:
    - View/edit universal stopwords (applied to all games)
    - View/edit game-specific stopwords (dual English/CN keys)
    - Table view with double-click editing
    - Auto-load from cache with tokenization
    """
    
    def get_tab_title(self):
        """Return the tab title."""
        return "Stopwords Manager"
    
    def create_ui(self):
        """Create the stopwords editor UI."""
        # Main container
        main_frame = ttk.Frame(self.frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title and description
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(
            title_frame,
            text="Stopwords Manager",
            font=('Arial', 14, 'bold')
        ).pack(anchor='w')
        
        ttk.Label(
            title_frame,
            text="Manage stopwords for all text analysis (N-gram, TF-IDF, BERTopic).\n"
                 "English game names auto-added from cache. Add Chinese terms manually to _CN keys.",
            foreground='gray'
        ).pack(anchor='w', pady=(5, 0))
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=5)
        
        ttk.Button(btn_frame, text="Load Stopwords", command=self.load_stopwords).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Load from Cache", command=self.load_from_cache).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Save Changes", command=self.save_stopwords).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Reset to Default", command=self.reset_stopwords).pack(side='left', padx=5)
        
        self.status_label = ttk.Label(btn_frame, text="", foreground='green')
        self.status_label.pack(side='left', padx=10)
        
        # Content frame with two columns
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        
        # Left column: Universal stopwords
        self._create_universal_section(content_frame)
        
        # Right column: Game-specific stopwords
        self._create_game_specific_section(content_frame)
        
        # Load initial data
        self.load_stopwords()
    
    def _create_universal_section(self, parent):
        """Create universal stopwords section."""
        frame = ttk.LabelFrame(parent, text="Universal Stopwords", padding="10")
        frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        
        # Description
        ttk.Label(
            frame,
            text="Common terms applied to all games and all analysis types",
            foreground='gray',
            wraplength=350
        ).pack(anchor='w', pady=(0, 5))
        
        # Text editor with scrollbar
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.universal_text = tk.Text(
            text_frame,
            wrap='word',
            yscrollcommand=scrollbar.set,
            height=25
        )
        self.universal_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.universal_text.yview)
        
        # Instructions
        ttk.Label(
            frame,
            text="One term per line. Can be English or Chinese.",
            foreground='gray',
            font=('Arial', 9, 'italic')
        ).pack(anchor='w', pady=(5, 0))
    
    def _create_game_specific_section(self, parent):
        """Create game-specific stopwords section with table view."""
        import customtkinter as ctk
        
        frame = ttk.LabelFrame(parent, text="Game-Specific Stopwords", padding="10")
        frame.grid(row=0, column=1, sticky='nsew', padx=(5, 0))
        
        # Description
        ttk.Label(
            frame,
            text="Per-game terms (Double-click to edit, English/CN keys auto-generated)",
            foreground='gray',
            wraplength=350
        ).pack(anchor='w', pady=(0, 5))
        
        # Table view with scrollbars
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for game-specific stopwords
        self.game_tree = ttk.Treeview(
            table_frame,
            columns=('game', 'terms'),
            show='headings',
            height=20
        )
        self.game_tree.heading('game', text='Game Key (Read-only)')
        self.game_tree.heading('terms', text='Terms (Double-click to edit)')
        self.game_tree.column('game', width=200, minwidth=150)
        self.game_tree.column('terms', width=400, minwidth=250)
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.game_tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.game_tree.xview)
        self.game_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.game_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Bind double-click to edit
        self.game_tree.bind('<Double-1>', self.edit_game_terms)
        
        # Instructions
        ttk.Label(
            frame,
            text="Format: appid_gamename and appid_gamename_CN (for Chinese terms)\n"
                 "English keys auto-generated, CN keys blank (add Chinese tokens manually)",
            foreground='gray',
            font=('Arial', 9, 'italic')
        ).pack(anchor='w', pady=(5, 0))
    
    def load_stopwords(self):
        """Load stopwords from file and display in UI."""
        try:
            stopwords_file = 'data/stopwords.json'
            
            # Load directly from file
            if not os.path.exists(stopwords_file):
                # Create default file if doesn't exist
                default_stopwords = {
                    "universal": [
                        "dlc", "jrpg", "rpg", "fps", "moba", "mmo",
                        "spoiler", "review", "game", "gameplay",
                        "游戏", "评分", "好评", "差评",
                        "10", "9", "8", "sp", "ed", "op",
                        "https", "http", "www", "com",
                        "best", "indie", "year"
                    ],
                    "game_specific": {}
                }
                os.makedirs(os.path.dirname(stopwords_file), exist_ok=True)
                with open(stopwords_file, 'w', encoding='utf-8') as f:
                    json.dump(default_stopwords, f, indent=2, ensure_ascii=False)
                stopwords_dict = default_stopwords
            else:
                with open(stopwords_file, 'r', encoding='utf-8') as f:
                    stopwords_dict = json.load(f)
            
            # Populate universal stopwords
            universal = stopwords_dict.get('universal', [])
            self.universal_text.delete('1.0', tk.END)
            self.universal_text.insert('1.0', '\n'.join(universal))
            
            # Populate game-specific stopwords table
            game_specific = stopwords_dict.get('game_specific', {})
            
            # Clear existing items
            for item in self.game_tree.get_children():
                self.game_tree.delete(item)
            
            # Insert items sorted by game key
            for game_key in sorted(game_specific.keys()):
                terms = game_specific[game_key]
                terms_str = ', '.join(terms) if isinstance(terms, list) else str(terms)
                self.game_tree.insert('', 'end', values=(game_key, terms_str))
            
            self.status_label.config(text="✓ Stopwords loaded", foreground='green')
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load stopwords:\n{e}")
            self.status_label.config(text="✗ Load failed", foreground='red')
    
    def load_from_cache(self):
        """Load game names from cached app details and add to game-specific stopwords."""
        try:
            import os
            import re
            
            cache_folder = 'data/cache/app_details'
            
            if not os.path.exists(cache_folder):
                messagebox.showinfo("No Cache", "No cached app details found.\nFetch game data first in the Data Collection tab.")
                return
            
            # Get all cached game files
            cache_files = [f for f in os.listdir(cache_folder) if f.endswith('_details.json')]
            
            if not cache_files:
                messagebox.showinfo("No Cache", "No cached app details found.\nFetch game data first in the Data Collection tab.")
                return
            
            # Parse current game-specific stopwords from table
            existing_games = {}
            for item in self.game_tree.get_children():
                game_key, terms_str = self.game_tree.item(item, 'values')
                terms = [t.strip() for t in terms_str.split(',') if t.strip()]
                if terms:
                    existing_games[game_key] = terms
            
            # Read cached games and add to stopwords
            added_count = 0
            updated_count = 0
            
            for cache_file in cache_files:
                try:
                    # Extract appid from filename
                    appid = cache_file.replace('_details.json', '')
                    
                    # Read game details
                    with open(os.path.join(cache_folder, cache_file), 'r', encoding='utf-8') as f:
                        game_data = json.load(f)
                    
                    game_name = game_data.get('name', '')
                    if not game_name:
                        continue
                    
                    # Create game keys (both English and CN)
                    clean_name = game_name.lower().replace(' ', '_').replace("'", '')
                    game_key = f"{appid}_{clean_name}"
                    game_key_cn = f"{appid}_{clean_name}_CN"
                    
                    # Tokenize English game name
                    tokens = re.findall(r'\w+', game_name.lower())
                    
                    if not tokens:
                        continue
                    
                    # Always regenerate English key (it's auto-generated)
                    if game_key in existing_games:
                        # Update existing English key
                        existing_games[game_key] = tokens
                        updated_count += 1
                    else:
                        # Add new English key
                        existing_games[game_key] = tokens
                        added_count += 1
                    
                    # For CN key: only add if missing, preserve if exists
                    if game_key_cn not in existing_games:
                        existing_games[game_key_cn] = []  # Empty CN key for manual input
                
                except Exception as e:
                    print(f"[WARNING] Failed to process {cache_file}: {e}")
                    continue
            
            # Update table view
            for item in self.game_tree.get_children():
                self.game_tree.delete(item)
            
            for game_key in sorted(existing_games.keys()):
                terms = existing_games[game_key]
                terms_str = ', '.join(terms) if terms else ''
                self.game_tree.insert('', 'end', values=(game_key, terms_str))
            
            self.status_label.config(text=f"✓ Added {added_count} games from cache", foreground='green')
            
            if added_count > 0 or updated_count > 0:
                messagebox.showinfo(
                    "Success",
                    f"Added {added_count} new game(s) from cache.\n"
                    f"Updated {updated_count} existing game(s).\n"
                    f"Each game has 2 keys: appid_name (English) and appid_name_CN (blank).\n"
                    f"Total entries: {len(existing_games)}\n\n"
                    f"Click 'Save Changes' to persist these stopwords."
                )
            else:
                messagebox.showinfo("No Changes", "All cached games are already up to date.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load from cache:\n{e}")
            self.status_label.config(text="✗ Load from cache failed", foreground='red')
    
    def save_stopwords(self):
        """Save edited stopwords back to file."""
        try:
            # Parse universal stopwords
            universal_text = self.universal_text.get('1.0', tk.END).strip()
            universal = [line.strip() for line in universal_text.split('\n') if line.strip()]
            
            # Parse game-specific stopwords from table
            game_specific = {}
            
            for item in self.game_tree.get_children():
                game_key, terms_str = self.game_tree.item(item, 'values')
                terms = [t.strip() for t in terms_str.split(',') if t.strip()]
                
                if terms:
                    game_specific[game_key] = terms
                else:
                    # Keep empty CN keys for manual input later
                    game_specific[game_key] = []
            
            # Create new stopwords dict
            new_stopwords = {
                'universal': universal,
                'game_specific': game_specific
            }
            
            # Save directly to file
            stopwords_file = 'data/stopwords.json'
            os.makedirs(os.path.dirname(stopwords_file), exist_ok=True)
            with open(stopwords_file, 'w', encoding='utf-8') as f:
                json.dump(new_stopwords, f, indent=2, ensure_ascii=False)
            
            self.status_label.config(text="✓ Stopwords saved successfully!", foreground='green')
            messagebox.showinfo("Success", "Stopwords saved successfully!")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save stopwords:\n{e}")
            self.status_label.config(text="✗ Save failed", foreground='red')
    
    def edit_game_terms(self, event):
        """Edit game-specific terms on double-click."""
        try:
            # Get selected item
            selection = self.game_tree.selection()
            if not selection:
                return
            
            item = selection[0]
            game_key, terms_str = self.game_tree.item(item, 'values')
            
            # Create edit dialog
            dialog = tk.Toplevel(self.frame)
            dialog.title(f"Edit Terms for {game_key}")
            dialog.geometry("600x300")
            dialog.transient(self.frame)
            dialog.grab_set()
            
            # Instructions
            ttk.Label(
                dialog,
                text=f"Edit terms for: {game_key}\nSeparate terms with commas. Empty for CN keys is OK.",
                font=('Arial', 10)
            ).pack(padx=10, pady=10, anchor='w')
            
            # Text editor
            text_frame = ttk.Frame(dialog)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            scrollbar = ttk.Scrollbar(text_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_widget = tk.Text(
                text_frame,
                wrap='word',
                yscrollcommand=scrollbar.set,
                height=10
            )
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=text_widget.yview)
            
            # Populate with current terms
            text_widget.insert('1.0', terms_str)
            text_widget.focus_set()
            
            # Buttons
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(fill='x', padx=10, pady=10)
            
            def save_changes():
                new_terms_str = text_widget.get('1.0', tk.END).strip()
                self.game_tree.item(item, values=(game_key, new_terms_str))
                dialog.destroy()
            
            def cancel():
                dialog.destroy()
            
            ttk.Button(btn_frame, text="Save", command=save_changes).pack(side='left', padx=5)
            ttk.Button(btn_frame, text="Cancel", command=cancel).pack(side='left', padx=5)
            
            # Bind Enter to save
            dialog.bind('<Return>', lambda e: save_changes())
            dialog.bind('<Escape>', lambda e: cancel())
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to edit terms:\n{e}")
    
    def reset_stopwords(self):
        """Reset stopwords to default values."""
        result = messagebox.askyesno(
            "Confirm Reset",
            "This will reset ALL stopwords to default values.\n"
            "All custom entries will be lost.\n\n"
            "Are you sure?"
        )
        
        if not result:
            return
        
        try:
            # Reset to default values
            default_stopwords = {
                "universal": [
                    "dlc", "jrpg", "rpg", "fps", "moba", "mmo",
                    "spoiler", "review", "game", "gameplay",
                    "游戏", "评分", "好评", "差评",
                    "10", "9", "8", "sp", "ed", "op",
                    "https", "http", "www", "com",
                    "best", "indie", "year"
                ],
                "game_specific": {}
            }
            
            stopwords_file = 'data/stopwords.json'
            os.makedirs(os.path.dirname(stopwords_file), exist_ok=True)
            with open(stopwords_file, 'w', encoding='utf-8') as f:
                json.dump(default_stopwords, f, indent=2, ensure_ascii=False)
            
            # Reload
            self.load_stopwords()
            
            self.status_label.config(text="✓ Reset to default", foreground='green')
            messagebox.showinfo("Success", "Stopwords reset to default values!")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset stopwords:\n{e}")
            self.status_label.config(text="✗ Reset failed", foreground='red')
