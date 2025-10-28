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
        # If plan already has a name, ask if they want to keep it or change it
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
            filepath = plan_storage.save_plan(newplan)
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
    from datetime import timedelta

    total_calendar_days = int(current_plan.time) + current_plan.spare_days

    while True:
        print("\n" + "=" * 50)
        print("MANAGE SPARE DAYS")
        print("=" * 50)
        print("\nSpare days are days with 0 words (holidays, urgent matters, etc.)")
        print(f"Writing days: {current_plan.time:.0f}")
        print(f"Spare days: {current_plan.spare_days}")
        print(f"Total calendar duration: {total_calendar_days} days")

        if current_plan.spare_days > 0:
            print("\nCurrent spare days:")
            sorted_spare = sorted(current_plan.spare_days_dates)

            # Show spare days with dates if start_date is set
            if current_plan.start_date:
                for day_num in sorted_spare:
                    spare_date = current_plan.start_date + timedelta(days=day_num - 1)
                    print(f"  Day {day_num}: {spare_date.strftime('%Y-%m-%d (%A)')}")
            else:
                print(f"  Days: {', '.join(map(str, sorted_spare))}")

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
                # Add spare days
                # Maximum reasonable limit: writing days + 365 (one year of potential spare days)
                max_allowed_day = int(current_plan.time) + 365

                print(f"\nCurrent plan has {int(current_plan.time)} writing days across {total_calendar_days} calendar days")
                print("Enter day numbers separated by commas (e.g., 5,10,15)")
                print("Or enter a range (e.g., 10-15)")
                print(f"Day numbers must be between 1 and {max_allowed_day}")

                days_input = input("Day(s) to mark as spare: ").strip()

                if not days_input:
                    continue

                try:
                    new_spare_days = []

                    # Parse input (handles both comma-separated and ranges)
                    parts = days_input.split(',')
                    for part in parts:
                        part = part.strip()
                        if '-' in part:
                            # Range
                            start, end = part.split('-')
                            start, end = int(start.strip()), int(end.strip())
                            if start > end:
                                start, end = end, start
                            new_spare_days.extend(range(start, end + 1))
                        else:
                            # Single day
                            new_spare_days.append(int(part))

                    # Validate day numbers
                    invalid_days = [d for d in new_spare_days if d < 1 or d > max_allowed_day]
                    if invalid_days:
                        print(f"\n✗ Invalid day numbers: {invalid_days}")
                        print(f"  Days must be between 1 and {max_allowed_day}")
                        continue

                    # Add to spare days (avoid duplicates)
                    added_count = 0
                    for day in new_spare_days:
                        if day not in current_plan.spare_days_dates:
                            current_plan.spare_days_dates.append(day)
                            added_count += 1

                    total_calendar_days = int(current_plan.time) + current_plan.spare_days

                    print(f"\n✓ Added {added_count} spare day(s)")
                    if added_count < len(new_spare_days):
                        print(f"  ({len(new_spare_days) - added_count} were already marked as spare)")
                    print(f"New total calendar duration: {total_calendar_days} days")

                except ValueError:
                    print("\n✗ Invalid input format. Use numbers separated by commas or ranges (e.g., 5,10-15,20)")

            elif choice == 2:
                # Remove spare days
                if current_plan.spare_days == 0:
                    print("\n✗ No spare days to remove")
                    continue

                print("\nEnter day numbers to remove (comma-separated or range)")
                days_input = input("Day(s) to remove from spare: ").strip()

                if not days_input:
                    continue

                try:
                    days_to_remove = []

                    # Parse input
                    parts = days_input.split(',')
                    for part in parts:
                        part = part.strip()
                        if '-' in part:
                            start, end = part.split('-')
                            start, end = int(start.strip()), int(end.strip())
                            if start > end:
                                start, end = end, start
                            days_to_remove.extend(range(start, end + 1))
                        else:
                            days_to_remove.append(int(part))

                    # Remove from spare days
                    removed_count = 0
                    for day in days_to_remove:
                        if day in current_plan.spare_days_dates:
                            current_plan.spare_days_dates.remove(day)
                            removed_count += 1

                    total_calendar_days = int(current_plan.time) + current_plan.spare_days

                    print(f"\n✓ Removed {removed_count} spare day(s)")
                    if removed_count < len(days_to_remove):
                        print(f"  ({len(days_to_remove) - removed_count} were not spare days)")

                except ValueError:
                    print("\n✗ Invalid input format")

            elif choice == 3:
                # Clear all spare days
                if current_plan.spare_days == 0:
                    print("\n✗ No spare days to clear")
                    continue

                if get_yes_no(f"Clear all {current_plan.spare_days} spare days?", default='n'):
                    current_plan.spare_days_dates.clear()
                    total_calendar_days = int(current_plan.time)
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
    print("\nWhat would you like to modify?")
    print("\n1. Total words")
    print("2. Daily words")
    print("3. Writing days")
    print("4. Spare days")
    print("5. Modify two values (third will be calculated)")
    print("0. Cancel")
    print("=" * 50)

    while True:
        try:
            choice = int(input("\nEnter your choice (0-5): "))
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
                print("Please enter a number between 0 and 5.")
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
