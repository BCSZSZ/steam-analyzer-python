# Steam Review Analyzer

A Python GUI application for fetching, analyzing, and visualizing Steam user reviews with advanced text analysis. Features multi-language support, N-gram analysis, TF-IDF distinctive term extraction, and word cloud visualization.

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Analysis Features](#analysis-features)
- [Project Structure](#project-structure)
- [Data Outputs](#data-outputs)
- [Roadmap](#roadmap)
- [License](#license)

## ✨ Features

### Data Collection & Management
- **Smart Fetching**: Steam API integration with automatic checkpoint every 50 pages
- **Resume Capability**: Pick up interrupted downloads from any checkpoint file
- **Console Logging**: Real-time progress tracking with percentage, timing, and cursor info
- **Game Name Caching**: Automatic retrieval and caching of game titles from Steam Store API

### Analysis Modules
- **Language Reports**: CSV exports with sentiment stats for 20+ languages
- **Extreme Reviews**: Longest playtime reviews grouped by language with filtering
- **N-gram Analysis**: Common phrase extraction (bigrams/trigrams) with word clouds
- **TF-IDF Analysis**: Distinctive term identification (positive vs negative sentiment)
- **Timeline Analysis**: Interactive charts with auto-determined rolling window, dual y-axes for rates and counts
- **Text Insights Dashboard**: Quick overview panel with navigation to detailed analysis

### Customization & Visualization
- **Stopwords Manager**: Table-based editor for universal and game-specific stopwords (dual-key system)
- **Word Clouds**: High-quality visualizations with Chinese font auto-detection, horizontal layout
- **Interactive Charts**: Plotly timeline graphs (1800x900) opening in browser with zoom/pan/hover
- **Multi-language NLP**: NLTK (English) and Jieba (Chinese) with customizable tokenization

---

## � Installation

### Prerequisites

- Python 3.8+
- pip package manager

### Setup

1. Clone repository:

```bash
git clone https://github.com/BCSZSZ/steam-analyzer-python.git
cd steam-analyzer-python
```

2. Create virtual environment (recommended):

```bash
python -m venv venv
# Windows: .\venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run application:

```bash
python main.py
```

---

## 🎯 Usage Guide

### 1. Data Collection Tab

**Fetch Reviews**:
- Enter Steam App ID (e.g., `1030300` for Hollow Knight: Silksong, `1091500` for Cyberpunk 2077)
- Choose review count (1000 for quick test, "all" for complete dataset)
- Click "Fetch & Analyze" → Downloads reviews + generates CSV language report
- Watch console for real-time progress: `[FETCH] Page 1 | Reviews: +100 (Total: 100 / 5,000 = 2.0%) | Time: 0.85s`

**Resume Downloads**:
- If download is interrupted (network error, cancel, etc.), checkpoint is auto-saved
- Click "Resume from Checkpoint" → Select checkpoint file → Continues from where it stopped
- Checkpoints are saved every 50 pages and on any error

### 2. Timeline Analysis Tab ⭐ NEW

- Load raw JSON file from `data/raw/`
- Select language filter (or "all" for combined)
- Set rolling window (0 = auto-determine based on date range, or 1-90 days manually)
- Click "Generate Timeline Chart" → Opens interactive graph in browser
- **Chart shows 4 lines**:
  - 🔵 Rolling Average Rate (dotted blue) - smoothed positive rate trend
  - 🔴 Cumulative Rate (dotted red) - overall positive rate evolution
  - 🟢 Cumulative Review Count (solid green) - total reviews over time
  - 🟠 Cumulative Positive Count (solid orange) - positive reviews over time

### 3. Extreme Reviews Tab

- Load raw JSON or saved results
- View "playtime battles": reviews with longest playtime per language
- Filter by language using checkboxes (default: English + Chinese)
- Great for finding dedicated players' opinions

### 4. N-gram Analysis Tab

- Load raw JSON file
- Select language, sentiment (positive/negative/all), N-gram size (bigrams/trigrams)
- Set minimum frequency threshold (filters out rare phrases)
- Click "Analyze" → View frequency table
- Click "Generate Word Cloud" → Popup window with visualization (horizontal layout, save button)

### 5. TF-IDF Analysis Tab

- Load raw JSON file
- Select language, N-gram range (2-2 for bigrams, 2-3 for bigrams+trigrams)
- Set top N terms to display (e.g., 30)
- Click "Analyze" → View distinctive terms table
- Click "Generate Word Clouds" → 2 popup windows (green=positive, red=negative)
- Shows which phrases are unique to positive vs negative reviews

### 6. Text Insights Dashboard

- Load raw JSON file
- Select language
- View quick overview of top N-grams and TF-IDF terms in one screen
- Navigate to detailed tabs for deeper analysis

### 7. Stopwords Manager Tab

- **Universal Stopwords**: Apply to all games (e.g., "game", "play", "fun")
- **Game-Specific Stopwords**: Apply to specific App ID (e.g., "hollow", "knight" for 1030300)
- Table view with dual keys: English (`{appid}_{game_name}`) and Chinese (`{appid}_{game_name}_CN`)
- Double-click to edit terms (comma-separated)
- Click "Save" to apply changes (affects N-gram, TF-IDF, BERTopic analysis)
- Auto-loads on application startup

---

## 🔍 Analysis Features

### Language Report (CSV)

- Reviews grouped by language with sentiment statistics (20+ languages)
- Steam category assignment (Overwhelmingly Positive, Mixed, Negative, etc.)
- Playtime metrics (average, median) and user profile counts
- Excel-compatible format for further analysis

### Timeline Analysis ⭐

- **Auto-Determined Rolling Window**: Intelligent window size based on date range
  - <30 days → 3-day window
  - 30-90 days → 7-day window
  - 90-180 days → 14-day window
  - 180-365 days → 30-day window
  - >365 days → 60-day window
- **Divide-by-Zero Failover**: Uses previous day's rate when no reviews in window
- **Dual Y-Axes**: Percentage rates (0-100%) on left, review counts on right
- **4 Data Lines**: Rolling average, cumulative rate, cumulative count, cumulative positive count
- **Visual Grouping**: Dotted lines for rates, solid lines for counts
- **Interactive Plotly Charts**: Zoom, pan, hover tooltips, opens in browser (1800x900)

### N-gram Analysis

- Extract common phrases (bigrams/trigrams only, unigrams excluded for clarity)
- Language-specific tokenization (NLTK for English, Jieba for Chinese)
- Repetitive N-gram filtering (e.g., "really really really" excluded)
- Custom stopwords (universal + game-specific from Stopwords Manager)
- Frequency-based word clouds with horizontal layout

### TF-IDF Analysis

- Identify distinctive terms using scikit-learn TF-IDF vectorization
- Compare positive vs negative sentiment vocabulary
- Distinctiveness scoring for term importance (shows what makes each sentiment unique)
- Dual word clouds (green for positive, red for negative)
- Custom stopwords integration

### Word Cloud Generation

- Horizontal text only (no vertical words, easier to read)
- Balanced font sizes (`relative_scaling=0.3` reduces variance)
- Automatic Chinese font detection (Windows: SimHei/YaHei, macOS: PingFang, Linux: WQY)
- Popup windows with save button and right-click support
- High resolution (1200x600 for N-gram, 600x600 per TF-IDF)

### Stopwords Management

- **Universal Stopwords**: Common words to exclude from all games ("game", "play", etc.)
- **Game-Specific Stopwords**: Exclude game-specific terms (e.g., game title words)
- **Dual-Key System**: English key + Chinese key per game for multi-language support
- **Table View**: Editable grid with game name (read-only) and terms (editable)
- **Auto-Load**: Loads on app startup, applies to N-gram, TF-IDF, BERTopic analysis

## 📁 Project Structure

```
steam-analyzer-python/
├── main.py                      # Application entry point
├── backend.py                   # Steam API fetching
├── utils.py                     # Game name caching
├── requirements.txt             # Dependencies
├── analyzers/                   # Analysis modules (plugin-based)
│   ├── base_analyzer.py         # Abstract base class
│   ├── language_report.py       # CSV report generation
│   ├── playtime_extremes.py     # Extreme review finder
│   ├── ngram_analyzer.py        # N-gram frequency extraction
│   ├── tfidf_analyzer.py        # TF-IDF vectorization
│   ├── timeline_analyzer.py     # Time-series sentiment analysis
│   ├── text_processor.py        # NLP utilities (tokenization, stopwords, n-grams)
│   └── wordcloud_generator.py   # Word cloud image generation
├── tabs/                        # UI tab modules (plugin-based)
│   ├── base_tab.py              # Abstract base class
│   ├── data_collection_tab.py   # Fetch & analyze with resume capability
│   ├── extreme_reviews_tab.py   # Extreme reviews visualization
│   ├── timeline_analysis_tab.py # Interactive timeline charts
│   ├── text_insights_tab.py     # Quick analysis dashboard
│   ├── ngram_analysis_tab.py    # N-gram frequency analysis
│   ├── tfidf_analysis_tab.py    # TF-IDF distinctive terms
│   └── bertopic_stopwords_tab.py # Stopwords manager (universal + game-specific)
└── data/                        # Data storage (auto-created)
    ├── raw/                     # Raw review JSON files
    ├── processed/
    │   ├── reports/             # CSV reports
    │   └── insights/            # JSON analysis results
    └── cache/                   # Checkpoints & game name cache
```

### Architecture Highlights

- **Plugin Architecture**: Tabs and analyzers inherit from base classes for easy extensibility
- **Single-Pass Algorithms**: O(n) complexity for efficient large dataset processing
- **Smart Checkpointing**: Auto-save every 50 pages, on empty page, cancel, or any exception
- **Resume Workflow**: File picker to select any checkpoint, continues from saved cursor
- **Separate Checkpoint Files**: Raw data and checkpoint metadata stored separately, checkpoints deleted on completion
- **Language-Specific NLP**: NLTK (English) and Jieba (Chinese) with customizable stopwords
- **Thread-Safe UI**: Background workers with queue-based updates, no UI freezing
- **Cache-First Pattern**: Game names cached locally to minimize Steam Store API calls
- **Consolidated Logging**: Single `[FETCH]` log line per page with progress %, timing, cursor

## 💾 Data Outputs

### File Naming Convention

- **Raw JSON**: `{appid}_{YYYY-MM-DD}_{HH-MM-SS}_{target}_{current}_reviews.json`
  - Example: `1030300_2025-11-06_14-30-00_5000_2500_reviews.json`
- **Checkpoint**: `{appid}_{YYYY-MM-DD}_{HH-MM-SS}_{target}_{current}_checkpoint.json`
  - Contains cursor, metadata for resuming
- **CSV Report**: `{appid}_{game_name}_{date}_all_report.csv`
- **N-gram Analysis**: `{appid}_{game_name}_{language}_{sentiment}_ngrams_{date}.json`
- **TF-IDF Analysis**: `{appid}_{game_name}_{language}_tfidf_{date}.json`
- **Timeline Analysis**: `{appid}_{game_name}_{language}_timeline_{date}.json`
- **Extreme Reviews**: `{appid}_extreme_reviews_by_language_{date}.json`

### Storage Structure

- `data/raw/` - Raw review JSON files (source data)
- `data/processed/reports/` - CSV language reports (Excel-compatible)
- `data/processed/insights/` - JSON analysis results (all tabs)
- `data/cache/` - Checkpoints (auto-deleted on completion) + app_details cache
- `data/stopwords.json` - Custom stopwords (universal + game-specific with dual keys)

---

## 🗺️ Roadmap

### Completed ✅ (November 2025)

- [x] Steam API fetching with checkpoint/resume system
- [x] Consolidated fetch logging with progress tracking
- [x] Multi-language CSV reports with sentiment analysis
- [x] Extreme playtime analysis with language filtering
- [x] N-gram frequency analysis (bigrams/trigrams) with word clouds
- [x] TF-IDF distinctive term extraction with dual word clouds
- [x] Timeline sentiment analysis with auto-determined rolling window
- [x] Interactive Plotly charts (dual y-axes, 4 lines, 1800x900)
- [x] Universal stopwords manager with table view and dual-key system
- [x] Text Insights Dashboard for quick overview
- [x] Game name caching from Steam Store API

### In Progress 🚧

- [ ] BERTopic integration for advanced topic modeling
- [ ] Topic distribution visualization
- [ ] Topic evolution over time

### Future Features 💡

- [ ] Multi-game comparison dashboard
- [ ] Advanced filtering (date range, playtime brackets, user type)
- [ ] Export enhancements (Excel, PDF reports)
- [ ] Batch analysis automation (analyze multiple games in queue)
- [ ] Recommendation system based on review patterns
- [ ] API endpoint for programmatic access

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Steam API for review data
- NLTK, Jieba, scikit-learn for NLP capabilities
- WordCloud library for visualization
