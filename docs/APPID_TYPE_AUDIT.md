# App ID Type Handling Audit

## Overview

This document tracks how App IDs are handled across the codebase to ensure proper type consistency for `utils.get_game_name(appid)` calls.

## Type Requirements

- `utils.get_game_name(appid)` expects **INTEGER** parameter
- All file saving functions use **INTEGER** appid
- Regex extraction from filenames returns **STRINGS** → must convert to int

## File Naming Patterns

### CSV Reports

**Format**: `{appid}_{sanitized_title}_{date}_{count_str}_report.csv`

- **Example**: `1030300_Baldur_s_Gate_3_2025-10-16_2000max_report.csv`
- **Saved as**: INT appid (line 201 in `analyzers/language_report.py`)

### JSON Raw Data

**Format**: `{appid}_{date}_{count_str}_reviews.json`

- **Example**: `1030300_2025-10-16_281603_reviews.json`
- **Saved as**: INT appid (line 171 in `backend.py`)
- **Metadata contains**: INT appid (line 141 in `backend.py`)

### Extreme Review Results

**Format**: `{appid}_extreme_reviews_by_language_{date}.json`

- **Saved as**: INT appid
- **Metadata contains**: INT appid (passed through from source JSON)

## Code Audit Results

### ✅ FIXED: CSV Import (`tabs/data_collection_tab.py`)

#### Location: `import_csv_report()` - Lines 150-183

**Issue**: Regex extraction returned STRING appid, but `utils.get_game_name()` expects INT

**Fix Applied**:

```python
# Line 156: New format pattern
appid, title_from_name, date, reviews_str = match.groups()
appid = int(appid)  # Convert to integer for utils.get_game_name()

# Line 177: Old format fallback
appid = int(title_or_appid) if is_appid_only else 'N/A'  # Convert to int
```

**Status**: ✅ **FIXED** - Converts regex string to int before passing to `update_info_display()`

### ✅ CORRECT: JSON Loading (`tabs/data_collection_tab.py`)

#### Location: `run_json_analysis_job()` - Lines 285-311

**Implementation**:

```python
appid = review_data.get('metadata', {}).get('appid', 'N/A')
final_title = utils.get_game_name(appid) if isinstance(appid, int) else f"AppID_{appid}"
```

**Status**: ✅ **CORRECT** - JSON stores appid as INT directly, no conversion needed

### ✅ CORRECT: Extreme Reviews Loading (`tabs/extreme_reviews_tab.py`)

#### Location: `load_raw_json()` and `load_extreme_results()` - Lines 92-145

**Implementation**:

- Both methods load JSON files that contain INT appid in metadata
- `display_extreme_reviews()` extracts: `appid = metadata.get('appid', 'N/A')`
- Already INTEGER from JSON deserialization

**Status**: ✅ **CORRECT** - JSON stores appid as INT, works correctly

### ✅ CORRECT: Fetch & Analyze (`tabs/data_collection_tab.py`)

#### Location: `start_analysis_thread()` - Lines 227-267

**Implementation**:

```python
appid = int(self.appid_entry.get().strip())  # Line 234
game_title = utils.get_game_name(appid)  # Line 237
```

**Status**: ✅ **CORRECT** - Converts string input to INT immediately

## Summary

| Function                  | File                     | Status     | Notes                                     |
| ------------------------- | ------------------------ | ---------- | ----------------------------------------- |
| `import_csv_report()`     | `data_collection_tab.py` | ✅ FIXED   | Added `int(appid)` conversion after regex |
| `run_json_analysis_job()` | `data_collection_tab.py` | ✅ CORRECT | JSON stores INT appid naturally           |
| `load_raw_json()`         | `extreme_reviews_tab.py` | ✅ CORRECT | JSON stores INT appid naturally           |
| `load_extreme_results()`  | `extreme_reviews_tab.py` | ✅ CORRECT | JSON stores INT appid naturally           |
| `start_analysis_thread()` | `data_collection_tab.py` | ✅ CORRECT | Explicit int() conversion on input        |

## Best Practices

1. **File Saving**: Always use INT appid when constructing filenames
2. **JSON Metadata**: Store appid as INT in metadata dictionaries
3. **Regex Parsing**: Always convert extracted appid strings to INT immediately after regex match
4. **Type Checking**: Use `isinstance(appid, int)` before calling `utils.get_game_name()`
5. **Fallback**: If appid is not INT, display `f"AppID_{appid}"` as fallback

## Testing Checklist

- [x] CSV import with new format (`{appid}_{title}_{date}_{count}_report.csv`)
- [x] CSV import with old format (`{title_or_appid}_{date}_{count}_report.csv`)
- [ ] CSV import displays correct game name (e.g., "Baldur's Gate 3")
- [ ] JSON analysis displays correct game name
- [ ] Extreme reviews displays correct game name from raw JSON
- [ ] Extreme reviews displays correct game name from saved results

## Related Files

- `utils.py`: Game name fetching with cache-first API
- `tabs/data_collection_tab.py`: Import and analysis functions
- `tabs/extreme_reviews_tab.py`: Extreme review display
- `backend.py`: JSON saving with metadata
- `analyzers/language_report.py`: CSV report generation
