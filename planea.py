#!/usr/bin/python3

"""This is an intended clone for the pacemaker.press site.
It intends to get a plan for daily work on words per day."""

from datetime import datetime
import readline
import plan
import calendar_view
import plan_storage
import plan_export
import progress_analytics
import plan_templates
import config
from ui_utils import (
    get_yes_no, get_positive_number, get_date_input, get_menu_choice,
    display_header, display_section, display_success, display_error
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
    print("0. Exit")
    print("=" * 50)

    return get_menu_choice("\nEnter your choice (0-3): ", 0, 3)


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


def save_plan_prompt(newplan):
    """Ask user if they want to save the plan."""
    if get_yes_no("\nWould you like to save this plan?", default='y'):
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


def manage_spare_days(current_plan):
    """Interactively manage spare days for the plan."""
    from datetime import timedelta, datetime as dt

    # Check if start_date is set
    if not current_plan.start_date:
        display_error("You must set a start date before managing spare days.")
        print("  Please view a calendar first to set a start date.")
        return False

    total_calendar_days = int(current_plan.time) + current_plan.spare_days
    plan_end_date = current_plan.start_date + timedelta(days=total_calendar_days - 1)

    while True:
        print("\n" + "=" * 50)
        print("MANAGE SPARE DAYS")
        print("=" * 50)
        print("\nSpare days are days with 0 words (holidays, urgent matters, etc.)")
        print(f"Plan period: {current_plan.start_date.strftime('%Y-%m-%d')} to {plan_end_date.strftime('%Y-%m-%d')}")
        print(f"Writing days: {current_plan.time:.0f}")
        print(f"Spare days: {current_plan.spare_days}")

        if current_plan.spare_days > 0:
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
                        from datetime import timedelta
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
                print(f"  {spare_date.strftime('%Y-%m-%d (%A)')}")

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
                    max_allowed_date = current_plan.start_date + timedelta(days=365 + int(current_plan.time))
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

                    total_calendar_days = int(current_plan.time) + current_plan.spare_days
                    plan_end_date = current_plan.start_date + timedelta(days=total_calendar_days - 1)

                    display_success(f"Added {added_count} spare day(s)")
                    if added_count < len(new_spare_dates):
                        print(f"  ({len(new_spare_dates) - added_count} were already marked as spare)")

                except ValueError as e:
                    display_error(f"Invalid date format: {e}")
                    print("  Please use YYYY-MM-DD format (e.g., 2025-12-25)")

            elif choice == 2:
                # Remove spare days by date
                if current_plan.spare_days == 0:
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

                    # Remove from spare days
                    removed_count = 0
                    for remove_date in dates_to_remove:
                        for i, spare_date in enumerate(current_plan.spare_days_dates[:]):
                            if remove_date.date() == spare_date.date():
                                current_plan.spare_days_dates.remove(spare_date)
                                removed_count += 1
                                break

                    total_calendar_days = int(current_plan.time) + current_plan.spare_days
                    plan_end_date = current_plan.start_date + timedelta(days=total_calendar_days - 1)

                    display_success(f"Removed {removed_count} spare day(s)")
                    if removed_count < len(dates_to_remove):
                        print(f"  ({len(dates_to_remove) - removed_count} were not spare days)")

                except ValueError as e:
                    display_error(f"Invalid date format: {e}")

            elif choice == 3:
                # Clear all spare days
                if current_plan.spare_days == 0:
                    display_error("No spare days to clear")
                    continue

                if get_yes_no(f"Clear all {current_plan.spare_days} spare days?", default='n'):
                    current_plan.spare_days_dates.clear()
                    total_calendar_days = int(current_plan.time)
                    plan_end_date = current_plan.start_date + timedelta(days=total_calendar_days - 1)
                    display_success("All spare days cleared")

            elif choice == 4:
                # Mark all Saturdays as spare
                added_count = 0
                current = current_plan.start_date
                one_year_later = current_plan.start_date + timedelta(days=365)

                while current <= one_year_later:
                    if current.weekday() == 5:  # Saturday
                        # Check if not already a spare day
                        is_duplicate = False
                        for existing in current_plan.spare_days_dates:
                            if current.date() == existing.date():
                                is_duplicate = True
                                break
                        if not is_duplicate:
                            current_plan.spare_days_dates.append(current)
                            added_count += 1
                    current += timedelta(days=1)

                total_calendar_days = int(current_plan.time) + current_plan.spare_days
                plan_end_date = current_plan.start_date + timedelta(days=total_calendar_days - 1)
                display_success(f"Marked {added_count} Saturdays as spare days")

            elif choice == 5:
                # Mark all Sundays as spare
                added_count = 0
                current = current_plan.start_date
                one_year_later = current_plan.start_date + timedelta(days=365)

                while current <= one_year_later:
                    if current.weekday() == 6:  # Sunday
                        # Check if not already a spare day
                        is_duplicate = False
                        for existing in current_plan.spare_days_dates:
                            if current.date() == existing.date():
                                is_duplicate = True
                                break
                        if not is_duplicate:
                            current_plan.spare_days_dates.append(current)
                            added_count += 1
                    current += timedelta(days=1)

                total_calendar_days = int(current_plan.time) + current_plan.spare_days
                plan_end_date = current_plan.start_date + timedelta(days=total_calendar_days - 1)
                display_success(f"Marked {added_count} Sundays as spare days")

            elif choice == 6:
                # Mark all weekends as spare
                added_count = 0
                current = current_plan.start_date
                one_year_later = current_plan.start_date + timedelta(days=365)

                while current <= one_year_later:
                    if current.weekday() in [5, 6]:  # Saturday or Sunday
                        # Check if not already a spare day
                        is_duplicate = False
                        for existing in current_plan.spare_days_dates:
                            if current.date() == existing.date():
                                is_duplicate = True
                                break
                        if not is_duplicate:
                            current_plan.spare_days_dates.append(current)
                            added_count += 1
                    current += timedelta(days=1)

                total_calendar_days = int(current_plan.time) + current_plan.spare_days
                plan_end_date = current_plan.start_date + timedelta(days=total_calendar_days - 1)
                display_success(f"Marked {added_count} weekend days as spare")

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


def recalculate_plan_with_choice(current_plan, old_total, choice_mode):
    """
    Recalculate plan based on user's choice of what to keep constant.

    Args:
        current_plan: The Plan object to recalculate
        old_total: The total before changes
        choice_mode: 'total' or 'days'
    """
    from datetime import timedelta
    if choice_mode == 'days':
        # Keep days constant, adjust total
        new_total = current_plan.recalculate_total_from_daily_goals()
        if abs(new_total - old_total) > 0.01:
            print(f"\nPlan total adjusted: {old_total:,.0f} -> {new_total:,.0f} words")

    elif choice_mode == 'total':
        # Keep total constant, adjust daily goals for non-customized days
        # Calculate the new total based on current settings
        calculated_total = current_plan.recalculate_total_from_daily_goals()

        # Calculate how many words need to be redistributed
        words_to_redistribute = old_total - calculated_total

        if abs(words_to_redistribute) < 0.01:
            print("\nNo adjustment needed - total remains the same")
            return

        # Count adjustable days (non-custom, non-spare, non-weekend-with-custom-goal)
        adjustable_days = 0
        total_calendar_days = int(current_plan.time) + current_plan.spare_days
        current_date = current_plan.start_date

        for day_num in range(total_calendar_days):
            date_key = current_date.strftime('%Y-%m-%d')

            # Skip spare days
            if current_plan.is_spare_day(current_date):
                current_date += timedelta(days=1)
                continue

            # Skip days with custom goals
            if date_key in current_plan.custom_daily_goals:
                current_date += timedelta(days=1)
                continue

            # Skip weekends if they have a specific different goal
            if current_plan.is_weekend(current_date) and current_plan.weekend_mode == "different":
                current_date += timedelta(days=1)
                continue

            adjustable_days += 1
            current_date += timedelta(days=1)

        if adjustable_days == 0:
            print("\nWarning: No adjustable days remaining!")
            print("All days have custom goals, weekend settings, or are spare days.")
            print(f"Total will be: {calculated_total:,.0f} words")
            current_plan.total = calculated_total
            return

        # Calculate adjustment per adjustable day
        adjustment_per_day = words_to_redistribute / adjustable_days
        new_daily = current_plan.daily + adjustment_per_day

        print(f"\nAdjusting {adjustable_days} days to maintain total of {old_total:,.0f} words")
        print(f"  Base daily goal: {current_plan.daily:,.0f} -> {new_daily:,.0f} words/day")
        print(f"  Change: {adjustment_per_day:+.0f} words/day")

        # Update the base daily goal
        current_plan.daily = new_daily
        current_plan.total = old_total
        current_plan.invalidate_daily_goals_cache()


def edit_individual_day_goal(current_plan):
    """Edit the word goal for a specific day."""
    from datetime import datetime as dt, timedelta

    if not current_plan.start_date:
        display_error("You must set a start date before editing individual day goals.")
        return False

    print("\n" + "=" * 50)
    print("EDIT INDIVIDUAL DAY GOAL")
    print("=" * 50)
    print("\nThis allows you to set a custom word goal for a specific date.")
    print("This overrides pattern-based goals and weekend settings for that day.")

    total_calendar_days = int(current_plan.time) + current_plan.spare_days
    plan_end_date = current_plan.start_date + timedelta(days=total_calendar_days - 1)
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
    print("0. Cancel")
    print("=" * 50)

    while True:
        try:
            choice = int(input("\nEnter your choice (0-9): "))
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
                new_time = get_positive_number("\nEnter new time (days): ")
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
                current_plan.start_date = new_start_date
                display_success(f"Start date changed to: {new_start_date.strftime('%Y-%m-%d')}")
                return True

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
                            time = get_positive_number("Enter writing days: ")
                            current_plan.daily = daily
                            current_plan.time = time
                            current_plan.calculate_words()
                            return True
                        elif calc_choice == 2:
                            total = get_positive_number("Enter total words: ")
                            time = get_positive_number("Enter writing days: ")
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

            else:
                print("Please enter a number between 0 and 9.")
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
                    start_date = datetime.now()
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
                        save_plan_prompt(current_plan)
                return

            elif choice == 1:
                # Quick entry for today
                today = datetime.now()
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
                    check_and_offer_recalculation(current_plan)

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
                    check_and_offer_recalculation(current_plan)

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
    """Check if user is on track and offer recalculation if needed."""
    on_track, info = current_plan.is_on_track()

    if on_track and info['status'] == 'on_track':
        # Exactly on track, no need to recalculate
        return

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

        if get_yes_no("\nWould you like to adjust your plan?", default='y'):
            offer_behind_recalculation(current_plan, info)


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
                # Reduce daily goals
                remaining_words = current_plan.get_remaining_words()
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

                # Calculate remaining writing days
                current_date = today + datetime.timedelta(days=1)  # Start from tomorrow
                total_days = int(current_plan.time) + current_plan.spare_days
                plan_end = current_plan.start_date + datetime.timedelta(days=total_days - 1)
                remaining_days = 0

                while current_date <= plan_end:
                    if not current_plan.is_spare_day(current_date):
                        remaining_days += 1
                    current_date += datetime.timedelta(days=1)

                if remaining_days == 0:
                    display_success("Plan complete! No remaining days.")
                    return

                new_daily = remaining_words / remaining_days

                print(f"\nProposed adjustment:")
                print(f"  Current daily goal: {current_plan.daily:,.0f} words/day")
                print(f"  New daily goal: {new_daily:,.0f} words/day")
                print(f"  Remaining days: {remaining_days}")

                if get_yes_no("Apply this adjustment?", default='y'):
                    current_plan.daily = new_daily
                    current_plan.time = remaining_days + info['days_elapsed']
                    current_plan.invalidate_daily_goals_cache()
                    display_success("Plan adjusted!")

                return

            elif choice == 2:
                # Finish early
                remaining_words = current_plan.get_remaining_words()
                new_days_needed = remaining_words / current_plan.daily

                print(f"\nProposed adjustment:")
                print(f"  Current plan: {current_plan.time:.0f} days")
                print(f"  New plan: {info['days_elapsed'] + new_days_needed:.0f} days")
                print(f"  Finishing early by: {current_plan.time - (info['days_elapsed'] + new_days_needed):.0f} days")

                if get_yes_no("Apply this adjustment?", default='y'):
                    current_plan.time = info['days_elapsed'] + new_days_needed
                    current_plan.invalidate_daily_goals_cache()
                    display_success("Plan adjusted!")

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
                # Increase daily goals
                remaining_words = current_plan.get_remaining_words()
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

                # Calculate remaining writing days
                current_date = today + datetime.timedelta(days=1)  # Start from tomorrow
                total_days = int(current_plan.time) + current_plan.spare_days
                plan_end = current_plan.start_date + datetime.timedelta(days=total_days - 1)
                remaining_days = 0

                while current_date <= plan_end:
                    if not current_plan.is_spare_day(current_date):
                        remaining_days += 1
                    current_date += datetime.timedelta(days=1)

                if remaining_days == 0:
                    display_error("No remaining days to adjust. Plan complete or past deadline.")
                    return

                new_daily = remaining_words / remaining_days

                print(f"\nProposed adjustment:")
                print(f"  Current daily goal: {current_plan.daily:,.0f} words/day")
                print(f"  New daily goal: {new_daily:,.0f} words/day")
                print(f"  Increase: {new_daily - current_plan.daily:,.0f} words/day")
                print(f"  Remaining days: {remaining_days}")

                if get_yes_no("Apply this adjustment?", default='y'):
                    current_plan.daily = new_daily
                    current_plan.time = remaining_days + info['days_elapsed']
                    current_plan.invalidate_daily_goals_cache()
                    display_success("Plan adjusted!")

                return

            elif choice == 2:
                # Extend deadline
                remaining_words = current_plan.get_remaining_words()
                additional_days_needed = remaining_words / current_plan.daily

                print(f"\nProposed adjustment:")
                print(f"  Current plan: {current_plan.time:.0f} days")
                print(f"  New plan: {info['days_elapsed'] + additional_days_needed:.0f} days")
                print(f"  Extension: {additional_days_needed:.0f} days")

                if get_yes_no("Apply this adjustment?", default='y'):
                    current_plan.time = info['days_elapsed'] + additional_days_needed
                    current_plan.invalidate_daily_goals_cache()
                    display_success("Plan adjusted!")

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


def handle_plan_actions(current_plan):
    """Handle the plan actions menu loop."""
    while True:
        display_results(current_plan)
        action = plan_actions_menu()

        if action == 0:
            # Go back to main menu
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

    old_total = current_plan.total

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

    # Recalculate plan based on new weekend settings
    if choice in [1, 2, 3]:
        # Ask user how to adjust the plan
        recalc_choice = ask_recalculation_preference()
        recalculate_plan_with_choice(current_plan, old_total, recalc_choice)


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

    # Ask for start date
    print("\n" + "=" * 50)
    print("PLAN START DATE")
    print("=" * 50)
    print("\nWhen would you like to start writing?")
    print("Enter date in format YYYY-MM-DD (e.g., 2025-10-28)")
    print("Or press Enter for today's date")
    start_date = get_date_input("Start date: ")

    # Create plan from template
    newplan = selected_template.create_plan(start_date=start_date)
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

    # Handle plan actions
    handle_plan_actions(newplan)


def create_new_plan():
    """Handle the creation of a new plan."""
    calc_choice = choose_calculation_method()

    if calc_choice == 0:
        return  # Go back to main menu

    newplan = None

    if calc_choice == 1:
        # Know total words and daily words → calculate time
        print("\n--- Calculate days needed ---")
        total = get_positive_number("Enter your total word goal: ")
        daily = get_positive_number("Enter how many words you can write daily: ")

        newplan = plan.Plan(total=total, daily=daily)
        newplan.calculate_time()

    elif calc_choice == 2:
        # Know daily words and time → calculate total words
        print("\n--- Calculate total words ---")
        daily = get_positive_number("Enter how many words you can write daily: ")
        time = get_positive_number("Enter how many days you have available: ")

        newplan = plan.Plan(daily=daily, time=time)
        newplan.calculate_words()

    elif calc_choice == 3:
        # Know total words and time → calculate daily words
        print("\n--- Calculate daily words needed ---")
        total = get_positive_number("Enter your total word goal: ")
        time = get_positive_number("Enter how many days you have available: ")

        newplan = plan.Plan(total=total, time=time)
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


def main():
    """Main function to run the interactive word planner."""

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


if __name__ == "__main__":
    main()
