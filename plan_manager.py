"""
Multiple Plans Management Module

This module provides functionality for managing multiple writing plans,
including filtering, sorting, comparison, archiving, and organization.
"""

from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import plan
import plan_storage
import config


def filter_plans_by_status(plans: List[plan.Plan], status: str) -> List[plan.Plan]:
    """
    Filter plans by status.

    Args:
        plans: List of Plan objects
        status: Status to filter by ("active", "archived", "completed")

    Returns:
        List of plans matching the status
    """
    return [p for p in plans if p.status == status]


def filter_plans_by_category(plans: List[plan.Plan], category: str) -> List[plan.Plan]:
    """
    Filter plans by category.

    Args:
        plans: List of Plan objects
        category: Category to filter by

    Returns:
        List of plans matching the category
    """
    return [p for p in plans if p.category == category]


def filter_plans_by_tag(plans: List[plan.Plan], tag: str) -> List[plan.Plan]:
    """
    Filter plans by tag.

    Args:
        plans: List of Plan objects
        tag: Tag to filter by

    Returns:
        List of plans that have the specified tag
    """
    return [p for p in plans if tag in p.tags]


def get_active_plan() -> Optional[plan.Plan]:
    """
    Get the currently active plan.

    Returns:
        The active Plan object, or None if no plan is marked as active
    """
    plans_info = plan_storage.list_saved_plans()

    for plan_info in plans_info:
        try:
            p = plan_storage.load_plan(plan_info['path'])
            if p.is_active:
                return p
        except Exception:
            continue

    return None


def set_active_plan(plan_path: Path) -> bool:
    """
    Set a plan as the active plan. Clears the active flag from all other plans.

    Args:
        plan_path: Path to the plan to set as active

    Returns:
        True if successful, False otherwise
    """
    try:
        # First, clear active flag from all plans
        plans_info = plan_storage.list_saved_plans()
        for plan_info in plans_info:
            try:
                p = plan_storage.load_plan(plan_info['path'])
                if p.is_active and plan_info['path'] != plan_path:
                    p.is_active = False
                    p.last_modified = datetime.now()
                    plan_storage.save_plan(p, overwrite_source=True)
            except Exception:
                continue

        # Set the target plan as active
        target_plan = plan_storage.load_plan(plan_path)
        target_plan.is_active = True
        target_plan.last_modified = datetime.now()
        plan_storage.save_plan(target_plan, overwrite_source=True)

        return True
    except Exception as e:
        print(f"Error setting active plan: {e}")
        return False


def clear_active_plan() -> bool:
    """
    Clear the active flag from all plans.

    Returns:
        True if successful, False otherwise
    """
    try:
        plans_info = plan_storage.list_saved_plans()
        for plan_info in plans_info:
            try:
                p = plan_storage.load_plan(plan_info['path'])
                if p.is_active:
                    p.is_active = False
                    p.last_modified = datetime.now()
                    plan_storage.save_plan(p, overwrite_source=True)
            except Exception:
                continue
        return True
    except Exception:
        return False


def archive_plan(plan_obj: plan.Plan) -> bool:
    """
    Archive a plan by setting its status to "archived".

    Args:
        plan_obj: Plan object to archive

    Returns:
        True if successful, False otherwise
    """
    try:
        plan_obj.status = "archived"
        plan_obj.is_active = False  # Clear active flag when archiving
        plan_obj.last_modified = datetime.now()
        plan_storage.save_plan(plan_obj, overwrite_source=True)
        return True
    except Exception as e:
        print(f"Error archiving plan: {e}")
        return False


def unarchive_plan(plan_obj: plan.Plan) -> bool:
    """
    Unarchive a plan by setting its status back to "active".

    Args:
        plan_obj: Plan object to unarchive

    Returns:
        True if successful, False otherwise
    """
    try:
        plan_obj.status = "active"
        plan_obj.last_modified = datetime.now()
        plan_storage.save_plan(plan_obj, overwrite_source=True)
        return True
    except Exception as e:
        print(f"Error unarchiving plan: {e}")
        return False


