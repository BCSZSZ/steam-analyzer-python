# Copilot Instructions for steam-analyzer-python

## Project Overview

This project is a Python GUI application for fetching and analyzing Steam user reviews by language and sentiment. It consists of a Tkinter-based frontend (`main.py`) and a backend for data fetching and analysis (`backend.py`, `review_analyzer.py`). Data is stored in `json/` and reports in `reports/`.

## Architecture & Data Flow

- **main.py**: Entry point that creates the tabbed GUI using CustomTkinter. Manages status queue and initializes tabs.
- **tabs/**: Modular tab implementations
  - `base_tab.py`: Abstract base class for all tabs
  - `data_collection_tab.py`: Fetch and analyze functionality
  - `extreme_reviews_tab.py`: Extreme playtime review battles with per-language filtering
- **analyzers/**: Plugin-based analysis modules
  - `base_analyzer.py`: Abstract base class for analyzers
  - `language_report.py`: CSV report generation with language/category mapping
  - `playtime_extremes.py`: Finds extreme playtime reviews with O(n) single-pass language grouping
- **backend.py**: Fetches reviews from the Steam API, manages checkpoints, saves raw data to `data/raw/`, and generates reports.
- **Data directories**:
  - `data/raw/`: Stores raw review data as JSON files
  - `data/processed/reports/`: CSV analysis reports
  - `data/processed/insights/`: JSON analysis results (extreme reviews)
  - `data/cache/`: Checkpointing for resume functionality

## Developer Workflows

- **Setup**: Use a Python virtual environment. Install dependencies with `pip install -r requirements.txt`.
- **Run**: Start the GUI with `python main.py`.
- **Debug**: Backend logic can be tested by running functions in `backend.py` directly. For UI debugging, use the GUI and observe status messages.
- **Data Import/Export**: The GUI supports importing CSV reports and analyzing from existing JSON files.

## Conventions & Patterns

- **Threading**: Long-running fetches use threads and a `cancel_event` for safe cancellation.
- **Status Updates**: UI updates are communicated via a `status_queue`.
- **Language & Category Mapping**: All language and review category codes are mapped to Chinese for output consistency.
- **File Naming**: JSON and CSV files are named with the appid, date, and review count for traceability.
- **Checkpointing**: Large fetches save progress in `data/cache/` every 50 pages to allow resuming.
- **Plugin Architecture**: Analyzers inherit from `BaseAnalyzer`, tabs inherit from `BaseTab` for extensibility.
- **Single-Pass Algorithms**: Use O(n) complexity for data processing (e.g., per-language grouping in extreme reviews).
- **Separation of Concerns**: Analyzers process all data and save to JSON, UI filters only display layer.

## Integration Points

- **Steam API**: All review data is fetched via `https://store.steampowered.com/appreviews/`.
- **External Libraries**: Requires `requests`, `CustomTkinter`, and standard Python libraries.

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
- To add a new analyzer:
  1. Create class inheriting from `BaseAnalyzer` in `analyzers/`.
  2. Implement `analyze()` method returning dict with results.
  3. Use `save_results()` helper to save to `data/processed/insights/`.
- To add a new tab:
  1. Create class inheriting from `BaseTab` in `tabs/`.
  2. Implement `get_tab_title()` and `create_ui()` methods.
  3. Import and instantiate in `main.py`.

## Key Files

- `main.py`: GUI initialization and tab management (67 lines).
- `backend.py`: Data fetching, checkpointing, and report generation.
- `review_analyzer.py`: Sentiment and language/category mapping (legacy, used by language_report).
- `tabs/base_tab.py`: Abstract base class for tab modules.
- `tabs/data_collection_tab.py`: Original fetch & analyze functionality.
- `tabs/extreme_reviews_tab.py`: Per-language playtime battle display with filtering.
- `analyzers/base_analyzer.py`: Abstract base class for analysis plugins.
- `analyzers/language_report.py`: CSV report generation (refactored from backend).
- `analyzers/playtime_extremes.py`: Single-pass O(n) extreme review finder with language grouping.
- `requirements.txt`: Dependency list.
- `README.md`: Setup and usage instructions.
- `docs/LANGUAGE_FILTER_FEATURE.md`: Documentation for per-language filtering feature.

---

For questions or unclear conventions, review the code in the above files or ask for clarification.
