#!/usr/bin/python3

"""This is an intended clone for the pacemaker.press site.
It intends to get a plan for daily work on words per day."""

import copy
from datetime import datetime, timedelta
import readline
from pathlib import Path
import plan
import calendar_view
import plan_storage
import plan_export
import progress_analytics
import plan_templates
import config
import user_preferences
from ui_utils import (
    get_yes_no, get_positive_number, get_date_input, get_menu_choice,
    display_header, display_section, display_success, display_error, display_warning
)
from pattern_utils import choose_writing_pattern, get_pattern_description


# Validation and input functions are now imported from ui_utils module
# (get_yes_no, get_positive_number, get_date_input)


def initial_menu():
    """Display the initial menu: create new plan or load existing."""
    display_header("WORD COUNT PLANNER")
    print("\nWhat would you like to do?")
    print("\n1. Create a new plan from scratch")
    print("2. Create plan from template")
    print("3. Load an existing plan")
    print("4. Manage multiple plans")
    print("5. Settings")
    print("0. Exit")
    print("=" * 50)

    return get_menu_choice("\nEnter your choice (0-5): ", 0, 5)


# choose_writing_pattern is now imported from pattern_utils module


def choose_calculation_method():
    """Display calculation method menu and return user choice."""
    display_header("CALCULATION METHOD")
    print("\nWhat do you know about your writing project?")
    print("\n1. I know my goal (total words) and daily capacity")
    print("   → Calculate how many days I'll need")
    print("\n2. I know my daily capacity and available time")
    print("   → Calculate total words I'll write")
    print("\n3. I know my goal (total words) and available time")
    print("   → Calculate daily words I need to write")
    print("\n0. Go back")
    print("=" * 50)

    return get_menu_choice("\nEnter your choice (0-3): ", 0, 3)


def display_results(newplan):
    """Display the plan results in a formatted way."""
    display_section("YOUR WRITING PLAN")
    print(f"Total words: {newplan.total:,.0f} words")
    if newplan.preexisting_words:
        print(f"Already written before the plan: {newplan.preexisting_words:,} words")
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

        print(f"Progress: {total_written:,} words written ({completion:.1f}%)")
        print(f"Remaining: {remaining:,} words")

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


