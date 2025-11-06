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

- **Data Collection**: Fetch reviews from Steam API with checkpointing and resume capability
- **Language Reports**: CSV reports with sentiment analysis grouped by language (20+ languages)
- **Extreme Reviews**: Find reviews with longest playtime per language
- **Text Insights Dashboard**: Quick overview of N-gram and TF-IDF analysis results
- **N-gram Analysis**: Extract common phrases (bigrams/trigrams) with frequency filtering
- **TF-IDF Analysis**: Identify distinctive terms for positive vs negative reviews
- **Word Cloud Visualization**: Generate visual word clouds with Chinese font support
- **Multi-language Support**: English and Chinese (Simplified) with language-specific tokenization

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

## 🎯 Usage

### 1. Data Collection Tab
- Enter Steam App ID (e.g., `1030300` for Baldur's Gate 3)
- Choose review count or fetch all
- Click "Fetch & Analyze" to download and generate language report
- Resume interrupted downloads from checkpoints

### 2. Extreme Reviews Tab
- Load raw JSON or saved results
- View reviews with longest playtime per language
- Filter by language (default: English and Chinese)

### 3. Text Insights Dashboard
- Load raw JSON file
- Select language (English/Chinese)
- View quick overview of top N-grams and distinctive terms
- Navigate to detailed analysis tabs

### 4. N-gram Analysis Tab
- Load raw JSON file
- Select language, sentiment, N-gram size (bigrams/trigrams)
- Set minimum frequency threshold
- Generate word cloud visualization (horizontal words, balanced sizes)

### 5. TF-IDF Analysis Tab
- Load raw JSON file
- Select language, N-gram range, top N terms
- View distinctive terms for positive vs negative reviews
- Generate dual word clouds with Chinese font support

---

## 🔍 Analysis Features

### Language Report (CSV)
- Reviews grouped by language with sentiment statistics
- Steam category assignment (Overwhelmingly Positive, Mixed, etc.)
- Playtime metrics and user profiles

### N-gram Analysis
- Extract common phrases (bigrams/trigrams only, unigrams excluded)
- Language-specific tokenization (NLTK for English, Jieba for Chinese)
- Repetitive N-gram filtering
- Frequency-based word clouds

### TF-IDF Analysis
- Identify distinctive terms using scikit-learn TF-IDF vectorization
- Compare positive vs negative sentiment vocabulary
- Distinctiveness scoring for term importance
- Dual word clouds (green for positive, red for negative)

### Word Cloud Generation
- Horizontal text only (no vertical words)
- Balanced font sizes (reduced variance between largest/smallest)
- Automatic Chinese font detection (Windows/macOS/Linux)
- Popup windows with save button and right-click support
- High resolution (1200x600 for N-gram, 600x600 per TF-IDF)

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
│   ├── text_processor.py        # NLP utilities (tokenization, n-grams)
│   └── wordcloud_generator.py   # Word cloud image generation
├── tabs/                        # UI tab modules (plugin-based)
│   ├── base_tab.py              # Abstract base class
│   ├── data_collection_tab.py   # Fetch & analyze interface
│   ├── extreme_reviews_tab.py   # Extreme reviews visualization
│   ├── text_insights_tab.py     # Quick analysis dashboard
│   ├── ngram_analysis_tab.py    # N-gram frequency analysis
│   └── tfidf_analysis_tab.py    # TF-IDF distinctive terms
└── data/                        # Data storage (auto-created)
    ├── raw/                     # Raw review JSON files
    ├── processed/
    │   ├── reports/             # CSV reports
    │   └── insights/            # JSON analysis results
    └── cache/                   # Checkpoints & game name cache
```

### Architecture Highlights

- **Plugin Architecture**: Tabs and analyzers inherit from base classes for extensibility
- **Single-Pass Algorithms**: O(n) complexity for efficient processing
- **Checkpointing**: Resume capability for large downloads
- **Language-Specific NLP**: NLTK (English) and Jieba (Chinese) tokenization
- **Thread-Safe UI**: Background workers with queue-based updates

## 💾 Data Outputs

### File Naming
- Raw JSON: `{appid}_{date}_{count}_reviews.json`
- CSV Report: `{appid}_{game_name}_{date}_{count}_report.csv`
- N-gram Analysis: `{appid}_{game_name}_{language}_{sentiment}_ngrams_{date}.json`
- TF-IDF Analysis: `{appid}_{game_name}_{language}_tfidf_{date}.json`
- Extreme Reviews: `{appid}_extreme_reviews_by_language_{date}.json`

### Storage
- `data/raw/` - Raw review JSON files
- `data/processed/reports/` - CSV language reports
- `data/processed/insights/` - JSON analysis results
- `data/cache/` - Checkpoints and game name cache

---

## 🗺️ Roadmap

### Completed ✅
- [x] Steam API fetching with checkpointing
- [x] Multi-language CSV reports
- [x] Extreme playtime analysis with language filtering
- [x] Text Insights Dashboard
- [x] N-gram frequency analysis (bigrams/trigrams)
- [x] TF-IDF distinctive term extraction
- [x] Word cloud visualization with Chinese font support

### Next: Phase 4 - Topic Modeling 🚧
- [ ] LDA (Latent Dirichlet Allocation) topic modeling
- [ ] Topic distribution visualization
- [ ] Topic-based review clustering
- [ ] Topic evolution over time

### Future Features 💡
- [ ] Sentiment timeline analysis
- [ ] Multi-game comparison
- [ ] Advanced filtering (date range, playtime)
- [ ] Export to Excel/PDF
- [ ] Batch analysis automation

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Steam API for review data
- NLTK, Jieba, scikit-learn for NLP capabilities
- WordCloud library for visualization
