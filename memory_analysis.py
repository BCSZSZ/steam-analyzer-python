"""
Memory Usage Analysis for Steam Analyzer

Analyzes memory consumption patterns when:
1. Loading large JSON files (300MB+)
2. Running analysis operations
3. Switching between tabs with different datasets
"""

import json
import os
import sys
import psutil
from datetime import datetime


def get_memory_mb():
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def get_file_size_mb(filepath):
    """Get file size in MB."""
    return os.path.getsize(filepath) / 1024 / 1024


def analyze_memory_scenario():
    """Simulate the user's scenario: loading 300MB data in multiple tabs."""
    
    print("=" * 80)
    print("MEMORY USAGE ANALYSIS - Steam Analyzer")
    print("=" * 80)
    
    # Find largest available test file
    test_files = []
    if os.path.exists('data/raw'):
        for filename in os.listdir('data/raw'):
            if filename.endswith('.json'):
                filepath = os.path.join('data/raw', filename)
                size_mb = get_file_size_mb(filepath)
                test_files.append((filepath, size_mb))
    
    if not test_files:
        print("ERROR: No test files found in data/raw/")
        return
    
    # Sort by size, use largest
    test_files.sort(key=lambda x: x[1], reverse=True)
    test_file = test_files[0][0]
    file_size = test_files[0][1]
    
    print(f"\nTest file: {test_file}")
    print(f"File size on disk: {file_size:.2f} MB")
    
    # Baseline memory
    baseline_mem = get_memory_mb()
    print(f"\nBaseline memory: {baseline_mem:.2f} MB")
    
    # Scenario 1: Load file once (simulating Tab 1)
    print("\n" + "-" * 80)
    print("SCENARIO 1: Loading file in Tab 1 (simulating Text Insights tab)")
    print("-" * 80)
    
    print("Loading JSON file...")
    with open(test_file, 'r', encoding='utf-8') as f:
        tab1_data = json.load(f)
    
    after_load1 = get_memory_mb()
    delta1 = after_load1 - baseline_mem
    
    reviews_count = len(tab1_data.get('reviews', []))
    print(f"✓ Loaded {reviews_count:,} reviews")
    print(f"Memory after load: {after_load1:.2f} MB")
    print(f"Memory increase: +{delta1:.2f} MB")
    print(f"Expansion ratio: {delta1 / file_size:.2f}x (JSON in memory vs disk)")
    
    # Scenario 2: Load same file again (simulating Tab 2)
    print("\n" + "-" * 80)
    print("SCENARIO 2: Loading SAME file in Tab 2 (simulating N-gram tab)")
    print("-" * 80)
    
    print("Loading JSON file again (second tab)...")
    with open(test_file, 'r', encoding='utf-8') as f:
        tab2_data = json.load(f)
    
    after_load2 = get_memory_mb()
    delta2 = after_load2 - after_load1
    
    print(f"✓ Loaded {len(tab2_data.get('reviews', [])):,} reviews")
    print(f"Memory after second load: {after_load2:.2f} MB")
    print(f"Memory increase: +{delta2:.2f} MB")
    print(f"Total memory used: {after_load2 - baseline_mem:.2f} MB")
    print(f"⚠️  DUPLICATION: Both tabs hold full copy in memory!")
    
    # Scenario 3: Load different file (simulating Tab 3)
    if len(test_files) > 1:
        test_file2 = test_files[1][0]
        file_size2 = test_files[1][1]
        
        print("\n" + "-" * 80)
        print(f"SCENARIO 3: Loading DIFFERENT file in Tab 3")
        print("-" * 80)
        print(f"Second file: {test_file2} ({file_size2:.2f} MB)")
        
        with open(test_file2, 'r', encoding='utf-8') as f:
            tab3_data = json.load(f)
        
        after_load3 = get_memory_mb()
        delta3 = after_load3 - after_load2
        
        print(f"✓ Loaded {len(tab3_data.get('reviews', [])):,} reviews")
        print(f"Memory after third load: {after_load3:.2f} MB")
        print(f"Memory increase: +{delta3:.2f} MB")
        print(f"Total memory used: {after_load3 - baseline_mem:.2f} MB")
        print(f"⚠️  THREE COPIES in memory simultaneously!")
    
    # Analysis summary
    print("\n" + "=" * 80)
    print("MEMORY ANALYSIS SUMMARY")
    print("=" * 80)
    
    total_mem = get_memory_mb()
    total_increase = total_mem - baseline_mem
    
    print(f"\n🔍 Current State:")
    print(f"   Total memory usage: {total_mem:.2f} MB")
    print(f"   Memory increase from baseline: +{total_increase:.2f} MB")
    print(f"   File size on disk: {file_size:.2f} MB")
    print(f"   Memory efficiency: {(total_increase / file_size):.2f}x disk size")
    
    print(f"\n⚠️  PROBLEMS IDENTIFIED:")
    print(f"   1. Each tab stores FULL copy of JSON data")
    print(f"   2. No memory cleanup when switching tabs")
    print(f"   3. No shared data between tabs")
    print(f"   4. 300MB file → ~{delta1:.0f} MB in memory PER TAB")
    print(f"   5. With 3 tabs loaded → ~{delta1 * 3:.0f} MB total!")
    
    print(f"\n💡 QUICK IMPROVEMENTS:")
    print(f"   1. Add 'Clear Data' button to each tab")
    print(f"   2. Centralized data store in main app (shared reference)")
    print(f"   3. Lazy loading: only load when needed")
    print(f"   4. Garbage collection hints after clearing data")
    
    print(f"\n📊 ESTIMATION for 300MB file:")
    expansion_ratio = delta1 / file_size
    print(f"   Memory per tab: ~{300 * expansion_ratio:.0f} MB")
    print(f"   3 tabs with 300MB data: ~{300 * expansion_ratio * 3:.0f} MB")
    print(f"   Recommended RAM: 8GB+ (with other programs running)")
    
    # Cleanup test
    print("\n" + "-" * 80)
    print("CLEANUP TEST: What happens when we delete references?")
    print("-" * 80)
    
    before_cleanup = get_memory_mb()
    print(f"Memory before cleanup: {before_cleanup:.2f} MB")
    
    del tab1_data
    del tab2_data
    if len(test_files) > 1:
        del tab3_data
    
    # Suggest garbage collection
    import gc
    gc.collect()
    
    after_cleanup = get_memory_mb()
    freed = before_cleanup - after_cleanup
    
    print(f"Memory after cleanup: {after_cleanup:.2f} MB")
    print(f"Memory freed: {freed:.2f} MB")
    print(f"Cleanup efficiency: {(freed / total_increase * 100):.1f}% recovered")
    
    if freed > 0:
        print(f"✅ Cleanup works! Memory can be freed.")
    else:
        print(f"⚠️  Memory not immediately freed (Python's GC will reclaim eventually)")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Check if psutil is available
    try:
        import psutil
    except ImportError:
        print("ERROR: psutil not installed")
        print("Install with: pip install psutil")
        sys.exit(1)
    
    analyze_memory_scenario()
