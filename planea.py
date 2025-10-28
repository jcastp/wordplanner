#!/usr/bin/python3

"""This is an intended clone for the pacemaker.press site.
It intends to get a plan for daily work on words per day."""

from datetime import datetime
import readline
import plan
import calendar_view
import plan_storage


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
    print(f"Time needed: {newplan.time:.1f} days")
    print(f"Daily goal: {newplan.daily:,.1f} words per day")
    print("-" * 50)


def save_plan_prompt(newplan):
    """Ask user if they want to save the plan."""
    save = input("\nWould you like to save this plan? (y/n): ").lower()
    if save == 'y':
        plan_name = input("Enter a name for this plan: ").strip()
        if not plan_name:
            print("No name provided, plan not saved.")
            return

        try:
            newplan.name = plan_name
            filepath = plan_storage.save_plan(newplan)
            print(f"\n✓ Plan saved successfully to: {filepath}")
        except Exception as e:
            print(f"\n✗ Error saving plan: {e}")


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
                                date_input = input("Start date: ").strip()
                                if date_input == "":
                                    start_date = datetime.now()
                                else:
                                    try:
                                        start_date = datetime.strptime(date_input, "%Y-%m-%d")
                                    except ValueError:
                                        print("Invalid format, using today's date")
                                        start_date = datetime.now()
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

                    date_input = input("Start date: ").strip()
                    if date_input == "":
                        start_date = datetime.now()
                    else:
                        try:
                            start_date = datetime.strptime(date_input, "%Y-%m-%d")
                        except ValueError:
                            print("Invalid format, using today's date")
                            start_date = datetime.now()

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


def create_new_plan():
    """Handle the creation of a new plan."""
    calc_choice = choose_calculation_method()

    if calc_choice == 0:
        return  # Go back to main menu

    if calc_choice == 1:
        # Know total words and daily words → calculate time
        print("\n--- Calculate days needed ---")
        total = get_positive_number("Enter your total word goal: ")
        daily = get_positive_number("Enter how many words you can write daily: ")

        newplan = plan.Plan(total=total, daily=daily)
        newplan.calculate_time()
        display_results(newplan)
        show_calendar_options(newplan)
        save_plan_prompt(newplan)

    elif calc_choice == 2:
        # Know daily words and time → calculate total words
        print("\n--- Calculate total words ---")
        daily = get_positive_number("Enter how many words you can write daily: ")
        time = get_positive_number("Enter how many days you have available: ")

        newplan = plan.Plan(daily=daily, time=time)
        newplan.calculate_words()
        display_results(newplan)
        show_calendar_options(newplan)
        save_plan_prompt(newplan)

    elif calc_choice == 3:
        # Know total words and time → calculate daily words
        print("\n--- Calculate daily words needed ---")
        total = get_positive_number("Enter your total word goal: ")
        time = get_positive_number("Enter how many days you have available: ")

        newplan = plan.Plan(total=total, time=time)
        newplan.calculate_daily()
        display_results(newplan)
        show_calendar_options(newplan)
        save_plan_prompt(newplan)


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
                display_results(loaded_plan)
                show_calendar_options(loaded_plan)


if __name__ == "__main__":
    main()