def mark_plan_completed(plan_obj: plan.Plan) -> bool:
    """
    Mark a plan as completed.

    Args:
        plan_obj: Plan object to mark as completed

    Returns:
        True if successful, False otherwise
    """
    try:
        plan_obj.status = "completed"
        plan_obj.is_active = False  # Clear active flag when completing
        plan_obj.last_modified = datetime.now()
        plan_storage.save_plan(plan_obj, overwrite_source=True)
        return True
    except Exception as e:
        print(f"Error marking plan as completed: {e}")
        return False


def add_tag_to_plan(plan_obj: plan.Plan, tag: str) -> bool:
    """
    Add a tag to a plan.

    Args:
        plan_obj: Plan object
        tag: Tag to add

    Returns:
        True if successful, False otherwise
    """
    try:
        tag = tag.strip().lower()
        if tag and tag not in plan_obj.tags:
            plan_obj.tags.append(tag)
            plan_obj.last_modified = datetime.now()
            plan_storage.save_plan(plan_obj, overwrite_source=True)
        return True
    except Exception as e:
        print(f"Error adding tag: {e}")
        return False


def remove_tag_from_plan(plan_obj: plan.Plan, tag: str) -> bool:
    """
    Remove a tag from a plan.

    Args:
        plan_obj: Plan object
        tag: Tag to remove

    Returns:
        True if successful, False otherwise
    """
    try:
        tag = tag.strip().lower()
        if tag in plan_obj.tags:
            plan_obj.tags.remove(tag)
            plan_obj.last_modified = datetime.now()
            plan_storage.save_plan(plan_obj, overwrite_source=True)
        return True
    except Exception as e:
        print(f"Error removing tag: {e}")
        return False


def set_plan_category(plan_obj: plan.Plan, category: str) -> bool:
    """
    Set the category of a plan.

    Args:
        plan_obj: Plan object
        category: Category to set

    Returns:
        True if successful, False otherwise
    """
    try:
        if category in config.PLAN_CATEGORIES or category is None:
            plan_obj.category = category
            plan_obj.last_modified = datetime.now()
            plan_storage.save_plan(plan_obj, overwrite_source=True)
            return True
        else:
            print(f"Invalid category: {category}")
            return False
    except Exception as e:
        print(f"Error setting category: {e}")
        return False


def sort_plans(plans: List[plan.Plan], sort_by: str = "modified", reverse: bool = True) -> List[plan.Plan]:
    """
    Sort plans by various criteria.

    Args:
        plans: List of Plan objects
        sort_by: Sort criterion ("name", "created", "modified", "completion", "deadline")
        reverse: Whether to reverse the sort order (default: True for descending)

    Returns:
        Sorted list of plans
    """
    if sort_by == "name":
        return sorted(plans, key=lambda p: (p.name or "").lower(), reverse=reverse)
    elif sort_by == "created":
        return sorted(plans, key=lambda p: p.created_date or datetime.min, reverse=reverse)
    elif sort_by == "modified":
        return sorted(plans, key=lambda p: p.last_modified or datetime.min, reverse=reverse)
    elif sort_by == "completion":
        return sorted(plans, key=lambda p: p.get_completion_percentage(), reverse=reverse)
    elif sort_by == "deadline":
        # Calculate end date for each plan
        def get_end_date(p):
            if p.start_date:
                return p.end_date or p.start_date
            return datetime.max  # Plans without dates go to the end
        return sorted(plans, key=get_end_date, reverse=reverse)
    else:
        # Default to modified
        return sorted(plans, key=lambda p: p.last_modified or datetime.min, reverse=reverse)


def get_plans_by_status() -> Dict[str, List[plan.Plan]]:
    """
    Get all plans organized by status.

    Returns:
        Dictionary with status as keys and lists of plans as values
    """
    plans_info = plan_storage.list_saved_plans()
    plans_by_status = {
        "active": [],
        "archived": [],
        "completed": []
    }

    for plan_info in plans_info:
        try:
            p = plan_storage.load_plan(plan_info['path'])
            status = p.status if p.status in plans_by_status else "active"
            plans_by_status[status].append(p)
        except Exception:
            continue

    return plans_by_status


