"""
Multiple Plans Management UI Module

This module provides user interface functions for managing multiple writing plans.
"""

from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

import plan
import plan_manager
import plan_storage
import config
import ui_utils


console = Console()


def display_plans_overview():
    """Display an overview of all plans organized by status."""
    ui_utils.display_header("My Writing Plans", width=70)

    # Get plans organized by status
    plans_by_status = plan_manager.get_plans_by_status()
    stats = plan_manager.get_plan_statistics()

    # Display summary
    print(f"\nTotal Plans: {stats['total_plans']}")
    print(f"Active: {stats['active_plans']} | Archived: {stats['archived_plans']} | Completed: {stats['completed_plans']}")
    print(f"Total Word Goal: {stats['total_word_goal']:,} words")
    print(f"Total Written: {stats['total_words_written']:,} words")

    if stats['active_plan']:
        print(f"\n★ Currently Active: {stats['active_plan'].name}")

    # Display active plans
    if plans_by_status['active']:
        _display_plans_section("Active Plans", plans_by_status['active'], show_progress=True)

    # Display completed plans
    if plans_by_status['completed']:
        _display_plans_section("Completed Plans", plans_by_status['completed'], show_progress=False)

    # Display archived plans
    if plans_by_status['archived']:
        _display_plans_section("Archived Plans", plans_by_status['archived'], show_progress=False)

    print("=" * 70)


def _display_plans_section(title: str, plans: list, show_progress: bool = True):
    """Display a section of plans."""
    print(f"\n{title} ({len(plans)}):")
    print("-" * 70)

    for p in plans:
        # Basic info
        name = p.name or "Unnamed Plan"
        active_marker = "★ " if p.is_active else "  "

        info_parts = [f"{p.total:,.0f} words"]

        if p.category:
            info_parts.append(f"[{p.category}]")

        if p.tags:
            info_parts.append(f"Tags: {', '.join(p.tags)}")

        info_str = " | ".join(info_parts)

        print(f"{active_marker}• {name}")
        print(f"   {info_str}")

        # Progress info for active plans
        if show_progress and p.start_date and p.progress:
            completion = p.get_completion_percentage()
            on_track, track_info = p.is_on_track()

            status_symbol = {
                'ahead': '✓ ahead',
                'on_track': '✓ on track',
                'behind': '⚠ behind'
            }.get(track_info.get('status'), '')

            print(f"   Progress: {completion:.0f}% complete, {status_symbol}")
        elif show_progress and p.start_date:
            print(f"   Not started yet (starts {p.start_date.strftime('%Y-%m-%d')})")

        print()


def manage_plans_menu():
    """Main menu for managing multiple plans."""
    while True:
        ui_utils.display_header("Manage Multiple Plans", width=70)

        options = [
            (1, "View all plans overview"),
            (2, "Filter and sort plans"),
            (3, "Search plans"),
            (4, "Compare plans"),
            (5, "Set active plan"),
            (6, "Manage plan categories and tags"),
            (7, "Archive/Unarchive plans"),
            (8, "View plan statistics"),
        ]

        choice = ui_utils.display_menu("Manage Multiple Plans", options, show_exit=True)

        if choice == 0:
            break
        elif choice == 1:
            display_plans_overview()
            input("\nPress Enter to continue...")
        elif choice == 2:
            filter_and_sort_menu()
        elif choice == 3:
            search_plans_ui()
        elif choice == 4:
            compare_plans_ui()
        elif choice == 5:
            set_active_plan_ui()
        elif choice == 6:
            manage_tags_categories_menu()
        elif choice == 7:
            archive_unarchive_menu()
        elif choice == 8:
            display_plan_statistics()
            input("\nPress Enter to continue...")


def filter_and_sort_menu():
    """Menu for filtering and sorting plans."""
    ui_utils.display_header("Filter and Sort Plans", width=70)

    print("\n1. Filter by status")
    print("2. Filter by category")
    print("3. Filter by tag")
    print("4. Sort all plans")
    print("0. Go back")

    choice = ui_utils.get_menu_choice("\nChoice: ", 0, 4)

    if choice == 0:
        return
    elif choice == 1:
        filter_by_status_ui()
    elif choice == 2:
        filter_by_category_ui()
    elif choice == 3:
        filter_by_tag_ui()
    elif choice == 4:
        sort_plans_ui()


