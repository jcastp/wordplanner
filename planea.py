#!/usr/bin/python3

"""This is an intended clone for the pacemaker.press site.
It intends to get a plan for daily work on words per day."""

from datetime import datetime
import readline
import plan
import calendar_view
import plan_storage


def get_yes_no(prompt, default='y'):
    """
    Get a yes/no answer from user with a default value.

    Args:
        prompt: The question to ask
        default: 'y' or 'n' for the default answer (selected with Enter)

    Returns:
        True for yes, False for no
    """
    if default.lower() == 'y':
        options = "[Y/n]"
    else:
        options = "[y/N]"

    while True:
        response = input(f"{prompt} {options}: ").strip().lower()

        if response == "":
            # Use default
            return default.lower() == 'y'
        elif response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no (or press Enter for default).")


def get_positive_number(prompt):
    """Get a positive number from user input with validation."""
    while True:
        try:
            value = float(input(prompt))
            if value <= 0:
                print("Please enter a positive number.")
                continue
            return value
        except ValueError:
            print("Invalid input. Please enter a number.")


def get_date_input(prompt_text="Start date: "):
    """Get and validate a date input from the user."""
    while True:
        date_input = input(prompt_text).strip()

        if date_input == "":
            selected_date = datetime.now()
        else:
            try:
                selected_date = datetime.strptime(date_input, "%Y-%m-%d")
            except ValueError:
                print("Invalid date format. Please use YYYY-MM-DD (e.g., 2025-10-28)")
                continue

        # Check if date is in the past
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        selected_date_normalized = selected_date.replace(hour=0, minute=0, second=0, microsecond=0)

        if selected_date_normalized < today:
            days_ago = (today - selected_date_normalized).days
            print(f"\n⚠ Warning: This date is {days_ago} day(s) in the past.")
            if get_yes_no("Do you want to use this date anyway?", default='n'):
                return selected_date
            else:
                print("Please enter a new date.")
                continue

        return selected_date


