"""
Utility functions for Steam Review Analyzer.
Handles game details caching and retrieval from Steam API.
"""

import os
import json
import requests
from typing import Optional, Dict, Any


def get_game_details(appid: int) -> Optional[Dict[str, Any]]:
    """
    Get game details from cache or Steam Store API.
    Uses cache-first approach - API only called once per game.
    
    Args:
        appid: Steam application ID
        
    Returns:
        Dictionary with game details or None if failed
    """
    cache_folder = 'data/cache/app_details'
    os.makedirs(cache_folder, exist_ok=True)
    cache_file = os.path.join(cache_folder, f"{appid}_details.json")
    
    # Check cache first
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"[WARNING] Failed to read cache for appid {appid}: {e}")
            # Continue to fetch from API
    
    # Cache miss - fetch from Steam Store API
    url = f"http://store.steampowered.com/api/appdetails/?appids={appid}"
    try:
        print(f"[INFO] Fetching game details from Steam API for appid {appid}...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if str(appid) in data and data[str(appid)].get('success'):
            game_data = data[str(appid)]['data']
            
            # Save to cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(game_data, f, ensure_ascii=False, indent=2)
            
            print(f"[INFO] Game details cached: {game_data.get('name', 'Unknown')}")
            return game_data
        else:
            print(f"[WARNING] Steam API returned unsuccessful response for appid {appid}")
            
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch game details for appid {appid}: {e}")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"[ERROR] Failed to parse Steam API response for appid {appid}: {e}")
    
    return None


def get_game_name(appid: int) -> str:
    """
    Get game name from cache or Steam Store API.
    
    Args:
        appid: Steam application ID
        
    Returns:
        Game name or "AppID_{appid}" if not found
    """
    details = get_game_details(appid)
    if details and 'name' in details:
        return details['name']
    return f"AppID_{appid}"


def get_game_info(appid: int) -> Dict[str, str]:
    """
    Get commonly used game information.
    
    Args:
        appid: Steam application ID
        
    Returns:
        Dictionary with name, short_description, type, etc.
    """
    details = get_game_details(appid)
    if not details:
        return {
            'name': f"AppID_{appid}",
            'short_description': 'N/A',
            'type': 'N/A'
        }
    
    return {
        'name': details.get('name', f"AppID_{appid}"),
        'short_description': details.get('short_description', 'N/A'),
        'type': details.get('type', 'N/A'),
        'is_free': details.get('is_free', False),
        'developers': ', '.join(details.get('developers', [])),
        'publishers': ', '.join(details.get('publishers', [])),
        'release_date': details.get('release_date', {}).get('date', 'N/A')
    }
