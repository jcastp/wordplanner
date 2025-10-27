"""Module for saving and loading writing plans to/from disk."""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import plan


# Default directory for storing plans
DEFAULT_PLANS_DIR = Path.home() / ".planeapalabras" / "plans"


def ensure_plans_directory():
    """Ensure the plans directory exists."""
    DEFAULT_PLANS_DIR.mkdir(parents=True, exist_ok=True)


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
    # Add timestamp to make it unique
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe_name}_{timestamp}.json"


def save_plan(plan_obj: plan.Plan, custom_path: Optional[Path] = None) -> Path:
    """
    Save a plan to disk.

    Args:
        plan_obj: The Plan object to save
        custom_path: Optional custom path to save to (defaults to plans directory)

    Returns:
        Path where the plan was saved
    """
    ensure_plans_directory()

    if custom_path:
        filepath = custom_path
    else:
        # Use plan name or generate a default name
        plan_name = plan_obj.name or f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        filename = get_plan_filename(plan_name)
        filepath = DEFAULT_PLANS_DIR / filename

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

    return plan.Plan.from_json(json_str)


def list_saved_plans() -> List[dict]:
    """
    List all saved plans in the default directory.

    Returns:
        List of dictionaries with plan metadata (name, path, created_date)
    """
    ensure_plans_directory()

    plans = []
    for filepath in DEFAULT_PLANS_DIR.glob("*.json"):
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
