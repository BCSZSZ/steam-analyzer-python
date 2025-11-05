# Steam Review Analyzer

A comprehensive Python GUI application for fetching, analyzing, and visualizing Steam user reviews. Built with Tkinter and featuring a modular architecture for extensibility.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
  - [Data Collection Tab](#data-collection-tab)
  - [Extreme Reviews Tab](#extreme-reviews-tab)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Data Outputs](#data-outputs)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

Steam Review Analyzer is a powerful desktop application designed for game developers, researchers, and enthusiasts who want to analyze Steam user reviews at scale. The application fetches reviews directly from Steam's API, performs comprehensive sentiment and language analysis, and presents insights through an intuitive tabbed interface.

### Key Capabilities

- **Bulk Review Fetching**: Download thousands of reviews with automatic pagination and checkpoint support
- **Multi-Language Analysis**: Analyze reviews across 20+ languages with Chinese translations
- **Sentiment Categorization**: Automatic Steam review category assignment (Overwhelmingly Positive, Mixed, etc.)
- **Extreme Review Detection**: Find reviews with exceptional playtime values per language
- **Offline Analysis**: Re-analyze previously downloaded data without re-fetching
- **Resume Capability**: Resume interrupted downloads from checkpoints

---

## ✨ Features

### Current Features

#### 📊 Data Collection & Analysis

- Fetch reviews from any Steam game by App ID
- Choose between fetching all reviews or a specific count
- Automatic game name resolution via Steam Store API with local caching
- Generate comprehensive CSV reports grouped by language
- Save raw review data in JSON format for future analysis
- Resume interrupted downloads from automatic checkpoints (saved every 50 pages)

#### 🌍 Multi-Language Support

- Analysis across 20+ languages including English, Chinese (Simplified & Traditional), Japanese, Korean, Russian, and more
- Chinese translations for language names and review categories
- Per-language sentiment statistics and metrics

#### 📈 Advanced Analytics

- **Sentiment Analysis**: Positive/negative review counts and percentages
- **Steam Categories**: Automatic categorization (Overwhelmingly Positive, Very Positive, Mixed, etc.)
- **Playtime Metrics**: Average playtime at review time and total playtime (positive vs negative)
- **User Profiles**: Average games owned by reviewers
- **Extreme Reviews**: Identify reviews with longest playtime per language (2 battles: playtime@review and total playtime)

#### 🎨 User Interface

- Clean tabbed interface for different analysis types
- Sortable data tables with multi-column support
- Visual comparison cards for extreme reviews with winner highlighting
- Language filtering for focused analysis (default: English and Chinese)
- Real-time status updates during long operations

### 🔮 Upcoming Features

More analysis tabs and features are planned! The modular architecture makes it easy to add:

- **Sentiment Timeline Tab**: Track review sentiment changes over time
- **Word Cloud Tab**: Visualize common themes in positive/negative reviews
- **Comparison Tab**: Compare multiple games side-by-side
- **Export Options**: Additional export formats (Excel, PDF reports)
- **Advanced Filters**: Filter by review date, playtime range, etc.

_See [Roadmap](#roadmap) for detailed future plans._

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** (Python 3.10+ recommended)
- **pip** (Python package manager)
- **Git** (for cloning the repository)
- **Internet connection** (for fetching reviews from Steam)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/BCSZSZ/steam-analyzer-python.git
cd steam-analyzer-python
```

#### 2. Create a Virtual Environment

It's strongly recommended to use a virtual environment to isolate dependencies.

**On Windows:**

```bash
python -m venv venv
.\venv\Scripts\activate
```

**On macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

You'll see `(venv)` at the beginning of your terminal prompt when activated.

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**

- `requests` - For Steam API communication
- `customtkinter` - Modern UI components (optional, falls back to tkinter)

### Quick Start

#### Run the Application

```bash
python main.py
```

The application window will open with the Data Collection tab active.

#### First Analysis (Example)

1. **Enter a Steam App ID** (e.g., `1030300` for Baldur's Gate 3)
2. **Choose review count** (default: 2000 reviews, or check "Fetch all available reviews")
3. **Click "Fetch & Analyze"**
4. **Wait for completion** - Status updates will show progress
5. **View results** in the table and check the `data/` folder for outputs

---

## 📖 Usage Guide

### Data Collection Tab

The main tab for fetching and analyzing Steam reviews.

#### Fetching Reviews

1. **App ID Input**: Enter the Steam App ID (find it in the game's Steam URL)

   - Example: `https://store.steampowered.com/app/1030300/` → App ID is `1030300`

2. **Review Count Options**:

   - **Specific Count**: Enter number (e.g., 2000) - will fetch ~20 pages
   - **Fetch All**: Check box to download all available reviews (can take hours for popular games)

3. **Controls**:
   - **Fetch & Analyze**: Start download and generate report
   - **Analyze from JSON**: Re-analyze previously downloaded data
   - **Import Report (CSV)**: View previously generated CSV reports
   - **Cancel**: Stop ongoing download (progress saved as checkpoint)

#### Resume Capability

If a download is interrupted, the app automatically saves a checkpoint every 50 pages. Next time you fetch the same game, you'll be asked if you want to resume from where you left off.

#### Understanding the Report

The generated table shows:

- **Language**: ISO language code (english, schinese, japanese, etc.)
- **Total Reviews**: Number of reviews in that language
- **Positive Rate**: Percentage of positive (thumbs up) reviews
- **Category**: Steam's review category (Overwhelmingly Positive, Mixed, etc.)
- **Playtime Metrics**: Average hours played by positive vs negative reviewers
- **Games Owned**: Average Steam library size of reviewers

### Extreme Reviews Tab

Visualizes reviews with exceptional playtime values.

#### Loading Data

1. **Load Raw JSON**: Analyze a previously downloaded JSON file from `data/raw/`
2. **Load Saved Results**: Open pre-analyzed results from `data/processed/insights/`

#### Language Filtering

By default, shows **English and Chinese** reviews. To view other languages:

1. Edit the **Languages** field (comma-separated)
   - Example: `english,japanese,korean`
   - Example: `german,french,spanish`
2. Click **Apply Filter**

#### Understanding the Battles

For each language, two battles are shown:

**⚔️ Battle 1: Longest Playtime @ Review**

- Shows the review that was written after the most hours played
- Compares positive vs negative review
- Winner highlighted in yellow

**⚔️ Battle 2: Longest Total Playtime**

- Shows the review from the user with the most total hours (current)
- Compares positive vs negative review
- Winner highlighted in yellow

Each card displays:

- Playtime at review time (hours when review was written)
- Total playtime (current total hours)
- Games owned by reviewer
- Full review text (scrollable)
- Review metadata (date, helpful votes, funny votes)

---

## 📁 Project Structure

```
steam-analyzer-python/
├── main.py                      # Application entry point and main window
├── backend.py                   # Steam API communication and data fetching
├── utils.py                     # Game name caching and Steam Store API
├── requirements.txt             # Python dependencies
├── analyzers/                   # Analysis modules (plugin architecture)
│   ├── __init__.py
│   ├── base_analyzer.py         # Abstract base class for analyzers
│   ├── language_report.py       # CSV report generation by language
│   └── playtime_extremes.py     # Extreme playtime review finder
├── tabs/                        # UI tab modules (plugin architecture)
│   ├── __init__.py
│   ├── base_tab.py              # Abstract base class for tabs
│   ├── data_collection_tab.py   # Main fetch and analyze interface
│   └── extreme_reviews_tab.py   # Extreme reviews visualization
├── data/                        # Data storage (created automatically)
│   ├── raw/                     # Raw review JSON files
│   ├── processed/
│   │   ├── reports/             # CSV analysis reports
│   │   └── insights/            # JSON analysis results
│   └── cache/                   # Checkpoints and game name cache
│       └── app_details/         # Steam Store API response cache
└── docs/                        # Documentation
    ├── METADATA_ANALYSIS.md     # Steam review field documentation
    └── APPID_TYPE_AUDIT.md      # AppID type handling audit
```

### Adding New Features

The architecture is designed for easy extension:

**To add a new analyzer:**

1. Create a class inheriting from `BaseAnalyzer` in `analyzers/`
2. Implement `analyze(json_data)` method
3. Return results and save to `data/processed/`

**To add a new tab:**

1. Create a class inheriting from `BaseTab` in `tabs/`
2. Implement `get_tab_title()` and `create_ui()` methods
3. Import and instantiate in `main.py`

---

## 🏗️ Architecture

### Core Components

- **Modular Tab System**: Each tab is a self-contained module inheriting from `BaseTab`
- **Plugin-Based Analyzers**: Analyzers inherit from `BaseAnalyzer` for consistent interface
- **Cache-First Design**: Game names cached locally to minimize API calls
- **Single-Pass Algorithms**: O(n) complexity for efficient large dataset processing
- **Thread-Safe Operations**: Background workers with queue-based UI updates

### Data Flow

```
User Input → Backend.fetch_reviews() → Save JSON → Analyzer.analyze() → Save CSV/JSON → Display in UI
                     ↓                                                        ↓
              Checkpoint System                                        Cache System
```

### Key Patterns

- **Checkpointing**: Every 50 pages during fetch for resume capability
- **Event Propagation**: `"break"` return to prevent nested scroll conflicts
- **Type Safety**: Explicit int() conversion for App IDs from filename parsing
- **Status Queue**: Non-blocking UI updates from background threads

---

## 💾 Data Outputs

### File Naming Conventions

**Raw Review Data:**

```
{appid}_{date}_{count}_reviews.json
Example: 1030300_2025-11-05_2000max_reviews.json
```

**CSV Reports:**

```
{appid}_{game_title}_{date}_{count}_report.csv
Example: 1030300_Baldur_s_Gate_3_2025-11-05_2000max_report.csv
```

**Extreme Reviews:**

```
{appid}_extreme_reviews_by_language_{date}.json
Example: 1030300_extreme_reviews_by_language_2025-11-05.json
```

**Checkpoints:**

```
{appid}_checkpoint.json
Example: 1030300_checkpoint.json
```

### Storage Locations

- `data/raw/` - Raw review JSON files (for re-analysis)
- `data/processed/reports/` - CSV reports (for import/sharing)
- `data/processed/insights/` - JSON analysis results (for extreme reviews)
- `data/cache/` - Checkpoints (temporary, can be deleted)
- `data/cache/app_details/` - Game name cache (permanent, speeds up app)

---

## 🗺️ Roadmap

### Phase 1: Core Features ✅

- [x] Basic review fetching
- [x] Language-based CSV reports
- [x] Extreme playtime analysis
- [x] Multi-language support
- [x] Checkpoint system
- [x] Game name auto-fetch with caching

### Phase 2: Enhanced Analytics (In Progress)

- [x] Per-language filtering in extreme reviews
- [x] Visual comparison cards with winner highlighting
- [ ] Sentiment timeline analysis
- [ ] Date range filtering
- [ ] Weighted scoring system

### Phase 3: Advanced Features (Planned)

- [ ] Word cloud generation from review text
- [ ] Topic modeling and theme extraction
- [ ] Multi-game comparison view
- [ ] Review text search functionality
- [ ] Export to Excel with charts
- [ ] Automated report scheduling

### Phase 4: Community Features (Future)

- [ ] Share analysis configurations
- [ ] Custom analyzer plugins
- [ ] REST API for programmatic access
- [ ] Web dashboard for remote viewing

---

## 🤝 Contributing

Contributions are welcome! The modular architecture makes it easy to add new features.

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Make your changes** (follow existing code style and patterns)
4. **Add tests** if applicable
5. **Update documentation** in README.md and docstrings
6. **Commit changes** (`git commit -m 'Add some AmazingFeature'`)
7. **Push to branch** (`git push origin feature/AmazingFeature`)
8. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guidelines
- Add comprehensive docstrings (Google style)
- Use type hints where applicable
- Keep modules focused and single-purpose
- Update README.md for new features

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Steam API for providing review data
- Python community for excellent libraries
- CustomTkinter for modern UI components

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/BCSZSZ/steam-analyzer-python/issues)
- **Discussions**: [GitHub Discussions](https://github.com/BCSZSZ/steam-analyzer-python/discussions)

---

**Made with ❤️ for the Steam community**
