"""
The plan actions menu: results, calendar, and leaving a plan.

Split out of planea.py (issues-program.org Q3).
"""

import plan
import calendar_view
import progress_analytics
from ui_utils import (
    get_menu_choice,
    display_header,
    display_section,
    display_success,
    display_warning,
)
import ui_files
import ui_modify
import ui_progress


def display_results(newplan):
    """Display the plan results in a formatted way."""
    display_section("YOUR WRITING PLAN")
    print(f"Total words: {newplan.total:,.0f} words")
    if newplan.preexisting_words:
        print(f"Already written before the plan: {newplan.preexisting_words:,.0f} words")
    print(f"Writing days: {newplan.time:.0f} days")
    print(f"Daily goal: {newplan.daily:,.0f} words per day")

    # Show weekend configuration
    if newplan.weekend_mode != "same":
        if newplan.weekend_mode == "different":
            day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            weekend_names = [day_names[d] for d in newplan.weekend_days]
            print(f"Weekend goal: {newplan.weekend_daily:,.0f} words/day ({', '.join(weekend_names)})")
        elif newplan.weekend_mode == "spare":
            print(f"Weekends: All marked as spare days")

    # Show custom day goals if any
    if newplan.custom_daily_goals:
        print(f"Custom day goals: {len(newplan.custom_daily_goals)} day(s) customized")

    if newplan.spare_days > 0:
        print(f"Spare days: {newplan.spare_days:.0f} days (0 words)")
        total_calendar_days = newplan.time + newplan.spare_days
        print(f"Total calendar duration: {total_calendar_days:.0f} days")

    # Show progress information if available
    if newplan.progress:
        print("-" * 50)
        total_written = newplan.get_total_written()
        completion = newplan.get_completion_percentage()
        remaining = newplan.get_remaining_words()

        print(f"Progress: {total_written:,.0f} words written ({completion:.1f}%)")
        print(f"Remaining: {remaining:,.0f} words")

        # Show on-track status if start date is set
        if newplan.start_date:
            on_track, info = newplan.is_on_track()
            if info.get('status'):
                if info['status'] == 'ahead':
                    print(f"Status: ✓ AHEAD by {info['difference']:,.0f} words")
                elif info['status'] == 'on_track':
                    print(f"Status: ✓ ON TRACK")
                else:
                    print(f"Status: ⚠ BEHIND by {abs(info['difference']):,.0f} words")

    print("-" * 50)


def plan_actions_menu():
    """Display plan actions menu after creating or loading a plan."""
    display_header("PLAN ACTIONS")
    print("\nWhat would you like to do with this plan?")
    print("\n1. Update progress")
    print("2. View progress summary")
    print("3. View progress graphs & analytics")
    print("4. Modify plan")
    print("5. View calendar")
    print("6. Export plan")
    print("7. Save plan")
    print("0. Go back to main menu")
    print("=" * 50)

    return get_menu_choice("\nEnter your choice (0-7): ", 0, 7)


def show_calendar_options(newplan):
    """Ask user if they want to see calendar views."""
    print("\n" + "=" * 50)
    print("CALENDAR VIEWS")
    print("=" * 50)
    print("\nWould you like to see your plan as a calendar?")
    print("\n1. Monthly calendar view (day-by-day breakdown)")
    print("2. Weekly summary view")
    print("3. Both views")
    print("0. Skip calendar view")
    print("=" * 50)

    choice = get_menu_choice("\nEnter your choice (0-3): ", 0, 3)
    if choice == 0:
        return

    # Get start date
    if newplan.start_date:
        # Plan has a saved start date - use it directly
        start_date = newplan.start_date
    else:
        # No saved start date - this shouldn't happen for new plans,
        # but if it does, use today
        display_warning("No start date set. Using today's date.")
        start_date = plan.today()
        newplan.start_date = start_date

    # Display chosen views
    if choice == 1 or choice == 3:
        calendar_view.display_calendar_view(newplan, start_date)

    if choice == 2 or choice == 3:
        calendar_view.display_weekly_summary(newplan, start_date)


# The plan shown by handle_plan_actions, so an interrupt can offer to save it
_open_plan = None


def confirm_leave_plan(current_plan):
    """
    Before going back to the main menu, offer to save unsaved changes.

    Returns:
        True to leave, False to stay in the plan
    """
    if not current_plan.has_unsaved_changes():
        return True

    print("\nThis plan has unsaved changes.")
    print("1. Save and go back")
    print("2. Go back without saving (the changes are lost)")
    print("0. Stay in this plan")
    choice = get_menu_choice("\nEnter your choice (0-2): ", 0, 2)
    if choice == 1:
        return ui_files.save_plan_prompt(current_plan, ask=False)
    return choice == 2


def handle_plan_actions(current_plan):
    """Handle the plan actions menu loop."""
    global _open_plan
    _open_plan = current_plan
    while True:
        # Every modification starts from this menu: freeze days that are now past
        # and keep the displayed daily goal in line with the schedule
        current_plan.lock_past_goals()
        current_plan.sync_daily()
        display_results(current_plan)
        action = plan_actions_menu()

        if action == 0:
            # Go back to main menu
            if confirm_leave_plan(current_plan):
                _open_plan = None
                break

        elif action == 1:
            # Update progress
            ui_progress.update_progress(current_plan)

        elif action == 2:
            # View progress summary
            ui_progress.view_progress_summary(current_plan)

        elif action == 3:
            # View progress graphs & analytics
            progress_analytics.show_analytics_menu(current_plan)

        elif action == 4:
            # Modify plan; only say so if something really changed
            fingerprint = current_plan.fingerprint()
            ui_modify.modify_plan(current_plan)
            if current_plan.fingerprint() != fingerprint:
                display_success("Plan modified successfully!")
            # Loop continues to show updated results

        elif action == 5:
            # View calendar
            show_calendar_options(current_plan)

        elif action == 6:
            # Export plan
            ui_files.export_plan_menu(current_plan)

        elif action == 7:
            # Save plan
            ui_files.save_plan_prompt(current_plan)
