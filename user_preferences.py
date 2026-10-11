"""
User preferences management for planeapalabras.

Stores user-configurable settings like custom save directory.
"""

import json
from file_utils import write_atomically
from pathlib import Path
from typing import Optional, Dict, Any
import config


def get_preferences_file() -> Path:
    """Get the path to the user preferences file."""
    save_dir = Path(config.SAVE_DIRECTORY)

    # If SAVE_DIRECTORY is absolute (for testing), use it directly
    if save_dir.is_absolute():
        return save_dir / "preferences.json"
    else:
        # Otherwise, use it relative to home directory (normal usage)
        return Path.home() / config.SAVE_DIRECTORY / "preferences.json"


def ensure_preferences_directory():
    """Ensure the preferences directory exists."""
    prefs_file = get_preferences_file()
    prefs_file.parent.mkdir(parents=True, exist_ok=True)


def load_preferences() -> Dict[str, Any]:
    """
    Load user preferences from disk.

    Returns a dictionary with user preferences. If the file doesn't exist
    or can't be loaded, returns an empty dictionary (default preferences).
    """
    prefs_file = get_preferences_file()

    if not prefs_file.exists():
        return {}

    try:
        with open(prefs_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # If preferences file is corrupted or can't be read, return empty dict
        return {}


def save_preferences(preferences: Dict[str, Any]):
    """
    Save user preferences to disk.

    Args:
        preferences: Dictionary containing user preferences
    """
    ensure_preferences_directory()
    prefs_file = get_preferences_file()

    write_atomically(prefs_file, json.dumps(preferences, indent=2))


def get_custom_save_directory() -> Optional[str]:
    """
    Get the custom save directory from user preferences.

    Returns:
        The custom save directory path as a string, or None if not set.
    """
    prefs = load_preferences()
    return prefs.get('custom_save_directory')


def set_custom_save_directory(directory: Optional[str]):
    """
    Set or clear the custom save directory in user preferences.

    Args:
        directory: The custom directory path as a string, or None to clear
    """
    prefs = load_preferences()

    if directory is None:
        # Remove the custom directory setting
        prefs.pop('custom_save_directory', None)
    else:
        prefs['custom_save_directory'] = directory

    save_preferences(prefs)


def reset_to_defaults():
    """Reset all preferences to default values."""
    save_preferences({})
