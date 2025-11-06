"""
BERTopic Stopwords Editor Tab - UI for managing custom stopwords.

Provides interface for editing universal and game-specific stopwords
used in BERTopic analysis to improve topic quality.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
from .base_tab import BaseTab


class BERTopicStopwordsTab(BaseTab):
    """
    Tab for editing BERTopic custom stopwords.
    
    Features:
    - View/edit universal stopwords
    - View/edit game-specific stopwords
    - Add/remove terms
    - Save changes
    """
    
    def get_tab_title(self):
        """Return the tab title."""
        return "BERTopic Stopwords"
    
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
            text="BERTopic Stopwords Editor",
            font=('Arial', 14, 'bold')
        ).pack(anchor='w')
        
        ttk.Label(
            title_frame,
            text="Manage stopwords to filter out common/irrelevant terms from topic analysis.\n"
                 "English game names are auto-added. Add Chinese game names manually if needed.",
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
            text="Common gaming terms and numbers (applied to all games)",
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
        """Create game-specific stopwords section."""
        frame = ttk.LabelFrame(parent, text="Game-Specific Stopwords", padding="10")
        frame.grid(row=0, column=1, sticky='nsew', padx=(5, 0))
        
        # Description
        ttk.Label(
            frame,
            text="Per-game terms (English names auto-added, add Chinese manually)",
            foreground='gray',
            wraplength=350
        ).pack(anchor='w', pady=(0, 5))
        
        # Text editor with scrollbar
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.game_specific_text = tk.Text(
            text_frame,
            wrap='word',
            yscrollcommand=scrollbar.set,
            height=25
        )
        self.game_specific_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.game_specific_text.yview)
        
        # Instructions
        ttk.Label(
            frame,
            text="Format: appid_gamename: term1, term2, term3\n"
                 "English names auto-added. Add Chinese names manually (split into tokens).\n"
                 "Example: 1030300_astlibra_revision: astlibra, revision, 神之, 天平",
            foreground='gray',
            font=('Arial', 9, 'italic')
        ).pack(anchor='w', pady=(5, 0))
    
    def load_stopwords(self):
        """Load stopwords from file and display in UI."""
        try:
            # Import here to avoid circular imports
            from analyzers.bertopic_analyzer import BERTopicAnalyzer
            
            analyzer = BERTopicAnalyzer()
            stopwords_dict = analyzer.get_stopwords_dict()
            
            # Populate universal stopwords
            universal = stopwords_dict.get('universal', [])
            self.universal_text.delete('1.0', tk.END)
            self.universal_text.insert('1.0', '\n'.join(universal))
            
            # Populate game-specific stopwords
            game_specific = stopwords_dict.get('game_specific', {})
            self.game_specific_text.delete('1.0', tk.END)
            
            lines = []
            for game_key, terms in game_specific.items():
                terms_str = ', '.join(terms)
                lines.append(f"{game_key}: {terms_str}")
            
            self.game_specific_text.insert('1.0', '\n'.join(lines))
            
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
            
            # Parse current game-specific stopwords
            game_specific_text = self.game_specific_text.get('1.0', tk.END).strip()
            existing_games = {}
            
            for line in game_specific_text.split('\n'):
                line = line.strip()
                if not line or ':' not in line:
                    continue
                game_key, terms_str = line.split(':', 1)
                game_key = game_key.strip()
                terms = [t.strip() for t in terms_str.split(',') if t.strip()]
                if terms:
                    existing_games[game_key] = terms
            
            # Read cached games and add to stopwords
            added_count = 0
            
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
                    
                    # Create game key
                    clean_name = game_name.lower().replace(' ', '_').replace("'", '')
                    game_key = f"{appid}_{clean_name}"
                    
                    # Skip if already exists
                    if game_key in existing_games:
                        continue
                    
                    # Tokenize English game name
                    tokens = re.findall(r'\w+', game_name.lower())
                    
                    if tokens:
                        existing_games[game_key] = tokens
                        added_count += 1
                
                except Exception as e:
                    print(f"[WARNING] Failed to process {cache_file}: {e}")
                    continue
            
            # Update text editor
            lines = []
            for game_key, terms in existing_games.items():
                terms_str = ', '.join(terms)
                lines.append(f"{game_key}: {terms_str}")
            
            self.game_specific_text.delete('1.0', tk.END)
            self.game_specific_text.insert('1.0', '\n'.join(lines))
            
            self.status_label.config(text=f"✓ Added {added_count} games from cache", foreground='green')
            
            if added_count > 0:
                messagebox.showinfo(
                    "Success",
                    f"Added {added_count} game(s) from cache.\n"
                    f"Total games: {len(existing_games)}\n\n"
                    f"Click 'Save Changes' to persist these stopwords."
                )
            else:
                messagebox.showinfo("No New Games", "All cached games are already in stopwords.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load from cache:\n{e}")
            self.status_label.config(text="✗ Load from cache failed", foreground='red')
    
    def save_stopwords(self):
        """Save edited stopwords back to file."""
        try:
            # Parse universal stopwords
            universal_text = self.universal_text.get('1.0', tk.END).strip()
            universal = [line.strip() for line in universal_text.split('\n') if line.strip()]
            
            # Parse game-specific stopwords
            game_specific_text = self.game_specific_text.get('1.0', tk.END).strip()
            game_specific = {}
            
            for line in game_specific_text.split('\n'):
                line = line.strip()
                if not line or ':' not in line:
                    continue
                
                game_key, terms_str = line.split(':', 1)
                game_key = game_key.strip()
                terms = [t.strip() for t in terms_str.split(',') if t.strip()]
                
                if terms:
                    game_specific[game_key] = terms
            
            # Create new stopwords dict
            new_stopwords = {
                'universal': universal,
                'game_specific': game_specific
            }
            
            # Save via analyzer
            from analyzers.bertopic_analyzer import BERTopicAnalyzer
            analyzer = BERTopicAnalyzer()
            analyzer.update_stopwords_dict(new_stopwords)
            
            self.status_label.config(text="✓ Stopwords saved successfully!", foreground='green')
            messagebox.showinfo("Success", "Stopwords saved successfully!")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save stopwords:\n{e}")
            self.status_label.config(text="✗ Save failed", foreground='red')
    
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
            import os
            
            # Delete the stopwords file
            stopwords_file = 'data/bertopic_stopwords.json'
            if os.path.exists(stopwords_file):
                os.remove(stopwords_file)
            
            # Reload (will create default)
            self.load_stopwords()
            
            self.status_label.config(text="✓ Reset to default", foreground='green')
            messagebox.showinfo("Success", "Stopwords reset to default values!")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset stopwords:\n{e}")
            self.status_label.config(text="✗ Reset failed", foreground='red')