def filter_by_status_ui():
    """Filter plans by status."""
    ui_utils.display_header("Filter by Status", width=70)

    print("\n1. Active plans")
    print("2. Archived plans")
    print("3. Completed plans")
    print("0. Go back")

    choice = ui_utils.get_menu_choice("\nChoice: ", 0, 3)

    status_map = {
        1: "active",
        2: "archived",
        3: "completed"
    }

    if choice in status_map:
        status = status_map[choice]
        all_plans = plan_manager.get_all_plans()
        filtered = plan_manager.filter_plans_by_status(all_plans, status)

        print(f"\n{status.capitalize()} Plans ({len(filtered)}):")
        print("=" * 70)

        if filtered:
            for idx, p in enumerate(filtered, 1):
                print(f"\n{idx}. {p.name or 'Unnamed'}")
                print(f"   {p.total:,.0f} words | {p.daily:,.0f} per day | {int(p.time)} days")
                if p.category:
                    print(f"   Category: {p.category}")
                if p.start_date:
                    print(f"   Started: {p.start_date.strftime('%Y-%m-%d')}")
        else:
            print(f"\nNo {status} plans found.")

        input("\nPress Enter to continue...")


def filter_by_category_ui():
    """Filter plans by category."""
    ui_utils.display_header("Filter by Category", width=70)

    categories = plan_manager.get_all_categories()

    if not categories:
        print("\nNo categories found. All plans are uncategorized.")
        input("\nPress Enter to continue...")
        return

    print("\nAvailable categories:")
    cat_list = list(categories.items())
    for idx, (cat, count) in enumerate(cat_list, 1):
        print(f"{idx}. {cat} ({count} plans)")

    print("0. Go back")

    choice = ui_utils.get_menu_choice("\nChoice: ", 0, len(cat_list))

    if choice > 0:
        category = cat_list[choice - 1][0]
        all_plans = plan_manager.get_all_plans()
        filtered = plan_manager.filter_plans_by_category(all_plans, category)

        print(f"\nPlans in category '{category}' ({len(filtered)}):")
        print("=" * 70)

        for idx, p in enumerate(filtered, 1):
            print(f"\n{idx}. {p.name or 'Unnamed'}")
            print(f"   {p.total:,.0f} words | Status: {p.status}")

        input("\nPress Enter to continue...")


def filter_by_tag_ui():
    """Filter plans by tag."""
    ui_utils.display_header("Filter by Tag", width=70)

    all_tags = plan_manager.get_all_tags()

    if not all_tags:
        print("\nNo tags found. No plans have been tagged yet.")
        input("\nPress Enter to continue...")
        return

    print("\nAvailable tags:")
    for idx, tag in enumerate(all_tags, 1):
        print(f"{idx}. {tag}")

    print("0. Go back")

    choice = ui_utils.get_menu_choice("\nChoice: ", 0, len(all_tags))

    if choice > 0:
        tag = all_tags[choice - 1]
        all_plans = plan_manager.get_all_plans()
        filtered = plan_manager.filter_plans_by_tag(all_plans, tag)

        print(f"\nPlans with tag '{tag}' ({len(filtered)}):")
        print("=" * 70)

        for idx, p in enumerate(filtered, 1):
            print(f"\n{idx}. {p.name or 'Unnamed'}")
            print(f"   {p.total:,.0f} words | Status: {p.status}")
            if p.tags:
                print(f"   Tags: {', '.join(p.tags)}")

        input("\nPress Enter to continue...")


def sort_plans_ui():
    """Sort and display all plans."""
    ui_utils.display_header("Sort Plans", width=70)

    print("\nSort by:")
    print("1. Name (A-Z)")
    print("2. Creation date (newest first)")
    print("3. Last modified (newest first)")
    print("4. Completion percentage")
    print("5. Deadline (end date)")
    print("0. Go back")

    choice = ui_utils.get_menu_choice("\nChoice: ", 0, 5)

    sort_map = {
        1: "name",
        2: "created",
        3: "modified",
        4: "completion",
        5: "deadline"
    }

    if choice in sort_map:
        sort_by = sort_map[choice]
        all_plans = plan_manager.get_all_plans()
        sorted_plans = plan_manager.sort_plans(all_plans, sort_by=sort_by)

        print(f"\nPlans sorted by {sort_by}:")
        print("=" * 70)

        for idx, p in enumerate(sorted_plans, 1):
            print(f"\n{idx}. {p.name or 'Unnamed'}")

            if sort_by == "name":
                print(f"   {p.total:,.0f} words | Status: {p.status}")
            elif sort_by == "created":
                created = p.created_date.strftime('%Y-%m-%d') if p.created_date else "Unknown"
                print(f"   Created: {created} | {p.total:,.0f} words")
            elif sort_by == "modified":
                modified = p.last_modified.strftime('%Y-%m-%d') if p.last_modified else "Unknown"
                print(f"   Last modified: {modified} | {p.total:,.0f} words")
            elif sort_by == "completion":
                completion = p.get_completion_percentage()
                print(f"   {completion:.0f}% complete | {p.get_total_written():,.0f} / {p.total:,.0f} words")
            elif sort_by == "deadline":
                if p.start_date:
                    end_date = p.start_date + timedelta(days=int(p.time) + p.spare_days)
                    print(f"   Deadline: {end_date.strftime('%Y-%m-%d')} | {p.total:,.0f} words")
                else:
                    print(f"   No deadline set | {p.total:,.0f} words")

        input("\nPress Enter to continue...")


