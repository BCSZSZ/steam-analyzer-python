# Copilot Instructions for steam-analyzer-python

## Project Overview

Python GUI application for fetching and analyzing Steam user reviews with comprehensive text analysis and visualization. Features include:
- **Data Collection**: Steam API fetching with checkpoint/resume capability
- **Text Analysis**: N-gram frequency, TF-IDF distinctive terms, timeline sentiment tracking
- **Visualization**: Word clouds, interactive Plotly timeline charts with dual y-axes
- **Language Support**: English/Chinese with customizable stopwords manager
- **Data Flow**: Steam API → checkpointed raw JSON → analysis pipelines → CSV/JSON outputs + HTML visualizations

## Architecture & Data Flow

### Core Components

- **main.py**: Entry point, creates tabbed GUI with status queue. 5 tabs: Data Collection, Extreme Reviews, Text Insights, N-gram Analysis, TF-IDF Analysis.
- **backend.py**: Steam API fetching, checkpointing (every 50 pages), saves to `data/raw/`.
- **utils.py**: Game name caching (Steam Store API, cache-first pattern).

### Tabs (inherit from BaseTab)

- `data_collection_tab.py`: Fetch reviews with resume from checkpoint, generate language reports
- `extreme_reviews_tab.py`: Display extreme playtime reviews with language filtering
- `text_insights_tab.py`: Dashboard with N-gram + TF-IDF quick views (frozen, kept as-is)
- `ngram_analysis_tab.py`: N-gram frequency analysis (bigrams/trigrams) with word clouds
- `tfidf_analysis_tab.py`: TF-IDF distinctive terms (positive vs negative) with dual word clouds
- `timeline_analysis_tab.py`: Interactive timeline with auto-determined rolling window, cumulative counts
- `bertopic_stopwords_tab.py`: Universal stopwords manager with table view, dual-key system

### Analyzers (inherit from BaseAnalyzer)

- `language_report.py`: CSV reports by language with sentiment stats
- `playtime_extremes.py`: Single-pass O(n) extreme finder with language grouping
- `text_processor.py`: Tokenization, custom stopwords (universal + game-specific), n-gram generation
- `ngram_analyzer.py`: Frequency extraction, repetitive filtering
- `tfidf_analyzer.py`: scikit-learn TF-IDF vectorization for sentiment comparison
- `timeline_analyzer.py`: Time-series analysis with auto-determined rolling window, divide-by-zero failover
- `wordcloud_generator.py`: Word cloud images with Chinese font detection

### Data Structure

- `data/raw/`: Raw JSON (`{appid}_{YYYY-MM-DD}_{HH-MM-SS}_{target}_{current}_reviews.json`)
- `data/processed/reports/`: CSV language reports
- `data/processed/insights/`: JSON analysis results (extreme, n-grams, TF-IDF, timeline)
- `data/cache/`: Separate checkpoint files + app_details cache
- `data/stopwords.json`: Universal + game-specific custom stopwords (dual-key system)

## Developer Workflows

- **Setup**: Use a Python virtual environment. Install dependencies with `pip install -r requirements.txt`.
- **Run**: Start the GUI with `python main.py`.
- **Debug**: Backend logic can be tested by running functions in `backend.py` directly. For UI debugging, use the GUI and observe status messages.
- **Data Import/Export**: The GUI supports importing CSV reports and analyzing from existing JSON files.

## Key Conventions

- **Threading**: Daemon threads for long operations, `status_queue`/`frame.after()` for thread-safe UI updates
- **Language Support**: English (NLTK) and Chinese (Jieba) with customizable stopwords (universal + game-specific)
- **File Naming**: 
  - Raw data: `{appid}_{YYYY-MM-DD}_{HH-MM-SS}_{target}_{current}_reviews.json`
  - Checkpoint: `{appid}_{YYYY-MM-DD}_{HH-MM-SS}_{target}_{current}_checkpoint.json`
  - Analysis: `{appid}_{game_name}_{language}_{sentiment}_{type}_{date}`
- **Checkpointing**: Every 50 pages, on empty page, cancel, or exception → separate JSON files, deleted on completion
- **Resume Workflow**: File picker to select checkpoint, extracts metadata, continues from cursor
- **Logging**: Consolidated `[FETCH]` logs per page with progress %, time, status, full cursor
- **Plugin Architecture**: Tabs inherit from `BaseTab`, analyzers from `BaseAnalyzer`
- **Single-Pass Algorithms**: O(n) complexity where possible
- **N-gram Filtering**: Only bigrams/trigrams (unigrams excluded), repetitive patterns filtered
- **TF-IDF Vectorization**: Tokenized reviews space-separated before scikit-learn processing
- **Timeline Analysis**: Auto-determined rolling window (3-60 days based on date range), divide-by-zero failover
- **Word Cloud Settings**:
  - `prefer_horizontal=1.0` (no vertical text)
  - `relative_scaling=0.3` (balanced sizes)
  - `min_font_size=12`, `max_font_size=80`
  - Chinese font auto-detection (Windows: SimHei/YaHei, macOS: PingFang, Linux: WQY)