def get_all_plans() -> List[plan.Plan]:
    """
    Load and return all saved plans.

    Returns:
        List of all Plan objects
    """
    plans_info = plan_storage.list_saved_plans()
    plans = []

    for plan_info in plans_info:
        try:
            p = plan_storage.load_plan(plan_info['path'])
            plans.append(p)
        except Exception:
            continue

    return plans


def get_all_tags() -> List[str]:
    """
    Get all unique tags used across all plans.

    Returns:
        Sorted list of unique tags
    """
    all_tags = set()
    plans = get_all_plans()

    for p in plans:
        all_tags.update(p.tags)

    return sorted(list(all_tags))


def get_all_categories() -> Dict[str, int]:
    """
    Get all categories used with counts.

    Returns:
        Dictionary mapping category names to count of plans
    """
    categories = {}
    plans = get_all_plans()

    for p in plans:
        if p.category:
            categories[p.category] = categories.get(p.category, 0) + 1

    return categories


def compare_plans(plan_list: List[plan.Plan]) -> Dict:
    """
    Compare multiple plans side by side.

    Args:
        plan_list: List of Plan objects to compare

    Returns:
        Dictionary with comparison data
    """
    if not plan_list:
        return {}

    comparison = {
        'plans': [],
        'summary': {
            'total_plans': len(plan_list),
            'total_words': sum(p.total for p in plan_list),
            'total_days': sum(p.time for p in plan_list),
            'avg_daily': sum(p.daily for p in plan_list) / len(plan_list) if plan_list else 0,
        }
    }

    for p in plan_list:
        plan_data = {
            'name': p.name or "Unnamed",
            'total': p.total,
            'daily': p.daily,
            'time': p.time,
            'category': p.category,
            'status': p.status,
            'completion': p.get_completion_percentage(),
            'written': p.get_total_written(),
            'remaining': p.get_remaining_words(),
            'start_date': p.start_date.strftime('%Y-%m-%d') if p.start_date else None,
            'is_active': p.is_active,
        }

        # Calculate on-track status if started
        if p.start_date and p.progress:
            on_track, info = p.is_on_track()
            plan_data['on_track'] = on_track
            plan_data['track_status'] = info.get('status', 'unknown')
        else:
            plan_data['on_track'] = None
            plan_data['track_status'] = 'not_started'

        comparison['plans'].append(plan_data)

    return comparison


def search_plans(query: str, search_in: List[str] = None) -> List[plan.Plan]:
    """
    Search for plans by query string.

    Args:
        query: Search query
        search_in: List of fields to search in (default: ["name", "tags", "category"])

    Returns:
        List of matching Plan objects
    """
    if search_in is None:
        search_in = ["name", "tags", "category"]

    query = query.lower().strip()
    if not query:
        return []

    matching_plans = []
    plans = get_all_plans()

    for p in plans:
        # Search in name
        if "name" in search_in and p.name and query in p.name.lower():
            matching_plans.append(p)
            continue

        # Search in tags
        if "tags" in search_in and p.tags:
            if any(query in tag.lower() for tag in p.tags):
                matching_plans.append(p)
                continue

        # Search in category
        if "category" in search_in and p.category and query in p.category.lower():
            matching_plans.append(p)
            continue

    return matching_plans


def get_plan_statistics() -> Dict:
    """
    Get overall statistics across all plans.

    Returns:
        Dictionary with statistics
    """
    plans = get_all_plans()
    plans_by_status = get_plans_by_status()

    stats = {
        'total_plans': len(plans),
        'active_plans': len(plans_by_status['active']),
        'archived_plans': len(plans_by_status['archived']),
        'completed_plans': len(plans_by_status['completed']),
        'total_word_goal': sum(p.total for p in plans),
        'total_words_written': sum(p.get_total_written() for p in plans),
        'plans_with_progress': len([p for p in plans if p.progress]),
        'categories': get_all_categories(),
        'tags': get_all_tags(),
        'active_plan': get_active_plan(),
    }

    # Calculate average completion for active plans
    active_plans = plans_by_status['active']
    if active_plans:
        stats['avg_completion'] = sum(p.get_completion_percentage() for p in active_plans) / len(active_plans)
    else:
        stats['avg_completion'] = 0

    return stats