def search_plans_ui():
    """Search for plans."""
    ui_utils.display_header("Search Plans", width=70)

    query = ui_utils.get_string_input("\nEnter search query (or press Enter to cancel): ", allow_empty=True)

    if not query:
        return

    matching = plan_manager.search_plans(query)

    print(f"\nSearch results for '{query}' ({len(matching)} found):")
    print("=" * 70)

    if matching:
        for idx, p in enumerate(matching, 1):
            print(f"\n{idx}. {p.name or 'Unnamed'}")
            print(f"   {p.total:,.0f} words | Status: {p.status}")
            if p.category:
                print(f"   Category: {p.category}")
            if p.tags:
                print(f"   Tags: {', '.join(p.tags)}")
    else:
        print("\nNo matching plans found.")

    input("\nPress Enter to continue...")


def compare_plans_ui():
    """Compare multiple plans side by side."""
    ui_utils.display_header("Compare Plans", width=70)

    # Get all active plans
    all_plans = plan_manager.get_all_plans()

    if len(all_plans) < 2:
        print("\nYou need at least 2 plans to compare.")
        input("\nPress Enter to continue...")
        return

    print("\nSelect plans to compare (enter plan numbers separated by commas):")
    print("=" * 70)

    for idx, p in enumerate(all_plans, 1):
        status_str = f"[{p.status}]"
        print(f"{idx}. {p.name or 'Unnamed'} {status_str}")

    selection = input("\nPlan numbers (e.g., 1,2,3): ").strip()

    if not selection:
        return

    try:
        indices = [int(x.strip()) - 1 for x in selection.split(',')]
        selected_plans = [all_plans[i] for i in indices if 0 <= i < len(all_plans)]

        if len(selected_plans) < 2:
            print("\nPlease select at least 2 plans.")
            input("\nPress Enter to continue...")
            return

        # Display comparison
        _display_plans_comparison(selected_plans)

    except (ValueError, IndexError):
        print("\nInvalid selection.")

    input("\nPress Enter to continue...")


def _display_plans_comparison(plans: list):
    """Display a comparison table of plans."""
    print("\n" + "=" * 70)
    print("PLAN COMPARISON")
    print("=" * 70)

    comparison = plan_manager.compare_plans(plans)

    # Create comparison table
    table = Table(show_header=True, header_style="bold magenta", border_style="blue")

    table.add_column("Metric", style="cyan", width=20)
    for p in comparison['plans']:
        active_marker = "★ " if p['is_active'] else ""
        table.add_column(f"{active_marker}{p['name']}", width=18)

    # Add rows
    rows_data = [
        ("Total Words", [f"{p['total']:,.0f}" for p in comparison['plans']]),
        ("Daily Goal", [f"{p['daily']:,.0f}" for p in comparison['plans']]),
        ("Days", [f"{int(p['time'])}" for p in comparison['plans']]),
        ("Category", [p['category'] or "None" for p in comparison['plans']]),
        ("Status", [p['status'] for p in comparison['plans']]),
        ("Completion", [f"{p['completion']:.0f}%" for p in comparison['plans']]),
        ("Words Written", [f"{p['written']:,.0f}" for p in comparison['plans']]),
        ("Remaining", [f"{p['remaining']:,.0f}" for p in comparison['plans']]),
        ("Start Date", [p['start_date'] or "Not set" for p in comparison['plans']]),
        ("Track Status", [p['track_status'] for p in comparison['plans']]),
    ]

    for row_name, row_values in rows_data:
        table.add_row(row_name, *row_values)

    console.print(table)

    # Summary
    print("\nComparison Summary:")
    print(f"  Total plans compared: {comparison['summary']['total_plans']}")
    print(f"  Combined word goal: {comparison['summary']['total_words']:,.0f} words")
    print(f"  Combined days: {comparison['summary']['total_days']:.0f} days")
    print(f"  Average daily goal: {comparison['summary']['avg_daily']:,.0f} words/day")


