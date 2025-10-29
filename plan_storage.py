"""Module for saving and loading writing plans to/from disk."""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import plan
import config


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

    Returns:
        Path to the plans directory
    """
    save_dir = Path(config.SAVE_DIRECTORY)

    # If SAVE_DIRECTORY is absolute (for testing), use it directly
    if save_dir.is_absolute():
        return save_dir / config.PLANS_SUBDIRECTORY
    else:
        # Otherwise, use it relative to home directory (normal usage)
        return Path.home() / config.SAVE_DIRECTORY / config.PLANS_SUBDIRECTORY


def ensure_plans_directory():
    """Ensure the plans directory exists."""
    plans_dir = get_plans_directory()
    plans_dir.mkdir(parents=True, exist_ok=True)


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
    with open(filepath, 'w') as f:
        f.write(plan_obj.to_json())

    return filepath


def load_plan(filepath: Path) -> plan.Plan:
    """
    Load a plan from disk.

    Args:
        filepath: Path to the plan file

    Returns:
        Loaded Plan object
    """
    with open(filepath, 'r') as f:
        json_str = f.read()

    loaded_plan = plan.Plan.from_json(json_str)
    # Track the source file so we can overwrite it later
    loaded_plan.source_file = filepath
    return loaded_plan


def list_saved_plans() -> List[dict]:
    """
    List all saved plans in the default directory.

    Returns:
        List of dictionaries with plan metadata (name, path, created_date)
    """
    ensure_plans_directory()

    plans = []
    for filepath in get_plans_directory().glob("*.json"):
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
        except Exception as e:
            # Skip files that can't be loaded
            print(f"Warning: Could not load {filepath}: {e}")
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
    """
    try:
        filepath.unlink()
        return True
    except Exception:
        return False