def initial_menu():
    """Display the initial menu: create new plan or load existing."""
    print("\n" + "=" * 50)
    print("WORD COUNT PLANNER")
    print("=" * 50)
    print("\nWhat would you like to do?")
    print("\n1. Create a new plan")
    print("2. Load an existing plan")
    print("0. Exit")
    print("=" * 50)

    while True:
        try:
            choice = int(input("\nEnter your choice (0-2): "))
            if choice in [0, 1, 2]:
                return choice
            else:
                print("Please enter a number between 0 and 2.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def choose_writing_pattern():
    """Display pattern selection menu and return pattern choice."""
    print("\n" + "=" * 50)
    print("WRITING PATTERN")
    print("=" * 50)
    print("\nHow would you like to distribute your daily word goals?")
    print("\n1. Flat/Steady - Same daily goal every day (default)")
    print("2. Valley - Start high, ease in middle, finish high")
    print("3. Mountain - Start easy, peak in middle, ease at end")
    print("4. Rising - Gradually increase goals over time")
    print("5. Declining - Gradually decrease goals over time")
    print("6. Random - Varied daily goals within a range")
    print("\n0. Skip (use flat pattern)")
    print("=" * 50)

    while True:
        try:
            choice = int(input("\nEnter your choice (0-6): "))
            if choice in [0, 1, 2, 3, 4, 5, 6]:
                pattern_map = {
                    0: "flat",
                    1: "flat",
                    2: "valley",
                    3: "mountain",
                    4: "rising",
                    5: "declining",
                    6: "random"
                }
                pattern = pattern_map[choice]

                # Get pattern configuration if needed
                pattern_config = {}
                if pattern in ["valley", "mountain"]:
                    print("\nPattern intensity (how extreme the variation):")
                    print("1. Mild (varies between 0.8x and 1.2x average)")
                    print("2. Moderate (varies between 0.7x and 1.5x average) [default]")
                    print("3. Extreme (varies between 0.5x and 2.0x average)")

                    intensity_choice = input("\nEnter your choice (1-3, or Enter for default): ").strip()
                    if intensity_choice == "1":
                        pattern_config = {'peak_multiplier': 1.2, 'valley_multiplier': 0.8}
                    elif intensity_choice == "3":
                        pattern_config = {'peak_multiplier': 2.0, 'valley_multiplier': 0.5}
                    else:
                        pattern_config = {'peak_multiplier': 1.5, 'valley_multiplier': 0.7}

                elif pattern in ["rising", "declining"]:
                    print("\nPattern intensity:")
                    print("1. Mild (varies between 0.8x and 1.2x average)")
                    print("2. Moderate (varies between 0.5x and 1.5x average) [default]")
                    print("3. Extreme (varies between 0.3x and 2.0x average)")

                    intensity_choice = input("\nEnter your choice (1-3, or Enter for default): ").strip()
                    if intensity_choice == "1":
                        if pattern == "rising":
                            pattern_config = {'start_multiplier': 0.8, 'end_multiplier': 1.2}
                        else:
                            pattern_config = {'start_multiplier': 1.2, 'end_multiplier': 0.8}
                    elif intensity_choice == "3":
                        if pattern == "rising":
                            pattern_config = {'start_multiplier': 0.3, 'end_multiplier': 2.0}
                        else:
                            pattern_config = {'start_multiplier': 2.0, 'end_multiplier': 0.3}
                    else:
                        if pattern == "rising":
                            pattern_config = {'start_multiplier': 0.5, 'end_multiplier': 1.5}
                        else:
                            pattern_config = {'start_multiplier': 1.5, 'end_multiplier': 0.5}

                elif pattern == "random":
                    print("\nRandom variation range:")
                    print("1. Mild (varies between 0.8x and 1.2x average)")
                    print("2. Moderate (varies between 0.5x and 1.5x average) [default]")
                    print("3. Extreme (varies between 0.3x and 2.0x average)")

                    intensity_choice = input("\nEnter your choice (1-3, or Enter for default): ").strip()
                    if intensity_choice == "1":
                        pattern_config = {'min_multiplier': 0.8, 'max_multiplier': 1.2}
                    elif intensity_choice == "3":
                        pattern_config = {'min_multiplier': 0.3, 'max_multiplier': 2.0}
                    else:
                        pattern_config = {'min_multiplier': 0.5, 'max_multiplier': 1.5}

                    # Optional seed for reproducibility
                    use_seed = get_yes_no("Use a fixed seed for reproducible randomness?", default='n')
                    if use_seed:
                        import random
                        pattern_config['seed'] = random.randint(1, 1000000)

                return pattern, pattern_config
            else:
                print("Please enter a number between 0 and 6.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def choose_calculation_method():
    """Display calculation method menu and return user choice."""
    print("\n" + "=" * 50)
    print("CALCULATION METHOD")
    print("=" * 50)
    print("\nWhat do you know about your writing project?")
    print("\n1. I know my goal (total words) and daily capacity")
    print("   → Calculate how many days I'll need")
    print("\n2. I know my daily capacity and available time")
    print("   → Calculate total words I'll write")
    print("\n3. I know my goal (total words) and available time")
    print("   → Calculate daily words I need to write")
    print("\n0. Go back")
    print("=" * 50)

    while True:
        try:
            choice = int(input("\nEnter your choice (0-3): "))
            if choice in [0, 1, 2, 3]:
                return choice
            else:
                print("Please enter a number between 0 and 3.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def display_results(newplan):
    """Display the plan results in a formatted way."""
    print("\n" + "-" * 50)
    print("YOUR WRITING PLAN")
    print("-" * 50)
    print(f"Total words: {newplan.total:,.0f} words")
    print(f"Writing days: {newplan.time:.0f} days")
    print(f"Daily goal: {newplan.daily:,.0f} words per day")
    if newplan.spare_days > 0:
        print(f"Spare days: {newplan.spare_days:.0f} days (0 words)")
        total_calendar_days = newplan.time + newplan.spare_days
        print(f"Total calendar duration: {total_calendar_days:.0f} days")
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
                                print(f"\n✓ Plan updated successfully in: {filepath}")
                            else:
                                print(f"\n✓ Plan saved as new file: {filepath}")
                            return True
                        except Exception as e:
                            print(f"\n✗ Error saving plan: {e}")
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
                print(f"\n✓ Plan saved successfully to: {filepath}")
                return True
            except Exception as e:
                print(f"\n✗ Error saving plan: {e}")
                return False
    return False


def plan_actions_menu():
    """Display plan actions menu after creating or loading a plan."""
    print("\n" + "=" * 50)
    print("PLAN ACTIONS")
    print("=" * 50)
    print("\nWhat would you like to do with this plan?")
    print("\n1. Modify plan")
    print("2. View calendar")
    print("3. Save plan")
    print("0. Go back to main menu")
    print("=" * 50)

    while True:
        try:
            choice = int(input("\nEnter your choice (0-3): "))
            if choice in [0, 1, 2, 3]:
                return choice
            else:
                print("Please enter a number between 0 and 3.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def manage_spare_days(current_plan):
    """Interactively manage spare days for the plan."""
    from datetime import timedelta, datetime as dt

    # Check if start_date is set
    if not current_plan.start_date:
        print("\n✗ You must set a start date before managing spare days.")
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
        print("0. Done")
        print("=" * 50)

        try:
            choice = int(input("\nEnter your choice (0-3): "))

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
                            print("\n✗ Invalid range format. Use: YYYY-MM-DD to YYYY-MM-DD")
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
                        print(f"\n✗ Some dates are outside the valid range:")
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

                    print(f"\n✓ Added {added_count} spare day(s)")
                    if added_count < len(new_spare_dates):
                        print(f"  ({len(new_spare_dates) - added_count} were already marked as spare)")

                except ValueError as e:
                    print(f"\n✗ Invalid date format: {e}")
                    print("  Please use YYYY-MM-DD format (e.g., 2025-12-25)")

            elif choice == 2:
                # Remove spare days by date
                if current_plan.spare_days == 0:
                    print("\n✗ No spare days to remove")
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

                    print(f"\n✓ Removed {removed_count} spare day(s)")
                    if removed_count < len(dates_to_remove):
                        print(f"  ({len(dates_to_remove) - removed_count} were not spare days)")

                except ValueError as e:
                    print(f"\n✗ Invalid date format: {e}")

            elif choice == 3:
                # Clear all spare days
                if current_plan.spare_days == 0:
                    print("\n✗ No spare days to clear")
                    continue

                if get_yes_no(f"Clear all {current_plan.spare_days} spare days?", default='n'):
                    current_plan.spare_days_dates.clear()
                    total_calendar_days = int(current_plan.time)
                    plan_end_date = current_plan.start_date + timedelta(days=total_calendar_days - 1)
                    print("\n✓ All spare days cleared")

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
    print("\nWhat would you like to modify?")
    print("\n1. Total words")
    print("2. Daily words")
    print("3. Writing days")
    print("4. Spare days")
    print("5. Writing pattern")
    print("6. Modify two values (third will be calculated)")
    print("0. Cancel")
    print("=" * 50)

    while True:
        try:
            choice = int(input("\nEnter your choice (0-6): "))
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
                print(f"\n✓ Pattern changed to: {pattern}")
                return True

            elif choice == 6:
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

            else:
                print("Please enter a number between 0 and 6.")
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
                    print(f"\n✓ Loaded plan: {loaded_plan.name}")
                    return loaded_plan
                except Exception as e:
                    print(f"\n✗ Error loading plan: {e}")
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
                    # Plan has a saved start date - show menu
                    print("\n" + "-" * 50)
                    print(f"This plan has a saved start date: {newplan.start_date.strftime('%Y-%m-%d')}")

                    # Check if saved date is in the past
                    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    saved_date_normalized = newplan.start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    if saved_date_normalized < today:
                        days_ago = (today - saved_date_normalized).days
                        print(f"⚠ Warning: This date is {days_ago} day(s) in the past.")

                    print("-" * 50)
                    print("\n1. Use saved date")
                    print("2. Enter a new date")
                    print("0. Cancel")
                    print("-" * 50)

                    date_choice_made = False
                    while not date_choice_made:
                        try:
                            date_choice = int(input("\nEnter your choice (0-2): "))
                            if date_choice == 0:
                                return
                            elif date_choice == 1:
                                start_date = newplan.start_date
                                date_choice_made = True
                            elif date_choice == 2:
                                print("\nEnter new start date (YYYY-MM-DD, e.g., 2025-10-28)")
                                print("Or press Enter for today's date")
                                start_date = get_date_input("Start date: ")
                                date_choice_made = True
                            else:
                                print("Please enter a number between 0 and 2.")
                        except ValueError:
                            print("Invalid input. Please enter a number.")
                else:
                    # No saved start date - ask for one
                    print("\nWhen would you like to start writing?")
                    print("Enter date in format YYYY-MM-DD (e.g., 2025-10-28)")
                    print("Or press Enter for today's date")
                    start_date = get_date_input("Start date: ")

                # Save the start_date to the plan object
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


def handle_plan_actions(current_plan):
    """Handle the plan actions menu loop."""
    while True:
        display_results(current_plan)
        action = plan_actions_menu()

        if action == 0:
            # Go back to main menu
            break

        elif action == 1:
            # Modify plan
            modified = modify_plan(current_plan)
            if modified:
                print("\n✓ Plan modified successfully!")
            # Loop continues to show updated results

        elif action == 2:
            # View calendar
            show_calendar_options(current_plan)

        elif action == 3:
            # Save plan
            save_plan_prompt(current_plan)


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
            print(f"\n✓ Using {pattern} pattern")

        handle_plan_actions(newplan)


def main():
    """Main function to run the interactive word planner."""

    while True:
        choice = initial_menu()

        if choice == 0:
            print("\nThank you for using Word Count Planner. Happy writing!")
            break

        elif choice == 1:
            # Create a new plan
            create_new_plan()

        elif choice == 2:
            # Load a saved plan
            loaded_plan = load_saved_plan()
            if loaded_plan:
                handle_plan_actions(loaded_plan)


if __name__ == "__main__":
    main()