def set_active_plan_ui():
    """Set a plan as the active plan."""
    ui_utils.display_header("Set Active Plan", width=70)

    all_plans = plan_manager.get_all_plans()

    if not all_plans:
        print("\nNo plans available.")
        input("\nPress Enter to continue...")
        return

    current_active = plan_manager.get_active_plan()

    print("\nSelect a plan to set as active:")
    print("=" * 70)

    for idx, p in enumerate(all_plans, 1):
        active_str = " (currently active)" if p.is_active else ""
        print(f"{idx}. {p.name or 'Unnamed'}{active_str}")

    print("0. Clear active plan")

    choice = ui_utils.get_menu_choice("\nChoice: ", 0, len(all_plans))

    if choice == 0:
        if ui_utils.get_yes_no("Clear the active plan?", default='n'):
            if plan_manager.clear_active_plan():
                ui_utils.display_success("Active plan cleared.")
            else:
                ui_utils.display_error("Failed to clear active plan.")
    else:
        selected_plan = all_plans[choice - 1]
        if selected_plan.source_file:
            if plan_manager.set_active_plan(selected_plan.source_file):
                ui_utils.display_success(f"'{selected_plan.name}' set as active plan.")
            else:
                ui_utils.display_error("Failed to set active plan.")

    input("\nPress Enter to continue...")


def manage_tags_categories_menu():
    """Menu for managing plan tags and categories."""
    ui_utils.display_header("Manage Tags and Categories", width=70)

    print("\n1. Set plan category")
    print("2. Add tags to plan")
    print("3. Remove tags from plan")
    print("4. View all tags")
    print("5. View all categories")
    print("0. Go back")

    choice = ui_utils.get_menu_choice("\nChoice: ", 0, 5)

    if choice == 0:
        return
    elif choice == 1:
        set_plan_category_ui()
    elif choice == 2:
        add_tags_ui()
    elif choice == 3:
        remove_tags_ui()
    elif choice == 4:
        view_all_tags_ui()
    elif choice == 5:
        view_all_categories_ui()


def set_plan_category_ui():
    """Set the category of a plan."""
    ui_utils.display_header("Set Plan Category", width=70)

    # Select plan
    all_plans = plan_manager.get_all_plans()

    if not all_plans:
        print("\nNo plans available.")
        input("\nPress Enter to continue...")
        return

    print("\nSelect a plan:")
    for idx, p in enumerate(all_plans, 1):
        cat_str = f" [{p.category}]" if p.category else " [No category]"
        print(f"{idx}. {p.name or 'Unnamed'}{cat_str}")

    print("0. Go back")

    plan_choice = ui_utils.get_menu_choice("\nChoice: ", 0, len(all_plans))

    if plan_choice == 0:
        return

    selected_plan = all_plans[plan_choice - 1]

    # Select category
    print("\nSelect category:")
    for idx, cat in enumerate(config.PLAN_CATEGORIES, 1):
        desc = config.PLAN_CATEGORY_DESCRIPTIONS.get(cat, "")
        print(f"{idx}. {cat} - {desc}")

    print("0. Remove category")

    cat_choice = ui_utils.get_menu_choice("\nChoice: ", 0, len(config.PLAN_CATEGORIES))

    if cat_choice == 0:
        category = None
    else:
        category = config.PLAN_CATEGORIES[cat_choice - 1]

    if plan_manager.set_plan_category(selected_plan, category):
        if category:
            ui_utils.display_success(f"Category set to '{category}'.")
        else:
            ui_utils.display_success("Category removed.")
    else:
        ui_utils.display_error("Failed to set category.")

    input("\nPress Enter to continue...")