def save_plan_prompt(newplan, ask=True):
    """
    Save the plan, asking where (overwrite or new file) and for a name if needed.

    Args:
        newplan: The plan to save
        ask: First ask whether to save at all (False when the caller already asked)

    Returns:
        True if the plan was saved
    """
    if not ask or get_yes_no("\nWould you like to save this plan?", default='y'):
        # Check if this plan was loaded from a file
        if newplan.source_file:
            print(f"\nThis plan was loaded from: {newplan.source_file.name}")
            print("\nHow would you like to save?")
            print("1. Overwrite the original file")
            print("2. Save as a new file (with timestamp)")
            print("0. Cancel")

            while True:
                try:
                    choice = int(input("\nEnter your choice (0-2): "))
                    if choice == 0:
                        return False
                    elif choice in [1, 2]:
                        overwrite = (choice == 1)

                        # If saving as new, optionally allow name change
                        if not overwrite:
                            if newplan.name:
                                print(f"\nCurrent plan name: {newplan.name}")
                                if not get_yes_no("Keep this name?", default='y'):
                                    plan_name = input("Enter a new name for this plan: ").strip()
                                    if plan_name:
                                        newplan.name = plan_name

                        try:
                            filepath = plan_storage.save_plan(newplan, overwrite_source=overwrite)
                            if overwrite:
                                display_success(f"Plan updated successfully in: {filepath}")
                            else:
                                display_success(f"Plan saved as new file: {filepath}")
                            return True
                        except Exception as e:
                            display_error(f"Error saving plan: {e}")
                            return False
                    else:
                        print("Please enter 0, 1, or 2.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
        else:
            # New plan - ask for name
            if newplan.name:
                print(f"\nCurrent plan name: {newplan.name}")
                if get_yes_no("Keep this name?", default='y'):
                    plan_name = newplan.name
                else:
                    plan_name = input("Enter a new name for this plan: ").strip()
            else:
                plan_name = input("Enter a name for this plan: ").strip()

            if not plan_name:
                print("No name provided, plan not saved.")
                return False

            try:
                newplan.name = plan_name
                filepath = plan_storage.save_plan(newplan, overwrite_source=False)
                display_success(f"Plan saved successfully to: {filepath}")
                return True
            except Exception as e:
                display_error(f"Error saving plan: {e}")
                return False
    return False


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


def today_midnight():
    """Today's date at midnight, the boundary between locked and open days."""
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


LOCKED_DAYS_MESSAGE = "Days before today are locked: their goals can't change."


def mark_weekdays_as_spare(current_plan, weekdays):
    """
    Mark every day of the given weekdays (Mon=0) inside the plan as spare.

    Each spare day pushes the end date out by one day, so the window is
    re-evaluated as days are added; days after the final end date are left alone.
    Days before today are locked and never marked.

    Returns:
        Number of spare days added
    """
    added_count = 0
    current = max(current_plan.start_date, today_midnight())
    while current <= current_plan.end_date:
        if current.weekday() in weekdays and not current_plan.is_spare_day(current):
            current_plan.spare_days_dates.append(current)
            added_count += 1
        current += timedelta(days=1)
    return added_count


def rebalance_after_writing_days_change(current_plan, before, drop_after_end=()):
    """
    Ask how the plan absorbs writing days that were added or removed (decision 1).

    Called after spare days or the weekend mode changed. Each option is
    previewed on a copy of the plan and only the chosen one is applied:
    - 'move_end': keep the daily goal and the total, move the end date;
    - 'keep_end': keep the end date and the total, change the daily goal;
    - 'change_total': keep the end date and the daily goal, change the total.

    Args:
        current_plan: The plan, already changed
        before: A copy of the plan taken before the change
        drop_after_end: Spare days just added that are dropped when the end date
            is kept and they fall after it (quick actions mark days up to the
            end date, which only grows if the end date moves)

    Returns:
        The chosen option, or None if the change didn't affect the plan
    """
    old_end = before.end_date
    if not current_plan.start_date or old_end is None:
        return None
    if current_plan.build_schedule()['goals'] == before.build_schedule()['goals']:
        return None

    old_total = before.total
    old_daily = before.daily

    def drop_spare_days_after_end(p):
        p.spare_days_dates = [d for d in p.spare_days_dates
                              if not (d > old_end and d in drop_after_end)]

    def move_end(p):
        p.total = old_total
        p.daily = old_daily
        p.calculate_time()

    def keep_end(p):
        drop_spare_days_after_end(p)
        p.total = old_total
        p.keep_end_date(old_end)

    def change_total(p):
        drop_spare_days_after_end(p)
        p.keep_end_date(old_end)
        p.total = p.total_for_daily(old_daily)
        p.sync_daily()

    options = []
    if old_daily > 0:
        options.append(('move_end', f"Move the end date (keep {old_daily:,.0f} words/day)", move_end))
    options.append(('keep_end', f"Keep the end date (change the daily goal)", keep_end))
    options.append(('change_total', "Keep the end date and the daily goal (change the total)", change_total))

    def outcome(p):
        end = p.end_date.strftime('%Y-%m-%d') if p.end_date else "-"
        return f"ends {end}, {p.daily:,.0f} words/day, total {p.total:,.0f} words"

    print("\nThis changes the plan's writing days. How should the plan adjust?")
    print(f"   Before: {outcome(before)}")
    for number, (_, label, apply) in enumerate(options, 1):
        preview = copy.deepcopy(current_plan)
        apply(preview)
        print(f"{number}. {label}")
        print(f"   -> {outcome(preview)}")

    while True:
        try:
            choice = int(input(f"\nEnter your choice (1-{len(options)}): "))
            if 1 <= choice <= len(options):
                break
            print(f"Please enter a number between 1 and {len(options)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    key, _, apply = options[choice - 1]
    apply(current_plan)
    display_success(f"Plan {outcome(current_plan)}")
    return key


def manage_spare_days(current_plan):
    """Interactively manage spare days for the plan."""
    dt = datetime  # Alias for strptime usage

    # Check if start_date is set
    if not current_plan.start_date:
        display_error("You must set a start date before managing spare days.")
        print("  Please view a calendar first to set a start date.")
        return False

    while True:
        plan_end_date = current_plan.end_date or current_plan.start_date
        print("\n" + "=" * 50)
        print("MANAGE SPARE DAYS")
        print("=" * 50)
        print("\nSpare days are days with 0 words (holidays, urgent matters, etc.)")
        print(f"Plan period: {current_plan.start_date.strftime('%Y-%m-%d')} to {plan_end_date.strftime('%Y-%m-%d')}")
        print(f"Writing days: {current_plan.time:.0f}")
        print(f"Spare days: {current_plan.spare_days}")

        if current_plan.spare_days_dates:
            print("\nCurrent spare days:")

            # Filter out any old integer-based spare days and convert if possible
            valid_spare_dates = []
            old_format_count = 0

            for spare_item in current_plan.spare_days_dates:
                if isinstance(spare_item, int):
                    # Old format (day number) - skip or convert if we have start_date
                    old_format_count += 1
                    if current_plan.start_date:
                        # Convert old day number to actual date
                        converted_date = current_plan.start_date + timedelta(days=spare_item - 1)
                        valid_spare_dates.append(converted_date)
                else:
                    # New format (datetime object)
                    valid_spare_dates.append(spare_item)

            # Update the list with converted dates
            if old_format_count > 0:
                current_plan.spare_days_dates = valid_spare_dates
                print(f"  (Converted {old_format_count} spare days from old format)")

            sorted_spare = sorted(valid_spare_dates)
            for spare_date in sorted_spare:
                outside = spare_date < current_plan.start_date or spare_date > plan_end_date
                note = "  (outside the plan, ignored)" if outside else ""
                print(f"  {spare_date.strftime('%Y-%m-%d (%A)')}{note}")

        print("\nOptions:")
        print("1. Add spare day(s)")
        print("2. Remove spare day(s)")
        print("3. Clear all spare days")
        print("\nQuick Actions:")
        print("4. Mark all Saturdays as spare")
        print("5. Mark all Sundays as spare")
        print("6. Mark all weekends as spare")
        print("0. Done")
        print("=" * 50)

        before = copy.deepcopy(current_plan)
        try:
            choice = int(input("\nEnter your choice (0-6): "))

            if choice == 0:
                return len(current_plan.spare_days_dates) > 0  # Return True if modified

            elif choice == 1:
                # Add spare days by date
                print("\nEnter dates to mark as spare days:")
                print("  Format: YYYY-MM-DD (e.g., 2025-12-25)")
                print("  Multiple dates: separated by commas (e.g., 2025-12-25,2025-12-26)")
                print("  Date range: use 'to' (e.g., 2025-12-24 to 2025-12-26)")
                print(f"  Valid range: {current_plan.start_date.strftime('%Y-%m-%d')} to ~1 year later")

                dates_input = input("Date(s): ").strip()

                if not dates_input:
                    continue

                try:
                    new_spare_dates = []

                    # Check if it's a range (contains 'to')
                    if ' to ' in dates_input.lower():
                        # Date range
                        parts = dates_input.lower().split(' to ')
                        if len(parts) == 2:
                            start_str = parts[0].strip()
                            end_str = parts[1].strip()

                            start_date = dt.strptime(start_str, "%Y-%m-%d")
                            end_date = dt.strptime(end_str, "%Y-%m-%d")

                            if start_date > end_date:
                                start_date, end_date = end_date, start_date

                            # Generate all dates in range
                            current = start_date
                            while current <= end_date:
                                new_spare_dates.append(current)
                                current += timedelta(days=1)
                        else:
                            display_error("Invalid range format. Use: YYYY-MM-DD to YYYY-MM-DD")
                            continue
                    else:
                        # Comma-separated dates
                        date_strings = [d.strip() for d in dates_input.split(',')]
                        for date_str in date_strings:
                            if date_str:
                                new_spare_dates.append(dt.strptime(date_str, "%Y-%m-%d"))

                    # Validate dates are reasonable (within plan period + 1 year buffer)
                    max_allowed_date = current_plan.start_date + timedelta(days=365 + current_plan.time)
                    min_allowed_date = current_plan.start_date

                    invalid_dates = []
                    for d in new_spare_dates:
                        if d < min_allowed_date or d > max_allowed_date:
                            invalid_dates.append(d.strftime('%Y-%m-%d'))

                    if invalid_dates:
                        display_error(f"Some dates are outside the valid range:")
                        for d in invalid_dates[:5]:  # Show first 5
                            print(f"  {d}")
                        if len(invalid_dates) > 5:
                            print(f"  ... and {len(invalid_dates) - 5} more")
                        continue

                    if any(d < today_midnight() for d in new_spare_dates):
                        display_error(LOCKED_DAYS_MESSAGE)
                        continue

                    # Add to spare days (avoid duplicates)
                    added_count = 0
                    for new_date in new_spare_dates:
                        # Check if already in spare days
                        is_duplicate = False
                        for existing in current_plan.spare_days_dates:
                            if new_date.date() == existing.date():
                                is_duplicate = True
                                break

                        if not is_duplicate:
                            current_plan.spare_days_dates.append(new_date)
                            added_count += 1


                    display_success(f"Added {added_count} spare day(s)")
                    if added_count < len(new_spare_dates):
                        print(f"  ({len(new_spare_dates) - added_count} were already marked as spare)")
                    rebalance_after_writing_days_change(current_plan, before)

                except ValueError as e:
                    display_error(f"Invalid date format: {e}")
                    print("  Please use YYYY-MM-DD format (e.g., 2025-12-25)")

            elif choice == 2:
                # Remove spare days by date
                if not current_plan.spare_days_dates:
                    display_error("No spare days to remove")
                    continue

                print("\nEnter dates to remove from spare days:")
                print("  Format: YYYY-MM-DD or comma-separated dates")
                print("  Or use range: YYYY-MM-DD to YYYY-MM-DD")

                dates_input = input("Date(s): ").strip()

                if not dates_input:
                    continue

                try:
                    dates_to_remove = []

                    # Check if it's a range
                    if ' to ' in dates_input.lower():
                        parts = dates_input.lower().split(' to ')
                        if len(parts) == 2:
                            start_date = dt.strptime(parts[0].strip(), "%Y-%m-%d")
                            end_date = dt.strptime(parts[1].strip(), "%Y-%m-%d")

                            if start_date > end_date:
                                start_date, end_date = end_date, start_date

                            current = start_date
                            while current <= end_date:
                                dates_to_remove.append(current)
                                current += timedelta(days=1)
                    else:
                        # Comma-separated
                        date_strings = [d.strip() for d in dates_input.split(',')]
                        for date_str in date_strings:
                            if date_str:
                                dates_to_remove.append(dt.strptime(date_str, "%Y-%m-%d"))

                    if any(d < today_midnight() for d in dates_to_remove):
                        display_error(LOCKED_DAYS_MESSAGE)
                        continue

                    # Remove from spare days
                    removed_count = 0
                    for remove_date in dates_to_remove:
                        for i, spare_date in enumerate(current_plan.spare_days_dates[:]):
                            if remove_date.date() == spare_date.date():
                                current_plan.spare_days_dates.remove(spare_date)
                                removed_count += 1
                                break


                    display_success(f"Removed {removed_count} spare day(s)")
                    if removed_count < len(dates_to_remove):
                        print(f"  ({len(dates_to_remove) - removed_count} were not spare days)")
                    rebalance_after_writing_days_change(current_plan, before)

                except ValueError as e:
                    display_error(f"Invalid date format: {e}")

            elif choice == 3:
                # Clear all spare days from today on (past ones are locked)
                today = today_midnight()
                clearable = [d for d in current_plan.spare_days_dates if d >= today]
                if not clearable:
                    display_error("No spare days from today on to clear")
                    continue

                if get_yes_no(f"Clear all {len(clearable)} spare days from today on?", default='n'):
                    current_plan.spare_days_dates = [d for d in current_plan.spare_days_dates if d < today]
                    display_success("Spare days from today on cleared")
                    rebalance_after_writing_days_change(current_plan, before)

            elif choice in (4, 5, 6):
                weekdays, label = {
                    4: ([5], "Saturdays"),
                    5: ([6], "Sundays"),
                    6: (current_plan.weekend_days, "weekend days"),
                }[choice]
                mark_weekdays_as_spare(current_plan, weekdays)
                added = [d for d in current_plan.spare_days_dates if d not in before.spare_days_dates]
                rebalance_after_writing_days_change(current_plan, before, drop_after_end=added)
                added_count = sum(1 for d in added if d in current_plan.spare_days_dates)
                display_success(f"Marked {added_count} {label} as spare days")

            else:
                print("Please enter a number between 0 and 6.")

        except ValueError:
            print("Invalid input. Please enter a number.")


def ask_recalculation_preference():
    """
    Ask user what they want to keep constant after changing daily goals.

    Returns:
        str: 'total' to keep total words constant, 'days' to keep days constant
    """
    print("\nHow would you like to adjust the plan?")
    print("1. Keep total word count constant (adjust other days' goals)")
    print("2. Keep days constant (adjust total word count)")

    while True:
        try:
            choice = int(input("\nEnter your choice (1-2): "))
            if choice == 1:
                return 'total'
            elif choice == 2:
                return 'days'
            else:
                print("Please enter 1 or 2.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def recalculate_plan_with_choice(current_plan, old_total, choice_mode, old_daily=None):
    """
    Rebalance the plan after a change (custom goal, weekend settings), as the user chose.

    Args:
        current_plan: The Plan object to recalculate
        old_total: The total before changes
        choice_mode: 'total' to keep the total (open days absorb the change),
            'days' to keep the daily goal of open days (the total changes)
        old_daily: The daily goal before changes (default: current_plan.daily,
            which callers haven't synced yet)
    """
    if old_daily is None:
        old_daily = current_plan.daily

    if choice_mode == 'days':
        # Keep open days at the old daily goal, adjust total
        new_total = current_plan.total_for_daily(old_daily)
        current_plan.total = new_total
        current_plan.sync_daily()
        if abs(new_total - old_total) > 0.01:
            print(f"\nPlan total adjusted: {old_total:,.0f} -> {new_total:,.0f} words")

    elif choice_mode == 'total':
        # Keep total constant; the schedule spreads the difference over open days
        current_plan.total = old_total
        schedule = current_plan.build_schedule()

        if schedule['adjustable_weight'] == 0:
            new_total = current_plan.total_for_daily(0)
            print("\nWarning: No adjustable days remaining!")
            print("All days are past, have custom goals, weekend settings, or are spare days.")
            print(f"Total will be: {new_total:,.0f} words")
            current_plan.total = new_total
            return

        current_plan.sync_daily()
        new_daily = current_plan.daily
        if abs(new_daily - old_daily) < 0.01:
            print("\nNo adjustment needed - total remains the same")
            return

        print(f"\nAdjusting {schedule['adjustable_days']} days to maintain total of {old_total:,.0f} words")
        print(f"  Base daily goal: {old_daily:,.0f} -> {new_daily:,.0f} words/day")
        print(f"  Change: {new_daily - old_daily:+.0f} words/day")


def edit_individual_day_goal(current_plan):
    """Edit the word goal for a specific day."""
    dt = datetime  # Alias for strptime usage

    if not current_plan.start_date:
        display_error("You must set a start date before editing individual day goals.")
        return False

    print("\n" + "=" * 50)
    print("EDIT INDIVIDUAL DAY GOAL")
    print("=" * 50)
    print("\nThis allows you to set a custom word goal for a specific date.")
    print("This overrides pattern-based goals and weekend settings for that day.")

    plan_end_date = current_plan.end_date or current_plan.start_date
    print(f"\nPlan period: {current_plan.start_date.strftime('%Y-%m-%d')} to {plan_end_date.strftime('%Y-%m-%d')}")

    if current_plan.custom_daily_goals:
        print(f"\nCurrent custom goals ({len(current_plan.custom_daily_goals)}):")
        for date_key, word_count in sorted(current_plan.custom_daily_goals.items()):
            date_obj = dt.strptime(date_key, '%Y-%m-%d')
            print(f"  {date_obj.strftime('%Y-%m-%d (%A)')}: {word_count:,.0f} words")

    print("\nOptions:")
    print("1. Set custom goal for a specific day")
    print("2. Remove custom goal (revert to pattern/default)")
    print("3. Clear all custom day goals")
    print("0. Done")
    print("=" * 50)

    while True:
        try:
            choice = int(input("\nEnter your choice (0-3): "))

            if choice == 0:
                return len(current_plan.custom_daily_goals) > 0

            elif choice == 1:
                # Set custom goal
                print("\nEnter date to customize:")
                date_input = input("Date (YYYY-MM-DD): ").strip()

                if not date_input:
                    continue

                try:
                    target_date = dt.strptime(date_input, "%Y-%m-%d")

                    if target_date < today_midnight():
                        display_error(LOCKED_DAYS_MESSAGE)
                        continue

                    # Show current goal for this day
                    current_goal = current_plan.get_daily_goal(date=target_date)
                    print(f"\nCurrent goal for {target_date.strftime('%A, %Y-%m-%d')}: {current_goal:,.0f} words")

                    if current_plan.is_spare_day(target_date):
                        print("  (This is currently a spare day)")

                    # Get new goal
                    print("\nEnter new word goal for this day:")
                    print("  (Enter 0 to make it a rest day, or any positive number)")
                    new_goal = get_positive_number("New goal: ")

                    old_total = current_plan.total
                    current_plan.set_custom_daily_goal(target_date, new_goal)

                    display_success(f"Set custom goal of {new_goal:,.0f} words for {target_date.strftime('%Y-%m-%d')}")

                    # Ask user how to adjust the plan
                    choice = ask_recalculation_preference()
                    recalculate_plan_with_choice(current_plan, old_total, choice)

                except ValueError as e:
                    display_error(f"Invalid date format: {e}")
                    print("  Please use YYYY-MM-DD format")

            elif choice == 2:
                # Remove custom goal
                if not current_plan.custom_daily_goals:
                    display_error("No custom day goals to remove")
                    continue

                print("\nEnter date to remove custom goal:")
                date_input = input("Date (YYYY-MM-DD): ").strip()

                if not date_input:
                    continue

                try:
                    target_date = dt.strptime(date_input, "%Y-%m-%d")
                    date_key = target_date.strftime('%Y-%m-%d')

                    if target_date < today_midnight():
                        display_error(LOCKED_DAYS_MESSAGE)
                        continue

                    if date_key in current_plan.custom_daily_goals:
                        old_total = current_plan.total
                        current_plan.remove_custom_daily_goal(target_date)

                        display_success(f"Removed custom goal for {target_date.strftime('%Y-%m-%d')}")

                        # Show what the goal will revert to (before recalculation)
                        reverted_goal = current_plan.get_daily_goal(date=target_date)
                        print(f"  Goal reverted to: {reverted_goal:,.0f} words")

                        # Ask user how to adjust the plan
                        choice = ask_recalculation_preference()
                        recalculate_plan_with_choice(current_plan, old_total, choice)
                    else:
                        display_error(f"No custom goal found for {target_date.strftime('%Y-%m-%d')}")

                except ValueError as e:
                    display_error(f"Invalid date format: {e}")

            elif choice == 3:
                # Clear all custom goals
                if not current_plan.custom_daily_goals:
                    display_error("No custom day goals to clear")
                    continue

                if get_yes_no(f"Clear all {len(current_plan.custom_daily_goals)} custom day goals?", default='n'):
                    old_total = current_plan.total
                    current_plan.custom_daily_goals.clear()
                    current_plan.invalidate_daily_goals_cache()

                    display_success("All custom day goals cleared")

                    # Ask user how to adjust the plan
                    choice = ask_recalculation_preference()
                    recalculate_plan_with_choice(current_plan, old_total, choice)

            else:
                print("Please enter a number between 0 and 3.")

        except ValueError:
            print("Invalid input. Please enter a number.")


def recalculate_plan_from_progress(current_plan):
    """
    Recalculate plan based on actual progress, redistributing remaining words
    across remaining days while keeping the end date fixed.
    """
    print("\n" + "=" * 50)
    print("RECALCULATE FROM PROGRESS")
    print("=" * 50)

    # Check if plan has a start date
    if not current_plan.start_date:
        display_error("This plan doesn't have a start date set.")
        print("  You need a start date to recalculate from progress.")
        input("\nPress Enter to continue...")
        return False

    # Check if there's any progress recorded
    if not current_plan.progress or len(current_plan.progress) == 0:
        display_error("No progress has been recorded yet.")
        print("  Record some progress first, then you can recalculate.")
        input("\nPress Enter to continue...")
        return False

    # Show current status
    words_completed = current_plan.get_total_written()
    words_remaining = current_plan.total - words_completed
    completion_pct = current_plan.get_completion_percentage()

    print("\nCurrent Progress:")
    print(f"  Total goal: {current_plan.total:,.0f} words")
    print(f"  Words completed: {words_completed:,.0f} words ({completion_pct:.1f}%)")
    print(f"  Words remaining: {words_remaining:,.0f} words")
    print(f"  Current daily target: {current_plan.daily:,.0f} words")

    if current_plan.start_date:
        end_date = current_plan.end_date or current_plan.start_date
        print(f"  Plan end date: {end_date.strftime('%Y-%m-%d')} (fixed)")

    print("\nThis will:")
    print("  • Spread the words actually left over the remaining writing days")
    print("  • Keep your end date fixed")
    print("  • Keep past daily goals (they are locked)")
    print("  • Keep your writing pattern and future custom day goals")
    if current_plan.weekend_mode == 'different':
        print("  • Keep the weekend goal in the same proportion to the weekday goal")
    print("  • Start today, or tomorrow if you have already logged words today")

    applied = offer_daily_recalculation(current_plan)
    input("\nPress Enter to continue...")
    return applied


def print_recalculation_failure(result):
    """Explain why recalculate_from_progress() could not run."""
    if result is None:
        display_error("Could not recalculate: Plan has no start date.")
        return

    reason = result.get('reason')
    if reason == 'goal_already_met':
        display_success("Congratulations! You've already met your goal!")
        print(f"  Total words completed: {result['words_completed']:,.0f}")
    elif reason == 'past_end_date':
        display_error("Cannot recalculate: Plan end date has already passed.")
        print(f"  End date was: {result['end_date'].strftime('%Y-%m-%d')}")
        print(f"  Words remaining: {result['words_remaining']:,.0f}")
    elif reason == 'no_remaining_days':
        display_error("Cannot recalculate: No remaining writing days.")
        print(f"  Words remaining: {result['words_remaining']:,.0f}")
    else:
        display_error(f"Recalculation failed: {reason}")


def print_recalculation_summary(result):
    """Show what recalculate_from_progress() changes (or would change)."""
    print(f"  Changes from: {result['as_of_date'].strftime('%Y-%m-%d')}")
    print(f"  Words remaining: {result['words_remaining']:,.0f}")
    print(f"  Remaining writing days: {result['remaining_writing_days']}")
    print(f"  Daily target: {result['old_daily']:,.0f} -> {result['new_daily']:,.0f} words")

    daily_change = result['new_daily'] - result['old_daily']
    if result['old_daily'] > 0 and abs(daily_change) >= 0.5:
        direction = "increase" if daily_change > 0 else "reduction"
        print(f"  Daily {direction}: {abs(daily_change):,.0f} words ({abs(daily_change) / result['old_daily'] * 100:.1f}%)")

    if result['pattern'] != 'flat':
        print(f"  Pattern kept: {result['pattern']}")
    if result['kept_custom_goals'] > 0:
        print(f"  Custom day goals kept: {result['kept_custom_goals']}")
    if result['weekend_daily'] is not None:
        print(f"  Weekend goal: {result['weekend_daily']:,.0f} words/day")
    if result['past_goals_preserved'] > 0:
        print(f"  Past daily goals locked: {result['past_goals_preserved']}")
    print(f"  Plan end date: {result['end_date'].strftime('%Y-%m-%d')} (unchanged)")


def offer_daily_recalculation(current_plan):
    """
    Spread the words actually left over the remaining days, keeping the end date.

    The result is previewed on a copy and applied only if the user agrees.

    Returns:
        True if the plan was changed
    """
    preview = copy.deepcopy(current_plan)
    result = preview.recalculate_from_progress()

    if result is None or not result['success']:
        print_recalculation_failure(result)
        return False

    print("\nProposed adjustment:")
    print_recalculation_summary(result)

    if not get_yes_no("\nApply this adjustment?", default='y'):
        print("Plan left unchanged.")
        return False

    current_plan.recalculate_from_progress(as_of_date=result['as_of_date'])
    display_success("Plan recalculated!")
    return True


def get_writing_days(prompt, current_plan):
    """Ask for a number of writing days, not fewer than the plan's locked (past) days."""
    min_days = current_plan.min_writing_days()
    while True:
        days = get_positive_number(prompt)
        if days >= min_days:
            return days
        display_error(f"The plan already has {min_days} past writing days; enter at least {min_days}.")


def describe_dated_days(dates_and_labels):
    """Print '  2026-11-07 (Saturday): spare day' lines, at most 10."""
    for date, label in dates_and_labels[:10]:
        print(f"  {date.strftime('%Y-%m-%d (%A)')}: {label}")
    if len(dates_and_labels) > 10:
        print(f"  ... and {len(dates_and_labels) - 10} more")


def start_date_move_warnings(before, moved):
    """
    What the user should know before a start-date move is applied (decision 7).

    Args:
        before: The plan before the move
        moved: A preview copy with the move applied

    Returns:
        List of warning strings
    """
    warnings = []
    start, end = moved.start_date, moved.end_date
    today = today_midnight()

    outside = [(k, w) for k, w in moved.progress.items()
               if w and not (start <= datetime.strptime(k, '%Y-%m-%d') <= end)]
    if outside:
        words = sum(w for _, w in outside)
        warnings.append(
            f"{len(outside)} day(s) with progress ({words:,.0f} words) are outside the new plan. "
            "Progress never moves: those words still count as written, but not toward any day's goal.")

    before_days = set(before.plan_days())
    joining = [d for d in moved.plan_days() if d < today and d not in before_days
               and not before.is_locked(d)]
    if joining:
        warnings.append(
            f"{len(joining)} day(s) before today join the plan. They are past, so their "
            "goals are locked as they are now.")

    if moved.locked_goals and any(before.is_locked(d) for d in before_days if not start <= d <= end):
        warnings.append("Some past (locked) days are now outside the plan; their goals no longer count.")
    return warnings


def change_start_date(current_plan, new_start):
    """
    Move the plan to a new start date, as decision 7 describes.

    Shows the new window, lists the spare days and custom goals that would
    end up outside it, offers to keep them on their dates (default) or shift
    them all by the same offset, warns about progress outside the new plan,
    and applies the move only after confirmation. Each option is previewed
    on a copy.

    Returns:
        True if the start date changed
    """
    new_start = plan.to_midnight(new_start)

    if not current_plan.start_date:
        current_plan.start_date = new_start
        display_success(f"Start date set to: {new_start.strftime('%Y-%m-%d')}")
        return True

    if current_plan.time <= 0:
        current_plan.start_date = new_start
        display_success(f"Start date changed to: {new_start.strftime('%Y-%m-%d')}")
        return True

    offset = (new_start - current_plan.start_date).days
    if offset == 0:
        print("\nThat is already the start date. Nothing changed.")
        return False

    today = today_midnight()
    movable = [(d, "spare day") for d in current_plan.spare_days_dates if d >= today]
    movable += [(datetime.strptime(k, '%Y-%m-%d'), f"custom goal of {g:,.0f} words")
                for k, g in current_plan.custom_daily_goals.items()
                if datetime.strptime(k, '%Y-%m-%d') >= today]
    movable.sort(key=lambda item: item[0])

    def preview(shift):
        moved = copy.deepcopy(current_plan)
        moved.move_start_date(new_start, shift_dated_days=shift)
        return moved

    def outcome(p):
        return (f"{p.start_date.strftime('%Y-%m-%d')} to {p.end_date.strftime('%Y-%m-%d')}, "
                f"{p.daily:,.0f} words/day")

    keep = preview(False)
    direction = "later" if offset > 0 else "earlier"
    print(f"\nMoving the start {abs(offset)} day(s) {direction}.")
    print(f"   Now: {outcome(current_plan)}")

    shift = False
    if movable:
        def is_outside(d):
            return not keep.start_date <= d <= keep.end_date
        outside = [(d, label) for d, label in movable if is_outside(d)]

        print("\nYour spare days and custom goals from today on:")
        if outside:
            print("These would fall outside the new plan (and be ignored) if kept on their dates:")
            describe_dated_days(outside)
        else:
            print("All of them stay inside the new plan if kept on their dates.")

        shifted = preview(True)
        print("\n1. Keep them on their dates (recommended)")
        print(f"   -> {outcome(keep)}")
        weekday_note = "" if offset % 7 == 0 else " (they land on other weekdays)"
        print(f"2. Shift all of them {abs(offset)} day(s) {direction}{weekday_note}")
        print(f"   -> {outcome(shifted)}")
        print("0. Cancel")
        choice = get_menu_choice("\nEnter your choice (0-2): ", 0, 2)
        if choice == 0:
            print("Start date not changed.")
            return False
        shift = choice == 2
        chosen = shifted if shift else keep
    else:
        chosen = keep
        print(f"   New: {outcome(chosen)}")

    warnings = start_date_move_warnings(current_plan, chosen)
    if chosen.locked_goals or chosen.progress:
        left = chosen.total - chosen.get_total_written()
        warnings.append(f"The plan has started: the open days are recalculated to cover the "
                        f"{max(0, left):,.0f} words left.")
    for warning in warnings:
        display_warning(warning)

    if not get_yes_no("\nApply the new start date?", default='y'):
        print("Start date not changed.")
        return False

    current_plan.move_start_date(new_start, shift_dated_days=shift)
    display_success(f"Start date changed to: {new_start.strftime('%Y-%m-%d')} "
                    f"(plan ends {current_plan.end_date.strftime('%Y-%m-%d')})")
    return True


def modify_plan(current_plan):
    """Allow user to modify plan values and recalculate."""
    print("\n" + "=" * 50)
    print("MODIFY PLAN")
    print("=" * 50)
    print("\nCurrent values:")
    print(f"  Total words: {current_plan.total:,.0f}")
    print(f"  Daily words: {current_plan.daily:,.0f}")
    print(f"  Writing days: {current_plan.time:.0f}")
    print(f"  Spare days: {current_plan.spare_days:.0f}")
    if current_plan.spare_days > 0:
        total_calendar_days = current_plan.time + current_plan.spare_days
        print(f"  Total calendar duration: {total_calendar_days:.0f} days")
    print(f"  Writing pattern: {current_plan.pattern}")
    if current_plan.start_date:
        print(f"  Start date: {current_plan.start_date.strftime('%Y-%m-%d')}")
    else:
        print(f"  Start date: Not set")
    print("\nWhat would you like to modify?")
    print("\n1. Total words")
    print("2. Daily words")
    print("3. Writing days")
    print("4. Spare days")
    print("5. Writing pattern")
    print("6. Start date")
    print("7. Modify two values (third will be calculated)")
    print("8. Weekend settings")
    print("9. Edit individual day goals")
    print("10. Recalculate from progress (redistribute remaining words)")
    print("0. Cancel")
    print("=" * 50)

    while True:
        try:
            choice = int(input("\nEnter your choice (0-10): "))
            if choice == 0:
                return False  # No changes made

            elif choice == 1:
                # Modify total words, ask what to keep constant
                new_total = get_positive_number("\nEnter new total words: ")
                print("\nKeep constant:")
                print("1. Daily words (recalculate time)")
                print("2. Time (recalculate daily words)")

                while True:
                    try:
                        keep_choice = int(input("Enter your choice (1-2): "))
                        if keep_choice == 1:
                            current_plan.total = new_total
                            current_plan.calculate_time()
                            return True
                        elif keep_choice == 2:
                            current_plan.total = new_total
                            current_plan.calculate_daily()
                            return True
                        else:
                            print("Please enter 1 or 2.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")

            elif choice == 2:
                # Modify daily words, ask what to keep constant
                new_daily = get_positive_number("\nEnter new daily words: ")
                print("\nKeep constant:")
                print("1. Total words (recalculate time)")
                print("2. Time (recalculate total words)")

                while True:
                    try:
                        keep_choice = int(input("Enter your choice (1-2): "))
                        if keep_choice == 1:
                            current_plan.daily = new_daily
                            current_plan.calculate_time()
                            return True
                        elif keep_choice == 2:
                            current_plan.daily = new_daily
                            current_plan.calculate_words()
                            return True
                        else:
                            print("Please enter 1 or 2.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")

            elif choice == 3:
                # Modify time, ask what to keep constant
                new_time = get_writing_days("\nEnter new time (days): ", current_plan)
                print("\nKeep constant:")
                print("1. Total words (recalculate daily words)")
                print("2. Daily words (recalculate total words)")

                while True:
                    try:
                        keep_choice = int(input("Enter your choice (1-2): "))
                        if keep_choice == 1:
                            current_plan.time = new_time
                            current_plan.calculate_daily()
                            return True
                        elif keep_choice == 2:
                            current_plan.time = new_time
                            current_plan.calculate_words()
                            return True
                        else:
                            print("Please enter 1 or 2.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")

            elif choice == 4:
                # Manage spare days
                modified = manage_spare_days(current_plan)
                if modified:
                    return True

            elif choice == 5:
                # Change writing pattern
                print(f"\nCurrent pattern: {current_plan.pattern}")
                pattern, pattern_config = choose_writing_pattern()
                current_plan.pattern = pattern
                current_plan.pattern_config = pattern_config
                current_plan.invalidate_daily_goals_cache()
                display_success(f"Pattern changed to: {pattern}")
                return True

            elif choice == 6:
                # Change start date
                if current_plan.start_date:
                    print(f"\nCurrent start date: {current_plan.start_date.strftime('%Y-%m-%d')}")
                else:
                    print(f"\nCurrent start date: Not set")

                print("\nEnter new start date (YYYY-MM-DD, e.g., 2025-10-28)")
                print("Or press Enter for today's date")
                new_start_date = get_date_input("Start date: ")
                return change_start_date(current_plan, new_start_date)

            elif choice == 7:
                # Modify two values, calculate the third
                print("\nWhich value should be calculated?")
                print("1. Calculate total words (from daily × time)")
                print("2. Calculate daily words (from total ÷ time)")
                print("3. Calculate time (from total ÷ daily)")

                while True:
                    try:
                        calc_choice = int(input("Enter your choice (1-3): "))
                        if calc_choice == 1:
                            daily = get_positive_number("Enter daily words: ")
                            time = get_writing_days("Enter writing days: ", current_plan)
                            current_plan.daily = daily
                            current_plan.time = time
                            current_plan.calculate_words()
                            return True
                        elif calc_choice == 2:
                            total = get_positive_number("Enter total words: ")
                            time = get_writing_days("Enter writing days: ", current_plan)
                            current_plan.total = total
                            current_plan.time = time
                            current_plan.calculate_daily()
                            return True
                        elif calc_choice == 3:
                            total = get_positive_number("Enter total words: ")
                            daily = get_positive_number("Enter daily words: ")
                            current_plan.total = total
                            current_plan.daily = daily
                            current_plan.calculate_time()
                            return True
                        else:
                            print("Please enter 1, 2, or 3.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")

            elif choice == 8:
                # Configure weekend settings
                configure_weekend_settings(current_plan)
                return True

            elif choice == 9:
                # Edit individual day goals
                modified = edit_individual_day_goal(current_plan)
                return modified

            elif choice == 10:
                # Recalculate from progress
                modified = recalculate_plan_from_progress(current_plan)
                return modified

            else:
                print("Please enter a number between 0 and 10.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def load_saved_plan():
    """Load a saved plan from disk."""
    print("\n" + "=" * 50)
    print("LOAD SAVED PLAN")
    print("=" * 50)

    saved_plans = plan_storage.list_saved_plans()

    if not saved_plans:
        print("\nNo saved plans found.")
        input("\nPress Enter to continue...")
        return None

    print(f"\nFound {len(saved_plans)} saved plan(s):\n")

    for idx, plan_info in enumerate(saved_plans, start=1):
        plan_name = plan_info['name']
        total = plan_info['total']
        daily = plan_info['daily']
        time = plan_info['time']
        created = plan_info['created_date']
        created_str = created.strftime("%Y-%m-%d %H:%M") if created else "Unknown"

        print(f"{idx}. {plan_name}")
        print(f"   {total:,.0f} words | {daily:,.0f}/day | {time:.0f} days")
        print(f"   Created: {created_str}\n")

    print("0. Cancel")
    print("=" * 50)

    while True:
        try:
            choice = int(input("\nSelect a plan to load (0 to cancel): "))
            if choice == 0:
                return None
            if 1 <= choice <= len(saved_plans):
                plan_info = saved_plans[choice - 1]
                filepath = plan_info['path']

                try:
                    loaded_plan = plan_storage.load_plan(filepath)
                    display_success(f"Loaded plan: {loaded_plan.name}")
                    return loaded_plan
                except Exception as e:
                    display_error(f"Error loading plan: {e}")
                    input("\nPress Enter to continue...")
                    return None
            else:
                print(f"Please enter a number between 0 and {len(saved_plans)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")


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

    while True:
        try:
            choice = int(input("\nEnter your choice (0-3): "))
            if choice in [0, 1, 2, 3]:
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
                    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    newplan.start_date = start_date

                # Display chosen views
                if choice == 1 or choice == 3:
                    calendar_view.display_calendar_view(newplan, start_date)

                if choice == 2 or choice == 3:
                    calendar_view.display_weekly_summary(newplan, start_date)

                return
            else:
                print("Please enter a number between 0 and 3.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def update_progress(current_plan):
    """Update progress for the writing plan."""
    if not current_plan.start_date:
        display_error("You must set a start date before tracking progress.")
        print("  Please view a calendar first to set a start date.")
        input("\nPress Enter to continue...")
        return

    progress_updated = False
    # Offer to adjust the plan at most once per visit to this screen
    adjustment_offered = False

    while True:
        print("\n" + "=" * 50)
        print("UPDATE PROGRESS")
        print("=" * 50)
        print("\nOptions:")
        print("1. Quick entry (today's words)")
        print("2. Enter for a specific date")
        print("3. View all progress entries")
        print("0. Done")
        print("=" * 50)

        try:
            choice = int(input("\nEnter your choice (0-3): "))

            if choice == 0:
                # Prompt to save if progress was updated
                if progress_updated:
                    if get_yes_no("\nProgress was updated. Save the plan?", default='y'):
                        save_plan_prompt(current_plan, ask=False)
                return

            elif choice == 1:
                # Quick entry for today
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                print(f"\nEntering progress for: {today.strftime('%Y-%m-%d (%A)')}")

                # Check if it's a spare day
                if current_plan.is_spare_day(today):
                    print("⚠ Note: This is a spare day (0 words expected)")

                # Show existing progress if any
                existing = current_plan.get_progress_for_date(today)
                if existing is not None:
                    print(f"Current progress: {existing:,} words")

                # Get goal for today
                daily_goal = current_plan.get_daily_goal(date=today)
                print(f"Goal for today: {daily_goal:,.0f} words")

                word_count_input = input("\nHow many words did you write today? (or press Enter to cancel): ").strip()

                if word_count_input == "":
                    continue

                try:
                    word_count = int(word_count_input)
                    if word_count < 0:
                        display_error("Word count cannot be negative")
                        continue

                    current_plan.record_progress(today, word_count)
                    progress_updated = True
                    display_success(f"Progress recorded: {word_count:,} words")

                    # Check if goal was met
                    if word_count >= daily_goal:
                        print("🎉 You met your daily goal!")
                    elif word_count > 0:
                        remaining = daily_goal - word_count
                        print(f"   ({remaining:,.0f} words short of goal)")

                    # Check overall status and offer recalculation
                    if not adjustment_offered:
                        adjustment_offered = check_and_offer_recalculation(current_plan)

                except ValueError:
                    print("✗ Invalid input. Please enter a number.")

            elif choice == 2:
                # Enter for specific date
                print("\nEnter the date (YYYY-MM-DD):")
                date_input = input("Date: ").strip()

                if date_input == "":
                    continue

                try:
                    entry_date = datetime.strptime(date_input, "%Y-%m-%d")

                    # Check if date is in plan range
                    if entry_date < current_plan.start_date:
                        display_error(f"Date is before plan start ({current_plan.start_date.strftime('%Y-%m-%d')})")
                        continue

                    print(f"\nEntering progress for: {entry_date.strftime('%Y-%m-%d (%A)')}")

                    # Check if it's a spare day
                    if current_plan.is_spare_day(entry_date):
                        print("Note: This is a spare day (0 words expected)")

                    # Show existing progress if any
                    existing = current_plan.get_progress_for_date(entry_date)
                    if existing is not None:
                        print(f"Current progress: {existing:,} words")

                    # Get goal for this date
                    daily_goal = current_plan.get_daily_goal(date=entry_date)
                    print(f"Goal for this day: {daily_goal:,.0f} words")

                    word_count_input = input("\nWords written: ").strip()

                    if word_count_input == "":
                        continue

                    word_count = int(word_count_input)
                    if word_count < 0:
                        display_error("Word count cannot be negative")
                        continue

                    current_plan.record_progress(entry_date, word_count)
                    progress_updated = True
                    display_success(f"Progress recorded: {word_count:,} words")

                    # Check overall status and offer recalculation
                    if not adjustment_offered:
                        adjustment_offered = check_and_offer_recalculation(current_plan)

                except ValueError as e:
                    display_error(f"Invalid input: {e}")

            elif choice == 3:
                # View all progress entries
                if not current_plan.progress:
                    display_error("No progress entries recorded yet")
                    input("\nPress Enter to continue...")
                    continue

                print("\n" + "=" * 50)
                print("ALL PROGRESS ENTRIES")
                print("=" * 50)

                # Sort by date
                sorted_dates = sorted(current_plan.progress.keys())

                for date_str in sorted_dates:
                    entry_date = datetime.strptime(date_str, "%Y-%m-%d")
                    word_count = current_plan.progress[date_str]
                    daily_goal = current_plan.get_daily_goal(date=entry_date)

                    status_icon = "✓" if word_count >= daily_goal else "○"
                    print(f"{status_icon} {entry_date.strftime('%Y-%m-%d (%A)')}: {word_count:,} words (goal: {daily_goal:,.0f})")

                input("\nPress Enter to continue...")

            else:
                print("Please enter a number between 0 and 3.")

        except ValueError:
            print("Invalid input. Please enter a number.")


def check_and_offer_recalculation(current_plan):
    """
    Check if user is on track and offer recalculation if needed.

    Returns:
        True if the ahead/behind offer was shown
    """
    on_track, info = current_plan.is_on_track()

    if on_track and info['status'] == 'on_track':
        # Exactly on track, no need to recalculate
        return False

    print("\n" + "-" * 50)
    print("PROGRESS STATUS")
    print("-" * 50)

    if info['status'] == 'ahead':
        print(f"✓ You're AHEAD of schedule!")
        print(f"  Expected: {info['expected_words']:,.0f} words")
        print(f"  Actual: {info['actual_words']:,.0f} words")
        print(f"  Ahead by: {info['difference']:,.0f} words ({info['percent_diff']:.1f}%)")

        if get_yes_no("\nWould you like to adjust your plan?", default='n'):
            offer_ahead_recalculation(current_plan, info)

    elif info['status'] == 'behind':
        print(f"⚠ You're BEHIND schedule")
        print(f"  Expected: {info['expected_words']:,.0f} words")
        print(f"  Actual: {info['actual_words']:,.0f} words")
        print(f"  Behind by: {abs(info['difference']):,.0f} words ({abs(info['percent_diff']):.1f}%)")

        if get_yes_no("\nWould you like to adjust your plan?", default='n'):
            offer_behind_recalculation(current_plan, info)

    return True


def offer_deadline_adjustment(current_plan):
    """
    Keep the daily goal and move the end date to fit the words actually left.

    Starts today, or tomorrow if words were already logged today. The result
    is previewed on a copy and applied only if the user agrees.
    """
    preview = copy.deepcopy(current_plan)
    as_of_date = preview.default_recalculation_date()
    result = preview.adjust_time_from_progress(as_of_date=as_of_date)

    if result is None or result['new_end_date'] is None or result['old_end_date'] is None:
        display_error("Could not adjust the deadline.")
        return

    day_change = (result['new_end_date'] - result['old_end_date']).days
    print(f"\nProposed adjustment:")
    print(f"  Daily goal: {result['daily']:,.0f} words/day")
    print(f"  Writing days: {result['old_time']} -> {result['new_time']}")
    print(f"  End date: {result['old_end_date'].strftime('%Y-%m-%d')} -> {result['new_end_date'].strftime('%Y-%m-%d')}")
    if day_change < 0:
        print(f"  Finishing early by: {-day_change} days")
    elif day_change > 0:
        print(f"  Extension: {day_change} days")
    else:
        print("  End date unchanged")

    if get_yes_no("Apply this adjustment?", default='y'):
        current_plan.adjust_time_from_progress(as_of_date=as_of_date)
        display_success("Plan adjusted!")


def offer_ahead_recalculation(current_plan, info):
    """Offer recalculation options when ahead of schedule."""
    print("\n" + "=" * 50)
    print("ADJUST PLAN (AHEAD OF SCHEDULE)")
    print("=" * 50)
    print("\nHow would you like to adjust your plan?")
    print("\n1. Reduce daily goals (keep end date)")
    print("2. Finish early (keep daily goals)")
    print("0. Keep plan as is")
    print("=" * 50)

    while True:
        try:
            choice = int(input("\nEnter your choice (0-2): "))

            if choice == 0:
                return

            elif choice == 1:
                # Reduce daily goals (keep end date)
                offer_daily_recalculation(current_plan)
                return

            elif choice == 2:
                # Finish early
                offer_deadline_adjustment(current_plan)
                return

            else:
                print("Please enter 0, 1, or 2.")

        except ValueError:
            print("Invalid input. Please enter a number.")


def offer_behind_recalculation(current_plan, info):
    """Offer recalculation options when behind schedule."""
    print("\n" + "=" * 50)
    print("ADJUST PLAN (BEHIND SCHEDULE)")
    print("=" * 50)
    print("\nHow would you like to adjust your plan?")
    print("\n1. Increase daily goals (keep end date)")
    print("2. Extend deadline (keep daily goals)")
    print("0. Keep plan as is")
    print("=" * 50)

    while True:
        try:
            choice = int(input("\nEnter your choice (0-2): "))

            if choice == 0:
                return

            elif choice == 1:
                # Increase daily goals (keep end date)
                offer_daily_recalculation(current_plan)
                return

            elif choice == 2:
                # Extend deadline
                offer_deadline_adjustment(current_plan)
                return

            else:
                print("Please enter 0, 1, or 2.")

        except ValueError:
            print("Invalid input. Please enter a number.")


def view_progress_summary(current_plan):
    """Display a comprehensive progress summary."""
    if not current_plan.start_date:
        display_error("No start date set")
        input("\nPress Enter to continue...")
        return

    print("\n" + "=" * 50)
    print("PROGRESS SUMMARY")
    print("=" * 50)

    # Overall progress
    total_written = current_plan.get_total_written()
    remaining = current_plan.get_remaining_words()
    completion = current_plan.get_completion_percentage()

    print(f"\nOverall Progress:")
    print(f"  Total goal: {current_plan.total:,.0f} words")
    print(f"  Written: {total_written:,} words ({completion:.1f}%)")
    print(f"  Remaining: {remaining:,} words")

    # Days with progress
    days_recorded = current_plan.get_days_with_progress()
    print(f"\n  Days recorded: {days_recorded}")

    # Current streak
    streak = current_plan.get_current_streak()
    if streak > 0:
        print(f"  Current streak: {streak} day{'s' if streak != 1 else ''} 🔥")

    # On track status
    on_track, info = current_plan.is_on_track()

    print(f"\nSchedule Status:")
    if info.get('message'):
        print(f"  {info['message']}")
    else:
        if info['status'] == 'ahead':
            print(f"  ✓ AHEAD by {info['difference']:,.0f} words ({info['percent_diff']:.1f}%)")
        elif info['status'] == 'on_track':
            print(f"  ✓ ON TRACK")
        else:
            print(f"  ⚠ BEHIND by {abs(info['difference']):,.0f} words ({abs(info['percent_diff']):.1f}%)")

        print(f"  Expected: {info['expected_words']:,.0f} words")
        print(f"  Actual: {info['actual_words']:,.0f} words")
        print(f"  Days elapsed: {info['days_elapsed']}")

    input("\nPress Enter to continue...")


def export_plan_menu(current_plan):
    """Display export menu and handle export operations."""
    if not current_plan.start_date:
        display_error("Plan must have a start date to export.")
        print("  Please view a calendar first to set a start date.")
        input("\nPress Enter to continue...")
        return

    print("\n" + "=" * 50)
    print("EXPORT PLAN")
    print("=" * 50)
    print("\nChoose export format:")
    print("\n1. CSV (Spreadsheet)")
    print("   - Day-by-day breakdown with goals and progress")
    print("   - Compatible with Excel, Google Sheets, etc.")
    print("\n2. iCal/ICS (Calendar)")
    print("   - Import into Google Calendar, Apple Calendar, etc.")
    print("   - Daily writing reminders")
    print("\n3. Markdown (Text)")
    print("   - Readable text format")
    print("   - Good for sharing or documentation")
    print("\n4. All formats")
    print("0. Cancel")
    print("=" * 50)

    while True:
        try:
            choice = int(input("\nEnter your choice (0-4): "))

            if choice == 0:
                return

            elif choice in [1, 2, 3, 4]:
                # Determine which formats to export
                formats_to_export = []
                if choice == 1:
                    formats_to_export = ['csv']
                elif choice == 2:
                    formats_to_export = ['ical']
                elif choice == 3:
                    formats_to_export = ['markdown']
                elif choice == 4:
                    formats_to_export = ['csv', 'ical', 'markdown']

                # Export each format
                exported_files = []
                for fmt in formats_to_export:
                    try:
                        if fmt == 'csv':
                            filepath = plan_export.export_to_csv(current_plan)
                            display_success(f"CSV exported: {filepath}")
                        elif fmt == 'ical':
                            filepath = plan_export.export_to_ical(current_plan)
                            display_success(f"iCal exported: {filepath}")
                        elif fmt == 'markdown':
                            filepath = plan_export.export_to_markdown(current_plan)
                            display_success(f"Markdown exported: {filepath}")

                        exported_files.append(filepath)
                    except Exception as e:
                        display_error(f"Error exporting {fmt}: {e}")

                if exported_files:
                    display_success(f"Exported {len(exported_files)} file(s)")
                    print(f"  Location: {plan_export.get_exports_directory()}")

                input("\nPress Enter to continue...")
                return

            else:
                print("Please enter a number between 0 and 4.")
        except ValueError:
            print("Invalid input. Please enter a number.")


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
        return save_plan_prompt(current_plan, ask=False)
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
            update_progress(current_plan)

        elif action == 2:
            # View progress summary
            view_progress_summary(current_plan)

        elif action == 3:
            # View progress graphs & analytics
            progress_analytics.show_analytics_menu(current_plan)

        elif action == 4:
            # Modify plan
            modified = modify_plan(current_plan)
            if modified:
                display_success("Plan modified successfully!")
            # Loop continues to show updated results

        elif action == 5:
            # View calendar
            show_calendar_options(current_plan)

        elif action == 6:
            # Export plan
            export_plan_menu(current_plan)

        elif action == 7:
            # Save plan
            save_plan_prompt(current_plan)


def configure_weekend_settings(current_plan):
    """Configure weekend-specific settings for the plan."""
    print("\n" + "=" * 50)
    print("WEEKEND CONFIGURATION")
    print("=" * 50)
    print("\nHow would you like to handle weekends?")
    print("\n1. Same as weekdays - Write the same amount every day")
    print("2. Different goal - Set a specific word count for weekends")
    print("3. Weekends as spare days - No writing on weekends")
    print("0. Skip weekend configuration")
    print("=" * 50)

    while True:
        try:
            choice = int(input("\nEnter your choice (0-3): "))
            if choice in [0, 1, 2, 3]:
                break
            else:
                print("Please enter a number between 0 and 3.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    if choice == 0:
        # Keep default: same as weekdays
        return

    before = copy.deepcopy(current_plan)

    if choice == 1:
        current_plan.weekend_mode = "same"
        display_success("Weekends will have the same writing goal as weekdays")

    elif choice == 2:
        current_plan.weekend_mode = "different"
        print("\nSet weekend writing goal:")
        print("(This could be higher for extra writing time, or lower for rest)")
        weekend_goal = get_positive_number("Weekend daily goal: ")
        current_plan.weekend_daily = weekend_goal
        display_success(f"Weekends will have a goal of {weekend_goal:,.0f} words/day")

    elif choice == 3:
        current_plan.weekend_mode = "spare"
        display_success("All weekends will be marked as spare days (0 words)")

    # Ask about which days are weekends
    if choice in [2, 3]:
        if get_yes_no("\nCustomize which days are considered 'weekend'?", default='n'):
            print("\nSelect weekend days (Saturday and Sunday are default):")
            print("0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday")
            days_input = input("Enter day numbers separated by commas (e.g., 5,6): ").strip()
            try:
                weekend_days = [int(d.strip()) for d in days_input.split(',')]
                weekend_days = [d for d in weekend_days if 0 <= d <= 6]
                if weekend_days:
                    current_plan.weekend_days = weekend_days
                    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                    weekend_names = [day_names[d] for d in weekend_days]
                    display_success(f"Weekend days set to: {', '.join(weekend_names)}")
                else:
                    display_warning("Invalid days, using default (Sat, Sun)")
            except ValueError:
                display_warning("Invalid input, using default weekend days (Sat, Sun)")

    # Decision 1: ask how the plan absorbs the change
    rebalance_after_writing_days_change(current_plan, before)


def ask_for_pre_existing_words_count(total_goal=None):
    """
    Ask user if they have words already written for this project.
    Returns the word count without recording it yet.

    Args:
        total_goal: Optional total goal to check against

    Returns:
        Number of pre-existing words, or 0 if none
    """
    print("\n" + "=" * 50)
    print("PRE-EXISTING WORDS")
    print("=" * 50)
    print("\nDo you have words already written for this project?")
    if total_goal:
        print(f"(Your total goal is {total_goal:,.0f} words)")
    print("(Pre-existing words will be subtracted when calculating your plan)")

    if not get_yes_no("\nHave you already written some words?", default='n'):
        return 0

    while True:
        words_written = get_positive_number("\nHow many words have you already written? ")

        if words_written <= 0:
            display_error("Word count must be positive")
            continue

        # Check if it exceeds the total goal
        if total_goal and words_written >= total_goal:
            print(f"\n⚠ Warning: You've already written {words_written:,.0f} words")
            print(f"  This equals or exceeds your goal of {total_goal:,.0f} words!")
            print(f"  You may have already completed your goal!")

            if get_yes_no("Continue anyway?", default='n'):
                return words_written
            else:
                continue

        # Show impact
        if total_goal:
            remaining = total_goal - words_written
            completion_pct = (words_written / total_goal) * 100

            print(f"\n✓ Pre-existing words: {words_written:,.0f}")
            print(f"  Progress: {completion_pct:.1f}% of goal")
            print(f"  Remaining to write: {remaining:,.0f} words")

        if get_yes_no("\nConfirm this word count?", default='y'):
            return words_written


def create_plan_from_template():
    """Create a plan from a pre-defined template."""
    print("\n" + "=" * 50)
    print("CREATE FROM TEMPLATE")
    print("=" * 50)

    # Get templates by category
    categories = plan_templates.list_templates_by_category()
    all_templates = plan_templates.get_all_templates()

    # Display templates by category
    template_list = []
    option_num = 1

    for category, template_keys in categories.items():
        print(f"\n{category}:")
        for key in template_keys:
            template = all_templates[key]
            print(f"  {option_num}. {template}")
            print(f"     {template.description}")
            template_list.append((key, template))
            option_num += 1

    print(f"\n0. Cancel")
    print("=" * 50)

    # Get user choice
    while True:
        try:
            choice = int(input(f"\nSelect a template (0-{len(template_list)}): "))
            if choice == 0:
                return  # Cancel
            elif 1 <= choice <= len(template_list):
                template_key, selected_template = template_list[choice - 1]
                break
            else:
                print(f"Please enter a number between 0 and {len(template_list)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Show template details
    print("\n" + "=" * 50)
    print(f"TEMPLATE: {selected_template.name}")
    print("=" * 50)
    print(f"Description: {selected_template.description}")
    print(f"Total words: {selected_template.total:,}")
    if selected_template.time:
        print(f"Duration: {selected_template.time} days")
    if selected_template.daily:
        print(f"Daily goal: {selected_template.daily:,.0f} words/day")
    if selected_template.suggested_pattern:
        print(f"Suggested pattern: {selected_template.suggested_pattern}")
    if selected_template.suggested_weekend_mode:
        print(f"Suggested weekend mode: {selected_template.suggested_weekend_mode}")

    # Ask if user wants to customize
    if not get_yes_no("\nUse this template as-is?", default='y'):
        print("\n" + "=" * 50)
        print("CUSTOMIZE TEMPLATE")
        print("=" * 50)

        # Allow customization
        if get_yes_no("Change total word count?", default='n'):
            new_total = get_positive_number("Enter total words: ")
            selected_template.total = new_total

        if selected_template.time and get_yes_no("Change duration (days)?", default='n'):
            new_time = get_positive_number("Enter number of days: ")
            selected_template.time = new_time
            selected_template.daily = None  # Will be recalculated

        elif selected_template.daily and get_yes_no("Change daily goal?", default='n'):
            new_daily = get_positive_number("Enter daily words: ")
            selected_template.daily = new_daily
            selected_template.time = None  # Will be recalculated

    # Ask about pre-existing words before creating the plan
    pre_existing_words = ask_for_pre_existing_words_count(total_goal=selected_template.total)

    if pre_existing_words >= selected_template.total:
        display_success("You've already met or exceeded this goal!")
        print(f"  Goal: {selected_template.total:,.0f} words")
        print(f"  Already written: {pre_existing_words:,.0f} words")
        input("\nPress Enter to continue...")
        return

    # Ask for start date
    print("\n" + "=" * 50)
    print("PLAN START DATE")
    print("=" * 50)
    print("\nWhen would you like to start writing?")
    print("Enter date in format YYYY-MM-DD (e.g., 2025-10-28)")
    print("Or press Enter for today's date")
    start_date = get_date_input("Start date: ")

    # Create plan from template
    newplan = selected_template.create_plan(start_date=start_date,
                                            preexisting_words=int(pre_existing_words))
    newplan.name = selected_template.name

    display_success(f"Created plan from template: {selected_template.name}")
    print(f"  Start date: {start_date.strftime('%Y-%m-%d')}")

    # Apply suggested pattern if available
    if selected_template.suggested_pattern:
        if get_yes_no(f"\nApply suggested '{selected_template.suggested_pattern}' pattern?", default='y'):
            newplan.pattern = selected_template.suggested_pattern
            if selected_template.suggested_pattern != 'flat':
                # Ask for intensity
                print("\nPattern intensity:")
                print("1. Mild")
                print("2. Moderate (recommended)")
                print("3. Extreme")

                while True:
                    try:
                        intensity_choice = int(input("Select intensity (1-3): "))
                        if intensity_choice == 1:
                            newplan.pattern_config = {'intensity': 'mild'}
                            break
                        elif intensity_choice == 2:
                            newplan.pattern_config = {'intensity': 'moderate'}
                            break
                        elif intensity_choice == 3:
                            newplan.pattern_config = {'intensity': 'extreme'}
                            break
                        else:
                            print("Please enter 1, 2, or 3.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")

            print(f"✓ Applied {newplan.pattern} pattern")

    # Apply suggested weekend mode if available
    if selected_template.suggested_weekend_mode and selected_template.suggested_weekend_mode != 'same':
        if get_yes_no(f"\nConfigure weekend settings as suggested?", default='y'):
            before = copy.deepcopy(newplan)
            if selected_template.suggested_weekend_mode == 'different':
                newplan.weekend_mode = 'different'
                # Suggest 1.5x the daily goal for weekends
                suggested_weekend_goal = int(newplan.daily * 1.5)
                print(f"\nSuggested weekend goal: {suggested_weekend_goal:,.0f} words/day")
                if get_yes_no("Use this weekend goal?", default='y'):
                    newplan.weekend_daily = suggested_weekend_goal
                else:
                    weekend_goal = get_positive_number("Enter weekend daily goal: ")
                    newplan.weekend_daily = weekend_goal
                print(f"✓ Weekend mode: different ({newplan.weekend_daily:,.0f} words/day)")
            elif selected_template.suggested_weekend_mode == 'spare':
                newplan.weekend_mode = 'spare'
                print("✓ Weekend mode: spare (no writing on weekends)")
            rebalance_after_writing_days_change(newplan, before)

    # Handle plan actions
    handle_plan_actions(newplan)


def create_new_plan():
    """Handle the creation of a new plan."""
    calc_choice = choose_calculation_method()

    if calc_choice == 0:
        return  # Go back to main menu

    newplan = None
    pre_existing_words = 0

    if calc_choice == 1:
        # Know total words and daily words → calculate time
        print("\n--- Calculate days needed ---")
        total = get_positive_number("Enter your total word goal: ")

        # Ask about pre-existing words
        pre_existing_words = ask_for_pre_existing_words_count(total_goal=total)

        daily = get_positive_number("Enter how many words you can write daily: ")

        if pre_existing_words >= total:
            display_success("You've already met or exceeded your goal!")
            print(f"  Goal: {total:,.0f} words")
            print(f"  Already written: {pre_existing_words:,.0f} words")
            input("\nPress Enter to continue...")
            return

        # Time is calculated for the words still to write
        newplan = plan.Plan(total=total, daily=daily, preexisting_words=int(pre_existing_words))
        newplan.calculate_time()

    elif calc_choice == 2:
        # Know daily words and time → calculate total words
        print("\n--- Calculate total words ---")
        daily = get_positive_number("Enter how many words you can write daily: ")
        time = get_positive_number("Enter how many days you have available: ")

        # Ask about pre-existing words (no total yet to check against)
        pre_existing_words = ask_for_pre_existing_words_count()

        # Total = daily × time + pre-existing words
        newplan = plan.Plan(daily=daily, time=time, preexisting_words=int(pre_existing_words))
        newplan.calculate_words()

    elif calc_choice == 3:
        # Know total words and time → calculate daily words
        print("\n--- Calculate daily words needed ---")
        total = get_positive_number("Enter your total word goal: ")

        # Ask about pre-existing words
        pre_existing_words = ask_for_pre_existing_words_count(total_goal=total)

        time = get_positive_number("Enter how many days you have available: ")

        if pre_existing_words >= total:
            display_success("You've already met or exceeded your goal!")
            print(f"  Goal: {total:,.0f} words")
            print(f"  Already written: {pre_existing_words:,.0f} words")
            input("\nPress Enter to continue...")
            return

        # Daily is calculated for the words still to write
        newplan = plan.Plan(total=total, time=time, preexisting_words=int(pre_existing_words))
        newplan.calculate_daily()

    if newplan:
        # Ask if user wants to use a writing pattern
        if get_yes_no("\nWould you like to use a variable writing pattern?", default='n'):
            pattern, pattern_config = choose_writing_pattern()
            newplan.pattern = pattern
            newplan.pattern_config = pattern_config
            display_success(f"Using {pattern} pattern")

        # Ask for start date
        print("\n" + "=" * 50)
        print("PLAN START DATE")
        print("=" * 50)
        print("\nWhen would you like to start writing?")
        print("Enter date in format YYYY-MM-DD (e.g., 2025-10-28)")
        print("Or press Enter for today's date")
        start_date = get_date_input("Start date: ")
        newplan.start_date = start_date
        display_success(f"Plan starts on: {start_date.strftime('%Y-%m-%d')}")

        # Configure weekend settings
        if get_yes_no("\nWould you like to configure weekend-specific settings?", default='n'):
            configure_weekend_settings(newplan)

        handle_plan_actions(newplan)


def configure_save_directory():
    """Configure the custom save directory for plans and exports."""
    display_header("CONFIGURE SAVE DIRECTORY")

    # Show current directory
    current_custom_dir = user_preferences.get_custom_save_directory()

    if current_custom_dir:
        print(f"\nCurrent save directory: {current_custom_dir}")
        print(f"Plans are saved in: {current_custom_dir}/plans")
        print(f"Exports are saved in: {current_custom_dir}/exports")
    else:
        default_dir = Path.home() / config.SAVE_DIRECTORY
        print(f"\nUsing default save directory: {default_dir}")
        print(f"Plans are saved in: {default_dir}/plans")
        print(f"Exports are saved in: {default_dir}/exports")

    print("\n" + "=" * 50)
    print("\nWhat would you like to do?")
    print("\n1. Set a custom save directory")
    print("2. Reset to default directory")
    print("0. Back to main menu")
    print("=" * 50)

    choice = get_menu_choice("\nEnter your choice (0-2): ", 0, 2)

    if choice == 0:
        return

    elif choice == 1:
        # Set custom directory
        print("\n" + "=" * 50)
        print("Enter the full path to your custom save directory.")
        print("Example: /home/username/Documents/writing-plans")
        print("or: ~/Documents/writing-plans")
        print("\nPress Enter to cancel.")
        print("=" * 50)

        custom_path = input("\nCustom directory path: ").strip()

        if not custom_path:
            display_warning("No directory entered. Keeping current settings.")
            return

        # Expand user path (handle ~)
        custom_path = str(Path(custom_path).expanduser())

        # Validate the path
        path_obj = Path(custom_path)

        # Check if path exists or can be created
        if not path_obj.exists():
            if get_yes_no(f"\nDirectory '{custom_path}' does not exist. Create it?", default='y'):
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                    display_success(f"Created directory: {custom_path}")
                except Exception as e:
                    display_error(f"Could not create directory: {e}")
                    return
            else:
                display_warning("Directory not created. Settings not changed.")
                return

        # Check if it's a directory
        if not path_obj.is_dir():
            display_error(f"'{custom_path}' is not a directory.")
            return

        # Check if it's writable
        test_file = path_obj / ".test_write"
        try:
            test_file.touch()
            test_file.unlink()
        except Exception:
            display_error(f"Directory '{custom_path}' is not writable.")
            return

        # Save the custom directory
        user_preferences.set_custom_save_directory(custom_path)
        display_success(f"Custom save directory set to: {custom_path}")
        print(f"\nPlans will be saved in: {custom_path}/plans")
        print(f"Exports will be saved in: {custom_path}/exports")

    elif choice == 2:
        # Reset to default
        if current_custom_dir:
            if get_yes_no("\nAre you sure you want to reset to the default directory?", default='n'):
                user_preferences.set_custom_save_directory(None)
                default_dir = Path.home() / config.SAVE_DIRECTORY
                display_success(f"Reset to default directory: {default_dir}")
        else:
            display_warning("Already using default directory.")


def settings_menu():
    """Display the settings menu."""
    while True:
        display_header("SETTINGS")
        print("\nWhat would you like to configure?")
        print("\n1. Save directory location")
        print("0. Back to main menu")
        print("=" * 50)

        choice = get_menu_choice("\nEnter your choice (0-1): ", 0, 1)

        if choice == 0:
            break
        elif choice == 1:
            configure_save_directory()


def save_after_interrupt(current_plan):
    """
    Ctrl+C or end of input: don't lose unsaved changes.

    Asks whether to save. If asking isn't possible (end of input, or a second
    Ctrl+C), a copy is saved as a new "(recovered)" plan instead, so the
    original file is never overwritten without confirmation.
    """
    if current_plan is None or not current_plan.has_unsaved_changes():
        return
    try:
        print("\nThe open plan has unsaved changes.")
        if get_yes_no("Save them before quitting?", default='y'):
            save_plan_prompt(current_plan, ask=False)
    except (KeyboardInterrupt, EOFError):
        recovered = copy.deepcopy(current_plan)
        recovered.name = f"{current_plan.name or 'plan'} (recovered)"
        try:
            filepath = plan_storage.save_plan(recovered, overwrite_source=False)
            print(f"\nUnsaved changes kept in a new plan: {filepath}")
        except Exception as e:
            print(f"\nCould not save the unsaved changes: {e}")


def main():
    """Main function to run the interactive word planner."""
    try:
        main_menu_loop()
    except (KeyboardInterrupt, EOFError):
        print()
        save_after_interrupt(_open_plan)
        print("\nThank you for using Word Count Planner. Happy writing!")


def main_menu_loop():
    """The main menu, until the user exits."""
    while True:
        choice = initial_menu()

        if choice == 0:
            print("\nThank you for using Word Count Planner. Happy writing!")
            break

        elif choice == 1:
            # Create a new plan from scratch
            create_new_plan()

        elif choice == 2:
            # Create plan from template
            create_plan_from_template()

        elif choice == 3:
            # Load a saved plan
            loaded_plan = load_saved_plan()
            if loaded_plan:
                handle_plan_actions(loaded_plan)

        elif choice == 4:
            # Manage multiple plans
            import plan_manager_ui
            plan_manager_ui.manage_plans_menu()

        elif choice == 5:
            # Settings
            settings_menu()


if __name__ == "__main__":
    main()
