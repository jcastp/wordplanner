#!/usr/bin/python3

"""This is an intended clone for the pacemaker.press site.
It intends to get a plan for daily work on words per day."""

from datetime import datetime
import plan
import calendar_view


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


def show_menu():
    """Display the main menu and return user choice."""
    print("\n" + "=" * 50)
    print("WORD COUNT PLANNER")
    print("=" * 50)
    print("\nWhat do you know about your writing project?")
    print("\n1. I know my goal (total words) and daily capacity")
    print("   → Calculate how many days I'll need")
    print("\n2. I know my daily capacity and available time")
    print("   → Calculate total words I'll write")
    print("\n3. I know my goal (total words) and available time")
    print("   → Calculate daily words I need to write")
    print("\n0. Exit")
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


def main():
    """Main function to run the interactive word planner."""

    while True:
        choice = show_menu()

        if choice == 0:
            print("\nThank you for using Word Count Planner. Happy writing!")
            break

        elif choice == 1:
            # Know total words and daily words → calculate time
            print("\n--- Plan 1: Calculate days needed ---")
            total = get_positive_number("Enter your total word goal: ")
            daily = get_positive_number("Enter how many words you can write daily: ")

            newplan = plan.Plan(total=total, daily=daily)
            newplan.calculate_time()
            display_results(newplan)
            show_calendar_options(newplan)

        elif choice == 2:
            # Know daily words and time → calculate total words
            print("\n--- Plan 2: Calculate total words ---")
            daily = get_positive_number("Enter how many words you can write daily: ")
            time = get_positive_number("Enter how many days you have available: ")

            newplan = plan.Plan(daily=daily, time=time)
            newplan.calculate_words()
            display_results(newplan)
            show_calendar_options(newplan)

        elif choice == 3:
            # Know total words and time → calculate daily words
            print("\n--- Plan 3: Calculate daily words needed ---")
            total = get_positive_number("Enter your total word goal: ")
            time = get_positive_number("Enter how many days you have available: ")

            newplan = plan.Plan(total=total, time=time)
            newplan.calculate_daily()
            display_results(newplan)
            show_calendar_options(newplan)

        # Ask if user wants to make another calculation
        print("\n")
        continue_choice = input("Would you like to create another plan? (y/n): ").lower()
        if continue_choice != 'y':
            print("\nThank you for using Word Count Planner. Happy writing!")
            break


if __name__ == "__main__":
    main()
