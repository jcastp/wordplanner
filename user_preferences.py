"""
User preferences: the save directory and the Settings choices.

Preferences live in preferences.json next to the plans folder. Each setting
has a default and a validator, so a missing, old or hand-edited file always
gives usable values. Reads are cached per file (formatting a calendar asks
for the date format hundreds of times); saving updates the cache.
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


# Last read or written preferences, per file: (path, preferences)
_cache = None

PATTERNS = ("flat", "valley", "mountain", "rising", "declining", "random")
WEEKEND_MODES = ("same", "different", "spare")
DATE_FORMATS = ("iso", "dmy", "mdy", "text")


def _valid_pattern_config(value):
    return isinstance(value, dict) and all(isinstance(k, str) for k in value)


# Setting: (default, validator)
SETTINGS = {
    'default_pattern': ("flat", lambda v: v in PATTERNS),
    'default_pattern_config': ({}, _valid_pattern_config),
    'default_weekend_mode': ("same", lambda v: v in WEEKEND_MODES),
    'default_weekend_daily': (0, lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)
                              and 0 <= v <= config.MAX_DAILY_WORDS),
    'first_weekday': (0, lambda v: v in (0, 6)),   # Monday or Sunday
    'date_format': ("iso", lambda v: v in DATE_FORMATS),
    'colors': (True, lambda v: isinstance(v, bool)),
}


def load_preferences() -> Dict[str, Any]:
    """
    Load user preferences from disk.

    Returns a dictionary with user preferences. If the file doesn't exist
    or can't be loaded, returns an empty dictionary (default preferences).
    """
    global _cache
    prefs_file = get_preferences_file()
    if _cache is not None and _cache[0] == prefs_file:
        return dict(_cache[1])

    preferences = {}
    if prefs_file.exists():
        try:
            with open(prefs_file, 'r') as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                preferences = loaded
        except (json.JSONDecodeError, OSError):
            # If preferences file is corrupted or can't be read, use the defaults
            pass

    _cache = (prefs_file, preferences)
    return dict(preferences)


def get_preference(name: str) -> Any:
    """A setting's value, or its default if it's missing or invalid."""
    default, valid = SETTINGS[name]
    value = load_preferences().get(name, default)
    return value if valid(value) else default


def set_preference(name: str, value: Any):
    """Save one setting (raises ValueError for an invalid value)."""
    default, valid = SETTINGS[name]
    if not valid(value):
        raise ValueError(f"invalid value for {name}: {value!r}")
    prefs = load_preferences()
    prefs[name] = value
    save_preferences(prefs)


def save_preferences(preferences: Dict[str, Any]):
    """
    Save user preferences to disk.

    Args:
        preferences: Dictionary containing user preferences
    """
    global _cache
    ensure_preferences_directory()
    prefs_file = get_preferences_file()

    write_atomically(prefs_file, json.dumps(preferences, indent=2))
    _cache = (prefs_file, dict(preferences))


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
