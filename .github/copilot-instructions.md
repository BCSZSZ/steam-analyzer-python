# Copilot Instructions for steam-analyzer-python

## Project Overview

Python GUI application for fetching and analyzing Steam user reviews with advanced text analysis. Features N-gram frequency analysis, TF-IDF distinctive term extraction, and word cloud visualization with multi-language support (English/Chinese). Data flows: Steam API → raw JSON → analysis pipelines → CSV/JSON outputs + visualizations.

## Architecture & Data Flow

### Core Components

- **main.py**: Entry point, creates tabbed GUI with status queue. 5 tabs: Data Collection, Extreme Reviews, Text Insights, N-gram Analysis, TF-IDF Analysis.
- **backend.py**: Steam API fetching, checkpointing (every 50 pages), saves to `data/raw/`.
- **utils.py**: Game name caching (Steam Store API, cache-first pattern).

### Tabs (inherit from BaseTab)

- `data_collection_tab.py`: Fetch reviews, generate language reports
- `extreme_reviews_tab.py`: Display extreme playtime reviews with language filtering
- `text_insights_tab.py`: Dashboard with N-gram + TF-IDF quick views (frozen, kept as-is)
- `ngram_analysis_tab.py`: N-gram frequency analysis (bigrams/trigrams) with word clouds
- `tfidf_analysis_tab.py`: TF-IDF distinctive terms (positive vs negative) with dual word clouds

### Analyzers (inherit from BaseAnalyzer)

- `language_report.py`: CSV reports by language with sentiment stats
- `playtime_extremes.py`: Single-pass O(n) extreme finder with language grouping
- `text_processor.py`: Tokenization, stopwords, n-gram generation (English: NLTK, Chinese: Jieba)
- `ngram_analyzer.py`: Frequency extraction, repetitive filtering
- `tfidf_analyzer.py`: scikit-learn TF-IDF vectorization for sentiment comparison
- `wordcloud_generator.py`: Word cloud images with Chinese font detection

### Data Structure

- `data/raw/`: Raw JSON (`{appid}_{date}_{count}_reviews.json`)
- `data/processed/reports/`: CSV language reports
- `data/processed/insights/`: JSON analysis results (extreme, n-grams, TF-IDF)
- `data/cache/`: Checkpoints + app_details cache

## Developer Workflows

- **Setup**: Use a Python virtual environment. Install dependencies with `pip install -r requirements.txt`.
- **Run**: Start the GUI with `python main.py`.
- **Debug**: Backend logic can be tested by running functions in `backend.py` directly. For UI debugging, use the GUI and observe status messages.
- **Data Import/Export**: The GUI supports importing CSV reports and analyzing from existing JSON files.

## Key Conventions

- **Threading**: Daemon threads for long operations, `status_queue`/`frame.after()` for thread-safe UI updates
- **Language Support**: English (NLTK) and Chinese (Jieba) with language-specific tokenization/stopwords
- **File Naming**: `{appid}_{game_name}_{language}_{sentiment}_{type}_{date}` for traceability
- **Checkpointing**: Every 50 pages during fetch, stored in `data/cache/`
- **Plugin Architecture**: Tabs inherit from `BaseTab`, analyzers from `BaseAnalyzer`
- **Single-Pass Algorithms**: O(n) complexity where possible
- **N-gram Filtering**: Only bigrams/trigrams (unigrams excluded), repetitive patterns filtered
- **TF-IDF Vectorization**: Tokenized reviews space-separated before scikit-learn processing
- **Word Cloud Settings**:
  - `prefer_horizontal=1.0` (no vertical text)
  - `relative_scaling=0.3` (balanced sizes)
  - `min_font_size=12`, `max_font_size=80`
  - Chinese font auto-detection (Windows: SimHei/YaHei, macOS: PingFang, Linux: WQY)
- **Popup Windows**: Word clouds displayed in popups with save button + right-click support

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
2. Resume: Checkpoint in `data/cache/` allows continuing interrupted downloads

### Text Analysis

1. **N-gram Analysis**: Load JSON → Select language/sentiment/size → Set threshold → Analyze → Generate word cloud (popup with save button)
2. **TF-IDF Analysis**: Load JSON → Select language/n-gram range/top N → Analyze → Generate word clouds (2 popups: positive/negative)
3. **Text Insights**: Load JSON → Select language → Quick overview with navigation to detailed tabs
4. **Extreme Reviews**: Load JSON → View battles by language → Filter languages (default: English + Chinese)

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

## Next Phase: LDA Topic Modeling

Upcoming feature: Latent Dirichlet Allocation (LDA) for topic discovery in Steam reviews.

---

For questions or unclear conventions, review the code in the above files or ask for clarification.