- **Visualization Windows**: Word clouds in popups, timeline charts in browser (1800x900 Plotly HTML)
- **Stopwords Manager**: Table view with dual keys (English + CN per game), auto-load on startup

## Integration Points

- **Steam API**:
  - Review data: `https://store.steampowered.com/appreviews/{appid}`
  - Game details: `http://store.steampowered.com/api/appdetails/?appids={appid}`
- **External Libraries**:
  - Core: `requests`, `customtkinter`, `tkinter`
  - NLP: `jieba` (Chinese), `nltk` (English), `scikit-learn` (TF-IDF)

## Usage Workflows

### Data Collection

1. Enter App ID → Choose count → "Fetch & Analyze" → Results in `data/raw/` and `data/processed/reports/`
2. Resume: "Resume from Checkpoint" button → File picker → Select checkpoint JSON → Continue from saved cursor
3. Console logs: `[FETCH] Page N | Reviews: +X (Total: Y/Z = %) | Time: Xs | Status: OK | Cursor: full_cursor`

### Text Analysis

1. **N-gram Analysis**: Load JSON → Select language/sentiment/size → Set threshold → Analyze → Generate word cloud (popup with save button)
2. **TF-IDF Analysis**: Load JSON → Select language/n-gram range/top N → Analyze → Generate word clouds (2 popups: positive/negative)
3. **Timeline Analysis**: Load JSON → Select language → Set rolling window (0=auto) → Generate chart → Opens in browser (4 lines: 2 dotted rates + 2 solid counts)
4. **Text Insights**: Load JSON → Select language → Quick overview with navigation to detailed tabs
5. **Extreme Reviews**: Load JSON → View battles by language → Filter languages (default: English + Chinese)
6. **Stopwords Manager**: Edit universal/game-specific stopwords → Table view with dual keys → Auto-loads on app start

### Extending

- **New Analyzer**: Inherit from `BaseAnalyzer` → Implement `analyze()` → Use `save_output()` helper
- **New Tab**: Inherit from `BaseTab` → Implement `get_tab_title()` and `create_ui()` → Import in `main.py`

## Key Files

- `main.py`: GUI initialization and tab management (67 lines).
- `backend.py`: Data fetching, checkpointing, and report generation.
- `utils.py`: Game name caching with Steam Store API.
- `review_analyzer.py`: Sentiment and language/category mapping (legacy, used by language_report).
- `tabs/base_tab.py`: Abstract base class for tab modules.
- `tabs/data_collection_tab.py`: Original fetch & analyze functionality.
- `tabs/extreme_reviews_tab.py`: Per-language playtime battle display with filtering.
- `tabs/text_insights_tab.py`: Dashboard combining N-gram and TF-IDF quick views (✅ COMPLETE).
- `tabs/ngram_analysis_tab.py`: N-gram frequency analysis (bigrams/trigrams only).
- `tabs/tfidf_analysis_tab.py`: TF-IDF distinctive terms analysis (bigrams/trigrams only).
- `analyzers/base_analyzer.py`: Abstract base class for analysis plugins.
- `analyzers/text_processor.py`: Text cleaning, tokenization, n-gram generation for English/Chinese.
- `analyzers/language_report.py`: CSV report generation (refactored from backend).
- `analyzers/playtime_extremes.py`: Single-pass O(n) extreme review finder with language grouping.
- `analyzers/ngram_analyzer.py`: N-gram frequency extraction with repetitive filtering.
- `analyzers/tfidf_analyzer.py`: TF-IDF vectorization for sentiment-distinctive term identification.
- `analyzers/wordcloud_generator.py`: Word cloud image generation with Chinese font support.
- `requirements.txt`: Dependency list (includes jieba, nltk, scikit-learn, wordcloud, pillow).
- `README.md`: Setup and usage instructions with roadmap.
- `docs/LANGUAGE_FILTER_FEATURE.md`: Documentation for per-language filtering feature.

---

## Current State (November 2025)

✅ **Completed Features**:
- Steam API fetching with checkpoint/resume system
- Language reports (CSV) with sentiment analysis
- Extreme playtime reviews with language filtering
- N-gram frequency analysis (bigrams/trigrams) with word clouds
- TF-IDF distinctive terms (positive vs negative) with dual word clouds
- Timeline analysis with auto-determined rolling window and cumulative counts
- Universal stopwords manager with table view and dual-key system
- Consolidated fetch logging with progress tracking

🚧 **Next Phase**: BERTopic integration for advanced topic modeling

---

For questions or unclear conventions, review the code in the above files or ask for clarification.
