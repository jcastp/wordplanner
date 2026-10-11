"""Module for saving and loading writing plans to/from disk."""

import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import plan
import config
import user_preferences
from file_utils import write_atomically, backup_path


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

    old_source = plan_obj.source_file
    old_active = plan_obj.is_active
    old_modified = plan_obj.last_modified
    new_file = False

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
        new_file = True
        # Update source_file since we're creating a new file
        plan_obj.source_file = filepath
        # A copy of a saved plan is never the active plan: the original keeps
        # that role, so there is only ever one active plan
        if old_source is not None:
            plan_obj.is_active = False

    # "Last modified" means the content changed, not that it was written again
    if new_file or plan_obj.has_unsaved_changes():
        plan_obj.last_modified = datetime.now()

    # Save to file: atomically, keeping the previous version as <file>.bak
    try:
        write_atomically(filepath, plan_obj.to_json(), backup=True)
    except BaseException as e:
        plan_obj.source_file = old_source
        plan_obj.is_active = old_active
        plan_obj.last_modified = old_modified
        if isinstance(e, PermissionError):
            raise PermissionError(f"Permission denied: Cannot write to {filepath}")
        if isinstance(e, OSError):
            raise OSError(f"Failed to save plan to {filepath}: {e}")
        if isinstance(e, Exception):
            raise RuntimeError(f"Unexpected error saving plan: {e}")
        raise

    plan_obj.mark_saved()
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
        message = f"Failed to load plan from {filepath}: {e}"
        if backup_path(filepath).exists():
            message += f" (the previous version is in {backup_path(filepath).name})"
        raise ValueError(message)

    # Track the source file so we can overwrite it later
    loaded_plan.source_file = filepath
    loaded_plan.mark_saved()
    return loaded_plan


# Files already reported as unreadable, as (path, modification time): each
# broken file is reported once per session, not on every listing (S5)
_reported_load_errors = set()


def _report_load_error(filepath: Path, error: Exception):
    try:
        version = filepath.stat().st_mtime_ns
    except OSError:
        version = None
    key = (str(filepath), version)
    if key in _reported_load_errors:
        return
    _reported_load_errors.add(key)
    if isinstance(error, (PermissionError, ValueError, OSError)):
        print(f"Warning: Could not load {filepath.name}: {error}")
    else:
        print(f"Warning: Unexpected error loading {filepath.name}: {type(error).__name__}: {error}")


def load_all_plans() -> List[plan.Plan]:
    """
    Load every plan in the plans directory, reading each file once.

    Files that can't be loaded are skipped; each is reported once per
    session (again only if the file changes).

    Returns:
        List of Plan objects, in file name order
    """
    try:
        ensure_plans_directory()
        json_files = sorted(get_plans_directory().glob("*.json"))
    except (PermissionError, OSError) as e:
        print(f"Error: Cannot access plans directory: {e}")
        return []

    plans = []
    for filepath in json_files:
        try:
            plans.append(load_plan(filepath))
        except FileNotFoundError:
            # Deleted between listing and loading
            continue
        except Exception as e:
            _report_load_error(filepath, e)
    return plans


def list_saved_plans() -> List[dict]:
    """
    List all saved plans in the default directory.

    Returns:
        List of dictionaries with plan metadata (name, path, created_date,
        total, daily, time), newest first
    """
    plans = [{
        'name': plan_obj.name or plan_obj.source_file.stem,
        'path': plan_obj.source_file,
        'created_date': plan_obj.created_date,
        'total': plan_obj.total,
        'daily': plan_obj.daily,
        'time': plan_obj.time,
    } for plan_obj in load_all_plans()]

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
        backup_path(filepath).unlink(missing_ok=True)
        return True
    except PermissionError:
        raise PermissionError(f"Permission denied: Cannot delete {filepath}")
    except OSError as e:
        raise OSError(f"Failed to delete plan file {filepath}: {e}")


def move_plans(from_dir: Path, to_dir: Path) -> tuple:
    """
    Move every plan file (and its .bak backup) from one plans directory to another.

    Used when the save directory changes, so existing plans don't disappear
    from the list. A plan whose file name already exists in to_dir is left
    where it is.

    Returns:
        (number of plans moved, list of file names left behind)
    """
    from_dir, to_dir = Path(from_dir), Path(to_dir)
    if not from_dir.is_dir() or from_dir.resolve() == to_dir.resolve():
        return 0, []
    to_dir.mkdir(parents=True, exist_ok=True)

    moved, skipped = 0, []
    for filepath in sorted(from_dir.glob("*.json")):
        target = to_dir / filepath.name
        if target.exists():
            skipped.append(filepath.name)
            continue
        shutil.move(str(filepath), str(target))
        if backup_path(filepath).exists() and not backup_path(target).exists():
            shutil.move(str(backup_path(filepath)), str(backup_path(target)))
        moved += 1
    return moved, skipped
