# Stopwords Manager

## Overview

The Stopwords Manager provides a comprehensive system for managing custom stopwords used across all text analysis features (N-gram, TF-IDF, BERTopic). It features a table-based UI with automatic loading and dual-key support for each game.

Stopwords are stored in `data/stopwords.json` and automatically applied to all text analysis operations.

## Key Features

### 1. Automatic Loading
- Stopwords JSON file (`data/stopwords.json`) is loaded automatically when the tab opens
- No manual "Load Stopwords" button click required
- File is created with default values if it doesn't exist

### 2. Dual-Key System
Each game generates **two keys**:
- **English Key**: `{appid}_{gamename}` - Auto-populated with tokenized English game name
- **Chinese Key**: `{appid}_{gamename}_CN` - Empty by default, for manual Chinese term input

Example:
```
1030300_hollow_knight_silksong: hollow, knight, silksong
1030300_hollow_knight_silksong_CN: (empty - add Chinese terms manually)
```

### 3. Table View Interface
- **Game-Specific Section**: Replaced text editor with Treeview table
- **Columns**:
  - `Game Key (Read-only)`: Displays the game identifier
  - `Terms (Double-click to edit)`: Comma-separated stopwords
- **Editing**: Double-click any row to open edit dialog
- **Sorting**: Table rows automatically sorted by game key

### 4. Universal Stopwords Integration
- TextProcessor merges three stopword sources:
  1. Built-in stopwords (ENGLISH_STOPWORDS / CHINESE_STOPWORDS)
  2. Universal custom stopwords (from JSON)
  3. All game-specific stopwords (both English and CN keys)

## File Structure

### JSON Format (`data/stopwords.json`)
```json
{
  "universal": [
    "dlc", "jrpg", "rpg", "游戏", "评分"
  ],
  "game_specific": {
    "1030300_hollow_knight_silksong": ["hollow", "knight", "silksong"],
    "1030300_hollow_knight_silksong_CN": [],
    "730_counter_strike_global_offensive": ["counter", "strike", "global", "offensive"],
    "730_counter_strike_global_offensive_CN": ["反恐", "精英"]
  }
}
```

## Usage Workflows

### Adding Game-Specific Stopwords

1. **Automatic (from cache)**:
   - Click "Load from Cache" button
   - Automatically generates both English and CN keys for all cached games
   - English key populated with tokenized game name
   - CN key left blank for manual input

2. **Manual (double-click edit)**:
   - Locate the game row in the table
   - Double-click the row
   - Edit dialog opens
   - Add/modify comma-separated terms
   - Click "Save" or press Enter

### Adding Chinese Terms

1. Find the `{appid}_{gamename}_CN` row (it will be empty)
2. Double-click to open edit dialog
3. Add Chinese terms separated by commas
4. Example: `神之天平, 修订版, 角色扮演`
5. Click "Save Changes" button to persist

### Editing Universal Stopwords

1. Universal stopwords section uses text editor (unchanged)
2. One term per line
3. Can include English or Chinese terms
4. Applied to all games and all analysis types automatically

## Technical Implementation

### TextProcessor Integration (`analyzers/text_processor.py`)

```python
def __init__(self):
    """Initialize with custom stopwords loading."""
    jieba.initialize()
    self.custom_stopwords = self._load_custom_stopwords()

def _load_custom_stopwords(self):
    """Load from data/stopwords.json."""
    # Returns {'universal': [], 'game_specific': {}}
    
def get_stopwords(self, language: str):
    """Merge built-in + universal + game-specific stopwords."""
    # 1. Get built-in stopwords for language
    # 2. Add universal custom stopwords
    # 3. Add all game-specific terms (English + CN)
    # Returns merged set
```

### Automatic Application

- **N-gram Analyzer**: Uses `text_processor.tokenize(remove_stopwords=True)`
- **TF-IDF Analyzer**: Uses `text_processor.tokenize(remove_stopwords=True)`
- **BERTopic Analyzer**: Uses custom stopwords directly
- No code changes needed in analyzers - stopwords applied automatically

### Load from Cache Logic (`tabs/bertopic_stopwords_tab.py`)

```python
def load_from_cache(self):
    """Generate dual keys for each cached game."""
    for game in cached_games:
        appid = extract_appid(game)
        name = get_game_name(game)
        clean_name = sanitize(name)
        
        # Create English key with tokens
        game_key = f"{appid}_{clean_name}"
        tokens = tokenize_english(name)
        existing_games[game_key] = tokens
        
        # Create empty CN key
        game_key_cn = f"{appid}_{clean_name}_CN"
        existing_games[game_key_cn] = []
    
    # Update table view
    populate_table(existing_games)
```

## UI Components

### Table View
- **Widget**: `ttk.Treeview` with 2 columns
- **Scrollbars**: Both vertical and horizontal
- **Event Binding**: `<Double-1>` triggers `edit_game_terms()`

### Edit Dialog
- **Toplevel window**: Modal dialog
- **Text editor**: Multi-line input for terms
- **Keybindings**: Enter=Save, Escape=Cancel
- **Validation**: Parses comma-separated values on save

## Migration Notes

### Changes from Previous Version

**Before (Text Editor)**:
- Game-specific section was a plain text editor
- Manual formatting required: `appid_name: term1, term2`
- No structured validation
- Single key per game

**After (Table View)**:
- Structured Treeview table
- Read-only keys, editable values
- Double-click dialog for editing
- Dual keys per game (English + CN)
- Automatic sorting

### Compatibility

- JSON file format unchanged (backward compatible)
- Existing game_specific entries preserved
- CN keys added as new entries with `_CN` suffix
- No data migration required

## Testing Checklist

- [ ] Load stopwords automatically on tab open
- [ ] Load from cache generates both English and CN keys
- [ ] Double-click opens edit dialog
- [ ] Edit dialog saves changes to table
- [ ] Save button persists changes to JSON file
- [ ] Empty CN keys saved as empty arrays
- [ ] N-gram analysis uses custom stopwords
- [ ] TF-IDF analysis uses custom stopwords
- [ ] Custom stopwords apply to both English and Chinese languages
- [ ] Table sorting works correctly

## Future Enhancements

1. **Bulk Operations**: Add/delete multiple games at once
2. **Search/Filter**: Filter table by game name or terms
3. **Import/Export**: CSV import/export for batch editing
4. **Validation**: Highlight duplicate terms across games
5. **Preview**: Show stopwords impact on sample reviews
6. **Auto-CN**: Automatic Chinese name detection from Steam