def add_tags_ui():
    """Add tags to a plan."""
    ui_utils.display_header("Add Tags to Plan", width=70)

    # Select plan
    all_plans = plan_manager.get_all_plans()

    if not all_plans:
        print("\nNo plans available.")
        input("\nPress Enter to continue...")
        return

    print("\nSelect a plan:")
    for idx, p in enumerate(all_plans, 1):
        tags_str = f" (Tags: {', '.join(p.tags)})" if p.tags else " (No tags)"
        print(f"{idx}. {p.name or 'Unnamed'}{tags_str}")

    print("0. Go back")

    plan_choice = ui_utils.get_menu_choice("\nChoice: ", 0, len(all_plans))

    if plan_choice == 0:
        return

    selected_plan = all_plans[plan_choice - 1]

    # Enter tags
    tags_input = ui_utils.get_string_input("\nEnter tags (comma-separated): ", allow_empty=True)

    if not tags_input:
        return

    tags = [t.strip() for t in tags_input.split(',') if t.strip()]

    success_count = 0
    for tag in tags:
        if plan_manager.add_tag_to_plan(selected_plan, tag):
            success_count += 1

    if success_count > 0:
        ui_utils.display_success(f"Added {success_count} tag(s).")
    else:
        ui_utils.display_error("Failed to add tags.")

    input("\nPress Enter to continue...")


def remove_tags_ui():
    """Remove tags from a plan."""
    ui_utils.display_header("Remove Tags from Plan", width=70)

    # Select plan
    all_plans = plan_manager.get_all_plans()

    if not all_plans:
        print("\nNo plans available.")
        input("\nPress Enter to continue...")
        return

    print("\nSelect a plan:")
    for idx, p in enumerate(all_plans, 1):
        tags_str = f" (Tags: {', '.join(p.tags)})" if p.tags else " (No tags)"
        print(f"{idx}. {p.name or 'Unnamed'}{tags_str}")

    print("0. Go back")

    plan_choice = ui_utils.get_menu_choice("\nChoice: ", 0, len(all_plans))

    if plan_choice == 0:
        return

    selected_plan = all_plans[plan_choice - 1]

    if not selected_plan.tags:
        print("\nThis plan has no tags.")
        input("\nPress Enter to continue...")
        return

    # Select tags to remove
    print("\nCurrent tags:")
    for idx, tag in enumerate(selected_plan.tags, 1):
        print(f"{idx}. {tag}")

    print("0. Go back")

    tag_choice = ui_utils.get_menu_choice("\nTag to remove: ", 0, len(selected_plan.tags))

    if tag_choice == 0:
        return

    tag_to_remove = selected_plan.tags[tag_choice - 1]

    if plan_manager.remove_tag_from_plan(selected_plan, tag_to_remove):
        ui_utils.display_success(f"Tag '{tag_to_remove}' removed.")
    else:
        ui_utils.display_error("Failed to remove tag.")

    input("\nPress Enter to continue...")


def view_all_tags_ui():
    """View all tags used across plans."""
    ui_utils.display_header("All Tags", width=70)

    all_tags = plan_manager.get_all_tags()

    if not all_tags:
        print("\nNo tags found.")
    else:
        print(f"\nTotal unique tags: {len(all_tags)}")
        print("=" * 70)
        for idx, tag in enumerate(all_tags, 1):
            # Count how many plans use this tag
            plans_with_tag = plan_manager.filter_plans_by_tag(plan_manager.get_all_plans(), tag)
            print(f"{idx}. {tag} ({len(plans_with_tag)} plans)")

    input("\nPress Enter to continue...")


def view_all_categories_ui():
    """View all categories used across plans."""
    ui_utils.display_header("All Categories", width=70)

    categories = plan_manager.get_all_categories()

    if not categories:
        print("\nNo categories found.")
    else:
        print(f"\nTotal categories in use: {len(categories)}")
        print("=" * 70)
        for cat, count in sorted(categories.items()):
            desc = config.PLAN_CATEGORY_DESCRIPTIONS.get(cat, "")
            print(f"• {cat}: {count} plans")
            if desc:
                print(f"  {desc}")
            print()

    input("\nPress Enter to continue...")


def archive_unarchive_menu():
    """Menu for archiving and unarchiving plans."""
    ui_utils.display_header("Archive/Unarchive Plans", width=70)

    print("\n1. Archive a plan")
    print("2. Unarchive a plan")
    print("3. Mark plan as completed")
    print("0. Go back")

    choice = ui_utils.get_menu_choice("\nChoice: ", 0, 3)

    if choice == 0:
        return
    elif choice == 1:
        archive_plan_ui()
    elif choice == 2:
        unarchive_plan_ui()
    elif choice == 3:
        mark_completed_ui()


