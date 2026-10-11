"""
Settings: the save directory.

Split out of planea.py (issues-program.org Q3).
"""

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
)


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
