#!/usr/bin/python3

"""This is an intended clone for the pacemaker.press site.
It intends to get a plan for daily work on words per day."""

import plan


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

        elif choice == 2:
            # Know daily words and time → calculate total words
            print("\n--- Plan 2: Calculate total words ---")
            daily = get_positive_number("Enter how many words you can write daily: ")
            time = get_positive_number("Enter how many days you have available: ")

            newplan = plan.Plan(daily=daily, time=time)
            newplan.calculate_words()
            display_results(newplan)

        elif choice == 3:
            # Know total words and time → calculate daily words
            print("\n--- Plan 3: Calculate daily words needed ---")
            total = get_positive_number("Enter your total word goal: ")
            time = get_positive_number("Enter how many days you have available: ")

            newplan = plan.Plan(total=total, time=time)
            newplan.calculate_daily()
            display_results(newplan)

        # Ask if user wants to make another calculation
        print("\n")
        continue_choice = input("Would you like to create another plan? (y/n): ").lower()
        if continue_choice != 'y':
            print("\nThank you for using Word Count Planner. Happy writing!")
            break


if __name__ == "__main__":
    main()