def archive_plan_ui():
    """Archive a plan."""
    ui_utils.display_header("Archive Plan", width=70)

    all_plans = plan_manager.get_all_plans()
    active_plans = [p for p in all_plans if p.status == "active"]

    if not active_plans:
        print("\nNo active plans to archive.")
        input("\nPress Enter to continue...")
        return

    print("\nSelect a plan to archive:")
    for idx, p in enumerate(active_plans, 1):
        print(f"{idx}. {p.name or 'Unnamed'}")

    print("0. Go back")

    choice = ui_utils.get_menu_choice("\nChoice: ", 0, len(active_plans))

    if choice == 0:
        return

    selected_plan = active_plans[choice - 1]

    if ui_utils.get_yes_no(f"Archive '{selected_plan.name}'?", default='n'):
        if plan_manager.archive_plan(selected_plan):
            ui_utils.display_success(f"'{selected_plan.name}' archived.")
        else:
            ui_utils.display_error("Failed to archive plan.")

    input("\nPress Enter to continue...")


def unarchive_plan_ui():
    """Unarchive a plan."""
    ui_utils.display_header("Unarchive Plan", width=70)

    all_plans = plan_manager.get_all_plans()
    archived_plans = [p for p in all_plans if p.status == "archived"]

    if not archived_plans:
        print("\nNo archived plans to unarchive.")
        input("\nPress Enter to continue...")
        return

    print("\nSelect a plan to unarchive:")
    for idx, p in enumerate(archived_plans, 1):
        print(f"{idx}. {p.name or 'Unnamed'}")

    print("0. Go back")

    choice = ui_utils.get_menu_choice("\nChoice: ", 0, len(archived_plans))

    if choice == 0:
        return

    selected_plan = archived_plans[choice - 1]

    if ui_utils.get_yes_no(f"Unarchive '{selected_plan.name}'?", default='n'):
        if plan_manager.unarchive_plan(selected_plan):
            ui_utils.display_success(f"'{selected_plan.name}' unarchived.")
        else:
            ui_utils.display_error("Failed to unarchive plan.")

    input("\nPress Enter to continue...")


def mark_completed_ui():
    """Mark a plan as completed."""
    ui_utils.display_header("Mark Plan as Completed", width=70)

    all_plans = plan_manager.get_all_plans()
    non_completed = [p for p in all_plans if p.status != "completed"]

    if not non_completed:
        print("\nAll plans are already completed.")
        input("\nPress Enter to continue...")
        return

    print("\nSelect a plan to mark as completed:")
    for idx, p in enumerate(non_completed, 1):
        completion = p.get_completion_percentage()
        print(f"{idx}. {p.name or 'Unnamed'} ({completion:.0f}% complete)")

    print("0. Go back")

    choice = ui_utils.get_menu_choice("\nChoice: ", 0, len(non_completed))

    if choice == 0:
        return

    selected_plan = non_completed[choice - 1]

    if ui_utils.get_yes_no(f"Mark '{selected_plan.name}' as completed?", default='n'):
        if plan_manager.mark_plan_completed(selected_plan):
            ui_utils.display_success(f"'{selected_plan.name}' marked as completed!")
        else:
            ui_utils.display_error("Failed to mark plan as completed.")

    input("\nPress Enter to continue...")


def display_plan_statistics():
    """Display overall statistics across all plans."""
    ui_utils.display_header("Plan Statistics", width=70)

    stats = plan_manager.get_plan_statistics()

    print("\nOverall Statistics:")
    print("=" * 70)
    print(f"Total Plans: {stats['total_plans']}")
    print(f"  • Active: {stats['active_plans']}")
    print(f"  • Archived: {stats['archived_plans']}")
    print(f"  • Completed: {stats['completed_plans']}")
    print()
    print(f"Writing Goals:")
    print(f"  • Total word goal: {stats['total_word_goal']:,} words")
    print(f"  • Total words written: {stats['total_words_written']:,} words")
    print(f"  • Plans with progress: {stats['plans_with_progress']}")
    if stats['active_plans'] > 0:
        print(f"  • Avg completion (active): {stats['avg_completion']:.0f}%")

    if stats['categories']:
        print(f"\nCategories in use:")
        for cat, count in sorted(stats['categories'].items()):
            print(f"  • {cat}: {count} plans")

    if stats['tags']:
        print(f"\nTags in use ({len(stats['tags'])}):")
        print(f"  {', '.join(stats['tags'])}")

    if stats['active_plan']:
        print(f"\nCurrently Active Plan:")
        print(f"  ★ {stats['active_plan'].name}")
