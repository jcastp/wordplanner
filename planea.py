#!/usr/bin/python3

"""This is an intended clone for the pacemaker.press site.
It intends to get a plan for daily work on words per day."""

import copy
import sys
import readline  # noqa: F401 (line editing at prompts)
import plan_storage
import plan_manager
import cli
from ui_utils import get_yes_no, get_menu_choice, display_header
import ui_create
import ui_files
import ui_plan_actions
import ui_settings


def initial_menu(current_plan=None):
    """
    Display the initial menu: create new plan or load existing.

    Args:
        current_plan: The current (★) plan, if any: adds "Continue" as option 6
    """
    display_header("WORD COUNT PLANNER")
    print("\nWhat would you like to do?")
    print("\n1. Create a new plan from scratch")
    print("2. Create plan from template")
    print("3. Load an existing plan")
    print("4. Manage multiple plans")
    print("5. Settings")
    last = 5
    if current_plan is not None:
        print(f"6. Continue the current plan: ★ {current_plan.name or 'Unnamed'}")
        last = 6
    print("0. Exit")
    print("=" * 50)

    return get_menu_choice(f"\nEnter your choice (0-{last}): ", 0, last)


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
            ui_files.save_plan_prompt(current_plan, ask=False)
    except (KeyboardInterrupt, EOFError):
        recovered = copy.deepcopy(current_plan)
        recovered.name = f"{current_plan.name or 'plan'} (recovered)"
        try:
            filepath = plan_storage.save_plan(recovered, overwrite_source=False)
            print(f"\nUnsaved changes kept in a new plan: {filepath}")
        except Exception as e:
            print(f"\nCould not save the unsaved changes: {e}")


def main(argv=()):
    """
    Run the word planner: the interactive menus, or a command (see cli.py).

    Args:
        argv: Command-line arguments (none: the menus)

    Returns:
        The exit code (0 for the menus)
    """
    if argv:
        return cli.run(argv)
    try:
        main_menu_loop()
    except (KeyboardInterrupt, EOFError):
        print()
        save_after_interrupt(ui_plan_actions._open_plan)
        print("\nThank you for using Word Count Planner. Happy writing!")
    return 0


def main_menu_loop():
    """The main menu, until the user exits."""
    while True:
        current_plan = plan_manager.get_active_plan()
        choice = initial_menu(current_plan)

        if choice == 0:
            print("\nThank you for using Word Count Planner. Happy writing!")
            break

        elif choice == 1:
            # Create a new plan from scratch
            ui_create.create_new_plan()

        elif choice == 2:
            # Create plan from template
            ui_create.create_plan_from_template()

        elif choice == 3:
            # Load a saved plan
            loaded_plan = ui_files.load_saved_plan()
            if loaded_plan:
                ui_plan_actions.handle_plan_actions(loaded_plan)

        elif choice == 4:
            # Manage multiple plans
            import plan_manager_ui
            plan_manager_ui.manage_plans_menu()

        elif choice == 5:
            # Settings
            ui_settings.settings_menu()

        elif choice == 6:
            # Continue the current plan
            ui_plan_actions.handle_plan_actions(current_plan)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
