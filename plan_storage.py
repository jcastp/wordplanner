"""Module for saving and loading writing plans to/from disk."""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import plan
import config
import user_preferences


def plan_to_dict(plan_obj: plan.Plan) -> dict:
    """
    Convert a Plan object to a dictionary.

    Args:
        plan_obj: The Plan object to convert

    Returns:
        Dictionary representation of the plan
    """
    return plan_obj.to_dict()


def dict_to_plan(data: dict) -> plan.Plan:
    """
    Convert a dictionary to a Plan object.

    Args:
        data: Dictionary containing plan data

    Returns:
        Plan object created from the dictionary
    """
    return plan.Plan.from_dict(data)


def get_plans_directory() -> Path:
    """
    Get the plans directory path.

    Checks user preferences for a custom save directory first.
    If not set, uses the default from config.

    Returns:
        Path to the plans directory
    """
    # Check for custom save directory in user preferences
    custom_dir = user_preferences.get_custom_save_directory()

    if custom_dir:
        # Use custom directory with plans subdirectory
        return Path(custom_dir) / config.PLANS_SUBDIRECTORY

    # Otherwise, use default behavior
    save_dir = Path(config.SAVE_DIRECTORY)

    # If SAVE_DIRECTORY is absolute (for testing), use it directly
    if save_dir.is_absolute():
        return save_dir / config.PLANS_SUBDIRECTORY
    else:
        # Otherwise, use it relative to home directory (normal usage)
        return Path.home() / config.SAVE_DIRECTORY / config.PLANS_SUBDIRECTORY


def ensure_plans_directory():
    """Ensure the plans directory exists."""
    try:
        plans_dir = get_plans_directory()
        plans_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise PermissionError(f"Permission denied: Cannot create plans directory at {plans_dir}")
    except OSError as e:
        raise OSError(f"Failed to create plans directory: {e}")


def get_plan_filename(plan_name: str) -> str:
    """
    Generate a safe filename from a plan name.

    Args:
        plan_name: The name of the plan

    Returns:
        A sanitized filename with .json extension
    """
    # Remove invalid filename characters
    safe_name = "".join(c for c in plan_name if c.isalnum() or c in (' ', '-', '_')).strip()
    # Replace spaces with underscores
    safe_name = safe_name.replace(' ', '_')
    # Add timestamp with microseconds to make it unique
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"{safe_name}_{timestamp}.json"


def save_plan(plan_obj: plan.Plan, custom_path: Optional[Path] = None, overwrite_source: bool = True) -> Path:
    """
    Save a plan to disk.

    Args:
        plan_obj: The Plan object to save
        custom_path: Optional custom path to save to (defaults to plans directory)
        overwrite_source: If True and plan has a source_file, overwrite it. If False, create new file.

    Returns:
        Path where the plan was saved
    """
    ensure_plans_directory()

    if custom_path:
        filepath = custom_path
    elif overwrite_source and plan_obj.source_file:
        # Overwrite the original file this plan was loaded from
        filepath = plan_obj.source_file
    else:
        # Create a new file with timestamp
        plan_name = plan_obj.name or f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        filename = get_plan_filename(plan_name)
        filepath = get_plans_directory() / filename
        # Update source_file since we're creating a new file
        plan_obj.source_file = filepath

    # Save to file
    try:
        with open(filepath, 'w') as f:
            f.write(plan_obj.to_json())
    except PermissionError:
        raise PermissionError(f"Permission denied: Cannot write to {filepath}")
    except OSError as e:
        raise OSError(f"Failed to save plan to {filepath}: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error saving plan: {e}")

    return filepath


def load_plan(filepath: Path) -> plan.Plan:
    """
    Load a plan from disk.

    Args:
        filepath: Path to the plan file

    Returns:
        Loaded Plan object

    Raises:
        FileNotFoundError: If the plan file doesn't exist
        PermissionError: If the file cannot be read
        ValueError: If the file contains invalid JSON or plan data
    """
    # Check if file exists
    if not filepath.exists():
        raise FileNotFoundError(f"Plan file not found: {filepath}")

    # Check if path is a directory
    if filepath.is_dir():
        raise IsADirectoryError(f"Expected a file, got a directory: {filepath}")

    try:
        with open(filepath, 'r') as f:
            json_str = f.read()
    except PermissionError:
        raise PermissionError(f"Permission denied: Cannot read {filepath}")
    except OSError as e:
        raise OSError(f"Failed to read plan file {filepath}: {e}")

    # Validate file is not empty
    if not json_str.strip():
        raise ValueError(f"Plan file is empty: {filepath}")

    try:
        loaded_plan = plan.Plan.from_json(json_str)
    except ValueError as e:
        # Re-raise with more context about which file failed
        raise ValueError(f"Failed to load plan from {filepath}: {e}")

    # Track the source file so we can overwrite it later
    loaded_plan.source_file = filepath
    return loaded_plan


def list_saved_plans() -> List[dict]:
    """
    List all saved plans in the default directory.

    Returns:
        List of dictionaries with plan metadata (name, path, created_date)
    """
    try:
        ensure_plans_directory()
    except (PermissionError, OSError) as e:
        print(f"Error: Cannot access plans directory: {e}")
        return []

    plans = []
    plans_dir = get_plans_directory()

    try:
        json_files = list(plans_dir.glob("*.json"))
    except (PermissionError, OSError) as e:
        print(f"Error: Cannot list files in plans directory: {e}")
        return []

    for filepath in json_files:
        try:
            # Load plan to get metadata
            plan_obj = load_plan(filepath)
            plans.append({
                'name': plan_obj.name or filepath.stem,
                'path': filepath,
                'created_date': plan_obj.created_date,
                'total': plan_obj.total,
                'daily': plan_obj.daily,
                'time': plan_obj.time,
            })
        except FileNotFoundError:
            # File was deleted between listing and loading - skip it
            continue
        except (PermissionError, ValueError, OSError) as e:
            # Skip files that can't be loaded but show specific error
            print(f"Warning: Could not load {filepath.name}: {e}")
            continue
        except Exception as e:
            # Catch-all for unexpected errors
            print(f"Warning: Unexpected error loading {filepath.name}: {type(e).__name__}: {e}")
            continue

    # Sort by created date, newest first
    plans.sort(key=lambda p: p['created_date'] if p['created_date'] else datetime.min, reverse=True)

    return plans


def delete_plan(filepath: Path) -> bool:
    """
    Delete a saved plan.

    Args:
        filepath: Path to the plan file to delete

    Returns:
        True if successful, False otherwise

    Raises:
        FileNotFoundError: If the file doesn't exist
        PermissionError: If permission is denied
        OSError: For other OS-related errors
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Cannot delete: Plan file not found at {filepath}")

    if filepath.is_dir():
        raise IsADirectoryError(f"Cannot delete: Path is a directory, not a file: {filepath}")

    try:
        filepath.unlink()
        return True
    except PermissionError:
        raise PermissionError(f"Permission denied: Cannot delete {filepath}")
    except OSError as e:
        raise OSError(f"Failed to delete plan file {filepath}: {e}")
