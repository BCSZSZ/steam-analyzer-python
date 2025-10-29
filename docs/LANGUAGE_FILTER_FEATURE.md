# Per-Language Battle Analysis Feature

## Overview

Added language-specific extreme review analysis with filtering capability to the Steam Review Analyzer. Users can now see playtime battles for each language separately, with English and Chinese displayed by default.

## Implementation Details

### 1. Backend Changes (`analyzers/playtime_extremes.py`)

#### Algorithm Optimization

- **Single-Pass O(n) Grouping**: Changed from processing all reviews twice (positive/negative) to grouping by language in one pass
- **Performance**: Efficiently handles large datasets (280k+ reviews) without performance degradation

#### Data Structure

```python
results = {
    'metadata': {...},
    'total_reviews_analyzed': int,
    'languages_analyzed': ['english', 'schinese', ...],  # All languages found
    'extremes_by_language': {
        'english': {
            'longest_playtime_at_review_positive': {...},
            'longest_playtime_at_review_negative': {...},
            'longest_total_playtime_positive': {...},
            'longest_total_playtime_negative': {...},
            'positive_count': int,
            'negative_count': int,
            'total_count': int
        },
        'schinese': {...},
        # ... other languages
    }
}
```

#### File Naming

- Old: `{appid}_extreme_reviews_{date}.json`
- New: `{appid}_extreme_reviews_by_language_{date}.json`

### 2. Frontend Changes (`tabs/extreme_reviews_tab.py`)

#### UI Controls

Added to control panel:

- **Language Filter Entry**: Text input with default value `"english,schinese"`
- **Apply Filter Button**: Triggers filtering and redisplay
- **Language Info Label**: Shows selected vs available languages (e.g., "Showing 2 of 15 languages: english, schinese")

#### Methods Added

1. **`apply_language_filter()`**

   - Parses comma-separated language list from entry box
   - Validates against available languages in `extremes_by_language`
   - Calls filtered display method
   - Shows warnings for invalid input or old file format

2. **`display_extreme_reviews_filtered(filtered_languages, extremes_by_language)`**
   - Iterates through selected languages
   - Displays language header with review counts
   - Shows 2 battles per language (Playtime @ Review, Total Playtime)
   - Separators between languages for clarity

#### User Workflow

1. Load raw JSON file or saved results
2. Default filter applies automatically (English + Chinese)
3. User can edit language filter (comma-separated list)
4. Click "Apply Filter" to update display

### 3. Backward Compatibility

#### Old File Format Detection

- Files without `extremes_by_language` structure show warning
- User prompted to re-analyze from raw JSON
- Old files still loadable but filtering unavailable

## Usage Example

### Analyzing New Data

1. Click "Load Raw JSON" in Extreme Reviews tab
2. Select a file from `data/raw/`
3. Analyzer processes all languages and saves to `data/processed/insights/`
4. Default display shows English and Chinese battles

### Filtering Languages

1. Edit "Languages:" field (e.g., `english,schinese,japanese,korean`)
2. Click "Apply Filter"
3. Display updates to show selected languages

### Loading Saved Results

1. Click "Load Saved Results"
2. Select from `data/processed/insights/`
3. Filter applies automatically with default languages

## Performance Characteristics

### Time Complexity

- **Language Grouping**: O(n) - single pass through all reviews
- **Finding Extremes**: O(n) - single pass per language to find 4 extremes
- **UI Filtering**: O(1) - direct dict lookup, no data reprocessing

### Space Complexity

- Stores 4 reviews × number of languages in memory
- Minimal overhead (< 1MB for typical datasets)

### Tested Scenarios

- ✅ Small dataset (200 reviews)
- ✅ Medium dataset (2,000 reviews)
- ✅ Large dataset (280,000+ reviews)
- ✅ Multiple languages (15+ languages)
- ✅ Single language datasets

## Future Enhancements

### Potential Features

1. **Language Dropdown**: Replace text entry with multi-select dropdown
2. **Save Filter Preferences**: Remember user's language selection
3. **Translation Integration**: Show language names in native script
4. **Comparison View**: Side-by-side language comparison
5. **Export Filtered Results**: Save filtered battles to separate file

### Extensibility

- Architecture supports adding language-specific metrics
- Easy to add new battle types (e.g., review length, vote counts)
- Filter system can be adapted for other attributes (date ranges, playtime ranges)

## Technical Notes

### Design Decisions

- **Separation of Concerns**: Analyzer processes all data, UI filters display
- **Performance First**: Single-pass algorithm prevents performance issues
- **Default to Common**: English/Chinese default covers most users
- **Future-Proof**: All languages saved for potential future features

### Code Quality

- Clear separation between data processing and display
- Reusable filtering pattern for other tabs
- Consistent error handling with user-friendly messages
- Maintains existing checkpoint/resume functionality

## Related Files

- `analyzers/playtime_extremes.py` - Backend analysis logic
- `tabs/extreme_reviews_tab.py` - Frontend UI and display
- `data/processed/insights/` - Saved analysis results
- `.github/copilot-instructions.md` - Updated project documentation
