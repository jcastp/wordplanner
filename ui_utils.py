"""
UI Utilities Module

This module provides common user interface functions for input validation,
menu display, and user interaction across the planeapalabras application.
"""

from datetime import datetime
import config


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


def get_positive_number(prompt, max_value=None):
    """
    Get a positive number from user input with validation.

    Args:
        prompt: The prompt to display to the user
        max_value: Optional maximum allowed value

    Returns:
        float: A positive number entered by the user
    """
    while True:
        try:
            user_input = input(prompt).strip()
            if not user_input:
                print("Error: Input cannot be empty. Please enter a number.")
                continue

            value = float(user_input)

            if value < 0:
                print(f"Error: Cannot use negative numbers. You entered: {value}")
                continue
            elif value == 0:
                print("Error: Value must be greater than zero.")
                continue
            elif max_value is not None and value > max_value:
                print(f"Error: Value cannot exceed {max_value:,.0f}. You entered: {value:,.0f}")
                continue

            return value
        except ValueError as e:
            print(f"Error: Invalid input '{user_input}'. Please enter a valid number.")
        except (KeyboardInterrupt, EOFError):
            print("\nInput cancelled by user.")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}. Please try again.")


def get_date_input(prompt_text="Start date: "):
    """
    Get and validate a date input from the user.

    Args:
        prompt_text: The prompt to display (default: "Start date: ")

    Returns:
        datetime: A validated datetime object
    """
    while True:
        date_input = input(prompt_text).strip()

        if date_input == "":
            selected_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
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
            print(f"\nWarning: This date is {days_ago} day(s) in the past.")
            if get_yes_no("Do you want to use this date anyway?", default='n'):
                return selected_date
            else:
                print("Please enter a new date.")
                continue

        return selected_date


def get_menu_choice(prompt, min_value, max_value):
    """
    Get a menu choice from the user within a valid range.

    Args:
        prompt: The prompt to display
        min_value: Minimum valid choice (inclusive)
        max_value: Maximum valid choice (inclusive)

    Returns:
        int: The user's validated choice
    """
    while True:
        try:
            user_input = input(prompt).strip()
            if not user_input:
                print("Error: Input cannot be empty. Please enter a number.")
                continue

            choice = int(user_input)
            if min_value <= choice <= max_value:
                return choice
            else:
                print(f"Error: Invalid choice. Please enter a number between {min_value} and {max_value}.")
        except ValueError:
            print(f"Error: Invalid input '{user_input}'. Please enter a valid number.")
        except (KeyboardInterrupt, EOFError):
            print("\nInput cancelled by user.")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}. Please try again.")


def display_header(title, width=config.DEFAULT_HEADER_WIDTH):
    """
    Display a formatted header.

    Args:
        title: The title text to display
        width: Width of the header (default: 50)
    """
    print("\n" + "=" * width)
    print(title)
    print("=" * width)


def display_section(text, width=config.DEFAULT_SECTION_WIDTH):
    """
    Display a formatted section separator.

    Args:
        text: The section text to display
        width: Width of the separator (default: 50)
    """
    print("\n" + "-" * width)
    print(text)
    print("-" * width)


def display_menu(title, options, footer_text="Enter your choice", show_exit=True):
    """
    Display a menu with options and get user's choice.

    Args:
        title: Menu title
        options: List of tuples (number, text) for menu items
        footer_text: Text to show before input prompt (default: "Enter your choice")
        show_exit: Whether to show "0. Exit/Go back" option (default: True)

    Returns:
        int: The user's choice
    """
    display_header(title)

    for num, text in options:
        print(f"\n{num}. {text}")

    if show_exit:
        print("\n0. Exit" if options[0][0] == 1 and "main" in title.lower() else "\n0. Go back")

    print("=" * 50)

    min_val = 0 if show_exit else min(num for num, _ in options)
    max_val = max(num for num, _ in options)

    prompt = f"\n{footer_text} ({min_val}-{max_val}): "
    return get_menu_choice(prompt, min_val, max_val)


def get_integer_input(prompt, min_value=None, max_value=None, allow_negative=False):
    """
    Get an integer input from the user with optional range validation.

    Args:
        prompt: The prompt to display
        min_value: Minimum valid value (optional)
        max_value: Maximum valid value (optional)
        allow_negative: Whether to allow negative numbers (default: False)

    Returns:
        int: The validated integer
    """
    while True:
        try:
            user_input = input(prompt).strip()
            if not user_input:
                print("Error: Input cannot be empty. Please enter an integer.")
                continue

            value = int(user_input)

            if not allow_negative and value < 0:
                print(f"Error: Cannot use negative numbers. You entered: {value}")
                continue

            if min_value is not None and value < min_value:
                print(f"Error: Value must be at least {min_value}. You entered: {value}")
                continue

            if max_value is not None and value > max_value:
                print(f"Error: Value cannot exceed {max_value}. You entered: {value}")
                continue

            return value
        except ValueError:
            print(f"Error: Invalid input '{user_input}'. Please enter a valid integer.")
        except (KeyboardInterrupt, EOFError):
            print("\nInput cancelled by user.")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}. Please try again.")


def get_string_input(prompt, allow_empty=False):
    """
    Get a string input from the user.

    Args:
        prompt: The prompt to display
        allow_empty: Whether to allow empty strings (default: False)

    Returns:
        str: The user's input
    """
    while True:
        value = input(prompt).strip()

        if not allow_empty and not value:
            print("Input cannot be empty. Please try again.")
            continue

        return value


def confirm_action(action_description):
    """
    Ask user to confirm an action.

    Args:
        action_description: Description of the action to confirm

    Returns:
        bool: True if user confirms, False otherwise
    """
    return get_yes_no(f"\nConfirm: {action_description}?", default='n')


def display_success(message):
    """
    Display a success message.

    Args:
        message: The success message to display
    """
    print(f"\n✓ {message}")


def display_error(message):
    """
    Display an error message.

    Args:
        message: The error message to display
    """
    print(f"\n✗ {message}")


def display_warning(message):
    """
    Display a warning message.

    Args:
        message: The warning message to display
    """
    print(f"\n⚠ {message}")


def display_info(message):
    """
    Display an informational message.

    Args:
        message: The info message to display
    """
    print(f"\nℹ {message}")
