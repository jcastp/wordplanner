"""
Settings: the save directory, defaults for new plans, the first day of the
week, the date format and colors. Values are stored by user_preferences.
"""

from datetime import datetime
from pathlib import Path
import plan_storage
import config
import user_preferences
from ui_utils import (
    get_yes_no,
    get_menu_choice,
    display_header,
    display_success,
    display_error,
    display_warning,
    get_positive_number,
)
from pattern_utils import choose_writing_pattern
import formatting


def offer_to_move_plans(old_plans_dir):
    """
    After the save directory changed, offer to move the plans in the old one (S4).

    Plans are only listed from the current directory, so plans left behind
    would disappear from the app (they stay on disk).
    """
    new_plans_dir = plan_storage.get_plans_directory()
    if not old_plans_dir.is_dir() or old_plans_dir.resolve() == new_plans_dir.resolve():
        return
    count = len(list(old_plans_dir.glob("*.json")))
    if count == 0:
        return

    print(f"\n{count} plan(s) are in the previous folder: {old_plans_dir}")
    print("Only plans in the current folder are listed in the app.")
    if not get_yes_no(f"Move them to {new_plans_dir}?", default='y'):
        print(f"They stay in {old_plans_dir}.")
        return

    moved, skipped = plan_storage.move_plans(old_plans_dir, new_plans_dir)
    display_success(f"Moved {moved} plan(s) to {new_plans_dir}")
    if skipped:
        display_warning(f"{len(skipped)} plan(s) not moved: a file with the same name "
                        f"is already there ({', '.join(skipped[:3])}{'...' if len(skipped) > 3 else ''})")


def configure_save_directory():
    """Configure the custom save directory for plans and exports."""
    display_header("CONFIGURE SAVE DIRECTORY")
    old_plans_dir = plan_storage.get_plans_directory()

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
        offer_to_move_plans(old_plans_dir)

    elif choice == 2:
        # Reset to default
        if current_custom_dir:
            if get_yes_no("\nAre you sure you want to reset to the default directory?", default='n'):
                user_preferences.set_custom_save_directory(None)
                default_dir = Path.home() / config.SAVE_DIRECTORY
                display_success(f"Reset to default directory: {default_dir}")
                offer_to_move_plans(old_plans_dir)
        else:
            display_warning("Already using default directory.")


def describe_weekend_default():
    """The default weekend setting from Settings, in words."""
    mode = user_preferences.get_preference('default_weekend_mode')
    if mode == "spare":
        return "no writing on weekends"
    if mode == "different":
        return f"{user_preferences.get_preference('default_weekend_daily'):,.0f} words/day on weekends"
    return "same as weekdays"


def describe_pattern_default():
    pattern = user_preferences.get_preference('default_pattern')
    return "flat (same goal every day)" if pattern == "flat" else pattern


def configure_new_plan_defaults():
    """Default writing pattern and weekend setting for plans created from scratch."""
    display_header("DEFAULTS FOR NEW PLANS")
    print("\nNew plans created from scratch start with these (you can still change")
    print("them while creating the plan). Templates keep their own suggestions.")
    print(f"\n1. Writing pattern: {describe_pattern_default()}")
    print(f"2. Weekends: {describe_weekend_default()}")
    print("0. Back")
    print("=" * 50)

    choice = get_menu_choice("\nEnter your choice (0-2): ", 0, 2)
    if choice == 1:
        pattern, pattern_config = choose_writing_pattern()
        user_preferences.set_preference('default_pattern', pattern)
        user_preferences.set_preference('default_pattern_config', pattern_config)
        display_success(f"Default writing pattern: {describe_pattern_default()}")
    elif choice == 2:
        print("\n1. Same as weekdays")
        print("2. A different goal on weekends")
        print("3. No writing on weekends")
        mode = {1: "same", 2: "different", 3: "spare"}[get_menu_choice("\nEnter your choice (1-3): ", 1, 3)]
        if mode == "different":
            words = get_positive_number("Weekend daily goal: ", max_value=config.MAX_DAILY_WORDS)
            user_preferences.set_preference('default_weekend_daily', words)
        user_preferences.set_preference('default_weekend_mode', mode)
        display_success(f"Default weekends: {describe_weekend_default()}")


def describe_first_weekday():
    return "Sunday" if user_preferences.get_preference('first_weekday') == 6 else "Monday"


def configure_first_weekday():
    """Monday or Sunday as the first column of the monthly calendar."""
    display_header("FIRST DAY OF THE WEEK")
    print("\nThe first column of the monthly calendar.")
    print("\n1. Monday")
    print("2. Sunday")
    print("0. Back")
    choice = get_menu_choice("\nEnter your choice (0-2): ", 0, 2)
    if choice:
        user_preferences.set_preference('first_weekday', 0 if choice == 1 else 6)
        display_success(f"Weeks start on {describe_first_weekday()}")


def configure_date_format():
    """How dates written as numbers are shown, and typed."""
    display_header("DATE FORMAT")
    print("\nHow dates are shown on screen, in the Markdown export and in commands.")
    print("Plan files, CSV and iCal always use YYYY-MM-DD, and typing a date as")
    print("YYYY-MM-DD always works.\n")
    names = list(formatting.DATE_FORMATS)
    sample = datetime(2026, 11, 5)
    current = user_preferences.get_preference('date_format')
    for number, name in enumerate(names, 1):
        strftime = formatting.DATE_FORMATS[name][0]
        marker = "  (current)" if name == current else ""
        print(f"{number}. {sample.strftime(strftime)}{marker}")
    print("0. Back")
    choice = get_menu_choice(f"\nEnter your choice (0-{len(names)}): ", 0, len(names))
    if choice:
        user_preferences.set_preference('date_format', names[choice - 1])
        display_success(f"Dates are now shown as {formatting.format_date(sample)}; "
                        f"type them as {formatting.date_hint()}")


def configure_colors():
    """Turn colors in tables, the calendar and graphs on or off."""
    on = user_preferences.get_preference('colors')
    print(f"\nColors are {'on' if on else 'off'}. With colors off, tables, the calendar")
    print("and graphs are plain; symbols (✓ ~ ✗) and the TODAY marker stay.")
    if get_yes_no(f"Turn colors {'off' if on else 'on'}?", default='y'):
        user_preferences.set_preference('colors', not on)
        display_success(f"Colors {'off' if on else 'on'}")


def settings_menu():
    """Display the settings menu."""
    while True:
        display_header("SETTINGS")
        print("\nWhat would you like to configure?")
        print("\n1. Save directory location")
        print(f"2. Defaults for new plans (pattern: {describe_pattern_default()}; "
              f"weekends: {describe_weekend_default()})")
        print(f"3. First day of the week ({describe_first_weekday()})")
        print(f"4. Date format ({formatting.format_date(datetime(2026, 11, 5))})")
        print(f"5. Colors ({'on' if user_preferences.get_preference('colors') else 'off'})")
        print("0. Back to main menu")
        print("=" * 50)

        choice = get_menu_choice("\nEnter your choice (0-5): ", 0, 5)

        if choice == 0:
            break
        elif choice == 1:
            configure_save_directory()
        elif choice == 2:
            configure_new_plan_defaults()
        elif choice == 3:
            configure_first_weekday()
        elif choice == 4:
            configure_date_format()
        elif choice == 5:
            configure_colors()
