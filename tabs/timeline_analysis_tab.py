"""
Timeline Analysis Tab - visualizes review sentiment and volume over time.

Provides interactive charts showing:
- Rolling average positive rate (configurable window)
- Cumulative positive rate evolution over time
- Language-specific filtering
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import threading
from analyzers.timeline_analyzer import TimelineAnalyzer
from .base_tab import BaseTab
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import webbrowser
import tempfile


class TimelineAnalysisTab(BaseTab):
    """
    Tab for timeline analysis visualization.
    
    Features:
    - Load review data
    - Select language
    - Configure rolling window
    - Generate interactive timeline chart
    """
    
    def get_tab_title(self):
        """Return the tab title."""
        return "Timeline Analysis"
    
    def create_ui(self):
        """Create the timeline analysis UI."""
        # Main container
        main_container = ttk.Frame(self.frame, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # === Data Loading Section ===
        load_frame = ttk.LabelFrame(main_container, text="Data Loading", padding="10")
        load_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(load_frame, text="Load Raw JSON", command=self.load_raw_json).pack(side='left', padx=5)
        
        self.data_info_label = ttk.Label(load_frame, text="No data loaded", foreground='gray')
        self.data_info_label.pack(side='left', padx=10)
        
        # === Analysis Parameters ===
        params_frame = ttk.LabelFrame(main_container, text="Chart Parameters", padding="10")
        params_frame.pack(fill='x', pady=(0, 10))
        
        # Language selection
        lang_frame = ttk.Frame(params_frame)
        lang_frame.pack(fill='x', pady=5)
        
        ttk.Label(lang_frame, text="Language:").pack(side='left', padx=(0, 5))
        self.language_var = tk.StringVar(value='all')
        self.lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.language_var,
            values=['all'],
            state='readonly',
            width=20
        )
        self.lang_combo.pack(side='left', padx=5)
        
        # Rolling window
        window_frame = ttk.Frame(params_frame)
        window_frame.pack(fill='x', pady=5)
        
        ttk.Label(window_frame, text="Rolling Window (days):").pack(side='left', padx=(0, 5))
        self.rolling_window_var = tk.IntVar(value=7)
        window_spin = ttk.Spinbox(
            window_frame,
            from_=1,
            to=90,
            textvariable=self.rolling_window_var,
            width=10
        )
        window_spin.pack(side='left', padx=5)
        ttk.Label(window_frame, text="(default: 7)", foreground='gray').pack(side='left', padx=5)
        
        # Action buttons
        action_frame = ttk.Frame(params_frame)
        action_frame.pack(fill='x', pady=10)
        
        self.analyze_btn = ttk.Button(
            action_frame,
            text="Generate Timeline Chart",
            command=self.generate_chart,
            state='disabled'
        )
        self.analyze_btn.pack(side='left', padx=5)
        
        self.export_btn = ttk.Button(
            action_frame,
            text="Export Data (JSON)",
            command=self.export_data,
            state='disabled'
        )
        self.export_btn.pack(side='left', padx=5)
        
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
        
        # === Info Section ===
        info_frame = ttk.LabelFrame(main_container, text="Current Analysis Info", padding="10")
        info_frame.pack(fill='x', pady=(0, 10))
        
        self.info_text = tk.Text(info_frame, height=8, wrap='word', state='disabled')
        self.info_text.pack(fill='x')
        
        # === Description ===
        desc_frame = ttk.LabelFrame(main_container, text="Chart Description", padding="10")
        desc_frame.pack(fill='both', expand=True)
        
        desc_text = (
            "Timeline Analysis visualizes review sentiment changes over time.\n\n"
            "Two lines are displayed:\n"
            "• Rolling Average (blue): Shows X-day average positive rate (smoothed short-term trend)\n"
            "• Cumulative Rate (red): Shows overall positive rate as it evolved over time\n\n"
            "The chart helps identify:\n"
            "• Launch reception and honeymoon periods\n"
            "• Impact of updates, DLCs, or controversies\n"
            "• Long-term sentiment trajectory\n"
            "• Whether recent reviews are better or worse than historical average\n\n"
            "Interactive features: Zoom, pan, hover for details. Opens in browser."
        )
        
        ttk.Label(desc_frame, text=desc_text, justify='left', foreground='gray').pack(anchor='w')
        
        # Store state
        self.current_data = None
        self.current_results = None
        self.analyzer = TimelineAnalyzer()
    
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
            
            # Get available languages
            languages = self.analyzer.get_available_languages(json_data)
            languages.insert(0, 'all')
            self.lang_combo.config(values=languages)
            self.language_var.set('all')
            
            # Update UI
            metadata = json_data.get('metadata', {})
            total_reviews = len(json_data.get('reviews', []))
            appid = metadata.get('appid', 'N/A')
            game_title = metadata.get('game_title', 'N/A')
            
            self.data_info_label.config(
                text=f"Loaded: {game_title} | {total_reviews:,} reviews | App ID: {appid}",
                foreground='green'
            )
            
            self.analyze_btn.config(state='normal')
            self.clear_btn.config(state='normal')
            
            messagebox.showinfo("Success", f"Loaded {total_reviews:,} reviews from {game_title}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")
    
    def generate_chart(self):
        """Generate and display timeline chart."""
        if not self.current_data:
            messagebox.showwarning("No Data", "Please load a JSON file first.")
            return
        
        language = self.language_var.get()
        rolling_window = self.rolling_window_var.get()
        
        if rolling_window < 1:
            messagebox.showwarning("Invalid Window", "Rolling window must be at least 1 day.")
            return
        
        # Disable UI
        self.analyze_btn.config(state='disabled')
        self.status_label.config(text="Analyzing timeline data...", foreground='blue')
        
        def run_analysis():
            try:
                results = self.analyzer.analyze(
                    self.current_data,
                    language=language,
                    rolling_window=rolling_window
                )
                
                self.frame.after(0, lambda: self.on_analysis_complete(results))
            
            except Exception as e:
                error_msg = str(e)
                self.frame.after(0, lambda: self.on_analysis_error(error_msg))
        
        thread = threading.Thread(target=run_analysis, daemon=True)
        thread.start()
    
    def on_analysis_complete(self, results):
        """Handle analysis completion and generate chart."""
        if 'error' in results:
            messagebox.showerror("Analysis Error", results['error'])
            self.status_label.config(text="", foreground='blue')
            self.analyze_btn.config(state='normal')
            return
        
        self.current_results = results
        
        # Update info display
        self._update_info_display(results)
        
        # Generate and open chart
        try:
            fig = self._create_plotly_chart(results)
            self._open_plotly_in_browser(fig)
            
            self.status_label.config(text="✓ Chart generated and opened in browser!", foreground='green')
            self.export_btn.config(state='normal')
        
        except Exception as e:
            messagebox.showerror("Chart Error", f"Failed to generate chart:\n{e}")
            self.status_label.config(text="", foreground='blue')
        
        self.analyze_btn.config(state='normal')
    
    def on_analysis_error(self, error_msg):
        """Handle analysis error."""
        messagebox.showerror("Error", f"Analysis failed:\n{error_msg}")
        self.status_label.config(text="", foreground='blue')
        self.analyze_btn.config(state='normal')
    
    def _update_info_display(self, results):
        """Update info text with analysis results."""
        metadata = results['metadata']
        
        info_text = (
            f"Total Reviews: {metadata['total_reviews']:,}\n"
            f"Positive Reviews: {metadata['total_positive']:,}\n"
            f"Negative Reviews: {metadata['total_negative']:,}\n"
            f"Overall Positive Rate: {metadata['overall_positive_rate']:.2f}%\n"
            f"Language Filter: {metadata['language']}\n"
            f"Rolling Window: {metadata['rolling_window']} days\n"
            f"Date Range: {metadata['date_range']['start']} to {metadata['date_range']['end']}"
        )
        
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', tk.END)
        self.info_text.insert('1.0', info_text)
        self.info_text.config(state='disabled')
    
    def _create_plotly_chart(self, results):
        """
        Create interactive Plotly timeline chart.
        
        Shows two lines:
        - Rolling average positive rate
        - Cumulative positive rate
        """
        timeline = results['timeline']
        metadata = results['metadata']
        
        if not timeline:
            raise ValueError("No timeline data to visualize")
        
        # Extract data
        dates = [point['date'] for point in timeline]
        rolling_rates = [point['rolling_rate'] for point in timeline]
        cumulative_rates = [point['cumulative_rate'] for point in timeline]
        daily_totals = [point['daily_total'] for point in timeline]
        
        # Create figure
        fig = go.Figure()
        
        # Add rolling average line
        fig.add_trace(go.Scatter(
            x=dates,
            y=rolling_rates,
            mode='lines',
            name=f'{metadata["rolling_window"]}-day Rolling Avg',
            line=dict(color='#2196F3', width=2.5),
            hovertemplate='<b>%{x}</b><br>' +
                         f'{metadata["rolling_window"]}-day Avg: ' + '%{y:.2f}%<br>' +
                         '<extra></extra>'
        ))
        
        # Add cumulative rate line
        fig.add_trace(go.Scatter(
            x=dates,
            y=cumulative_rates,
            mode='lines',
            name='Cumulative Rate',
            line=dict(color='#F44336', width=2, dash='dash'),
            hovertemplate='<b>%{x}</b><br>' +
                         'Cumulative Rate: %{y:.2f}%<br>' +
                         '<extra></extra>'
        ))
        
        # Update layout
        game_title = self.current_data.get('metadata', {}).get('game_title', 'Unknown Game')
        language_display = metadata['language'].upper() if metadata['language'] != 'all' else 'All Languages'
        
        fig.update_layout(
            title=dict(
                text=f"Review Sentiment Timeline - {game_title}<br><sub>{language_display}</sub>",
                x=0.5,
                xanchor='center'
            ),
            xaxis=dict(
                title='Date',
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)'
            ),
            yaxis=dict(
                title='Positive Rate (%)',
                range=[0, 100],
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)'
            ),
            hovermode='x unified',
            template='plotly_white',
            width=1400,
            height=700,
            legend=dict(
                x=0.01,
                y=0.99,
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='rgba(0,0,0,0.2)',
                borderwidth=1
            )
        )
        
        return fig
    
    def _open_plotly_in_browser(self, fig):
        """Open Plotly figure in web browser."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8')
        fig.write_html(temp_file.name)
        temp_file.close()
        webbrowser.open('file://' + temp_file.name)
    
    def export_data(self):
        """Export timeline analysis results to JSON."""
        if not self.current_results:
            messagebox.showwarning("No Results", "Please generate a chart first.")
            return
        
        metadata = self.current_results['metadata']
        appid = self.current_data.get('metadata', {}).get('appid', 'unknown')
        game_name = self.current_data.get('metadata', {}).get('game_title', 'unknown')
        language = metadata['language']
        
        default_filename = f"{appid}_{game_name}_{language}_timeline.json"
        
        filepath = filedialog.asksaveasfilename(
            title="Export Timeline Data",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialdir="./data/processed/insights",
            initialfile=default_filename
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.current_results, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Success", f"Timeline data exported to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export:\n{e}")
    
    def clear_data(self):
        """Clear loaded data and results."""
        self.current_data = None
        self.current_results = None
        
        self.data_info_label.config(text="No data loaded", foreground='gray')
        self.status_label.config(text="", foreground='blue')
        
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', tk.END)
        self.info_text.config(state='disabled')
        
        self.lang_combo.config(values=['all'])
        self.language_var.set('all')
        self.rolling_window_var.set(7)
        
        self.analyze_btn.config(state='disabled')
        self.export_btn.config(state='disabled')
        self.clear_btn.config(state='disabled')
