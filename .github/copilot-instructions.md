# Copilot Instructions for steam-analyzer-python

## Project Overview

This project is a Python GUI application for fetching and analyzing Steam user reviews by language and sentiment. It features a Tkinter-based tabbed interface with advanced text analysis capabilities including N-gram frequency analysis and TF-IDF term importance comparison. Data flows from Steam API → raw JSON storage → multiple analysis pipelines → CSV/JSON outputs.

## Architecture & Data Flow

- **main.py**: Entry point that creates the tabbed GUI. Manages status queue and initializes 5 tabs (Data Collection, Extreme Reviews, Text Insights, N-gram Analysis, TF-IDF Analysis).
- **tabs/**: Modular tab implementations (all inherit from `BaseTab`)
  - `base_tab.py`: Abstract base class defining tab interface
  - `data_collection_tab.py`: Fetch reviews from Steam API with checkpointing
  - `extreme_reviews_tab.py`: Display extreme playtime reviews with per-language filtering
  - `text_insights_tab.py`: Dashboard combining N-gram and TF-IDF quick views (UI ready, backend TODO)
  - `ngram_analysis_tab.py`: N-gram frequency analysis with language/sentiment filtering
  - `tfidf_analysis_tab.py`: TF-IDF distinctive term comparison (positive vs negative)
- **analyzers/**: Plugin-based analysis modules (all inherit from `BaseAnalyzer`)
  - `base_analyzer.py`: Abstract base class with common save/load functionality
  - `text_processor.py`: Shared NLP utilities (tokenization, stopwords, n-gram generation)
  - `language_report.py`: CSV report generation with language/category mapping
  - `playtime_extremes.py`: Single-pass O(n) extreme playtime finder with language grouping
  - `ngram_analyzer.py`: N-gram frequency extraction with repetitive filtering
  - `tfidf_analyzer.py`: TF-IDF vectorization using scikit-learn for sentiment comparison
- **backend.py**: Fetches reviews from Steam API, manages checkpoints, saves raw data to `data/raw/`.
- **utils.py**: Game name caching with Steam Store API (cache-first pattern).
- **Data directories**:
  - `data/raw/`: Raw review JSON files (named: `{appid}_{date}_{count}_reviews.json`)
  - `data/processed/reports/`: CSV analysis reports from language_report analyzer
  - `data/processed/insights/`: JSON analysis results (extreme reviews, n-grams, TF-IDF)
  - `data/cache/`: Checkpointing for resume functionality + app_details cache

## Developer Workflows

- **Setup**: Use a Python virtual environment. Install dependencies with `pip install -r requirements.txt`.
- **Run**: Start the GUI with `python main.py`.
- **Debug**: Backend logic can be tested by running functions in `backend.py` directly. For UI debugging, use the GUI and observe status messages.
- **Data Import/Export**: The GUI supports importing CSV reports and analyzing from existing JSON files.

## Conventions & Patterns

- **Threading**: Long-running operations use threads with `daemon=True` to keep UI responsive. Analysis tabs use background threads.
- **Status Updates**: UI updates are communicated via `status_queue` or `frame.after()` for thread-safe GUI updates.
- **Language Support**: Full English/Chinese (schinese) support with language-specific tokenization:
  - English: NLTK-style tokenization with common stopwords
  - Chinese: Jieba segmentation with Chinese stopwords
- **File Naming**: JSON and CSV files include `{appid}_{game_name}_{language}_{sentiment}_{type}_{date}` for traceability.
- **Checkpointing**: Large fetches save progress in `data/cache/` every 50 pages to allow resuming.
- **Plugin Architecture**: Analyzers inherit from `BaseAnalyzer`, tabs inherit from `BaseTab` for extensibility.
- **Single-Pass Algorithms**: Use O(n) complexity for data processing where possible.
- **Separation of Concerns**: Analyzers process all data and save to JSON, UI loads and displays results.
- **N-gram Filtering**: Repetitive n-grams (e.g., ('难评', '难评')) are filtered out during generation.
- **TF-IDF Corpus Building**: Reviews are tokenized and space-separated before TF-IDF vectorization.
- **Game Name Caching**: `utils.get_game_name(appid)` uses cache-first pattern to minimize API calls.

## Integration Points

- **Steam API**:
  - Review data: `https://store.steampowered.com/appreviews/{appid}`
  - Game details: `http://store.steampowered.com/api/appdetails/?appids={appid}`
- **External Libraries**:
  - Core: `requests`, `customtkinter`, `tkinter`
  - NLP: `jieba` (Chinese), `nltk` (English), `scikit-learn` (TF-IDF)

## Example Patterns

- To fetch and analyze reviews for a Steam app:
  1. Enter App ID and game title in the Data Collection tab.
  2. Choose review count or "Fetch all".
  3. Click "Fetch & Analyze".
  4. Results are saved in `data/raw/` and `data/processed/reports/`.
- To resume a large fetch, use the checkpoint file in `data/cache/`.
- To view extreme playtime reviews:
  1. Go to Extreme Reviews tab.
  2. Load raw JSON or saved results.
  3. Default filter shows English and Chinese.
  4. Edit "Languages" field and click "Apply Filter" to show other languages.
- To perform N-gram analysis:
  1. Go to N-gram Analysis tab.
  2. Load raw JSON file.
  3. Select language (English/Chinese), sentiment (Positive/Negative/Both), n-gram size (2/3).
  4. Set minimum frequency threshold.
  5. Click "Analyze" to extract common phrases (bigrams/trigrams only).
- To perform TF-IDF analysis:
  1. Go to TF-IDF Analysis tab.
  2. Load raw JSON file.
  3. Select language, n-gram range (bigrams/trigrams), and top N terms.
  4. Click "Analyze" to identify distinctive terms for positive vs negative reviews.
- To use Text Insights Dashboard:
  1. Go to Text Insights tab.
  2. Load raw JSON file.
  3. Select language (English/Chinese).
  4. Click "Refresh Analysis" to see quick overview.
  5. View top 10 bigrams and top 5 distinctive terms per sentiment.
  6. Click "Deep Dive →" buttons to navigate to detailed analysis tabs.
- To add a new analyzer:
  1. Create class inheriting from `BaseAnalyzer` in `analyzers/`.
  2. Implement `analyze()` method returning dict with results.
  3. Use `save_output()` helper to save to `data/processed/insights/`.
- To add a new tab:
  1. Create class inheriting from `BaseTab` in `tabs/`.
  2. Implement `get_tab_title()` and `create_ui()` methods.
  3. Import and instantiate in `main.py`.

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
- `requirements.txt`: Dependency list (includes jieba, nltk, scikit-learn).
- `README.md`: Setup and usage instructions with roadmap.
- `docs/LANGUAGE_FILTER_FEATURE.md`: Documentation for per-language filtering feature.

---

For questions or unclear conventions, review the code in the above files or ask for clarification.
