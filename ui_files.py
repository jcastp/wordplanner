"""
Save, load and export screens.

Split out of planea.py (issues-program.org Q3).
"""

import plan_storage
import plan_export
from ui_utils import get_yes_no, get_menu_choice, display_success, display_error
from formatting import format_date


def save_plan_prompt(newplan, ask=True):
    """
    Save the plan, asking where (overwrite or new file) and for a name if needed.

    Args:
        newplan: The plan to save
        ask: First ask whether to save at all (False when the caller already asked)

    Returns:
        True if the plan was saved
    """
    if not ask or get_yes_no("\nWould you like to save this plan?", default='y'):
        # Check if this plan was loaded from a file
        if newplan.source_file:
            print(f"\nThis plan was loaded from: {newplan.source_file.name}")
            print("\nHow would you like to save?")
            print("1. Overwrite the original file")
            print("2. Save as a new file (with timestamp)")
            print("0. Cancel")

            choice = get_menu_choice("\nEnter your choice (0-2): ", 0, 2)
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
                    was_active = newplan.is_active
                    filepath = plan_storage.save_plan(newplan, overwrite_source=overwrite)
                    if overwrite:
                        display_success(f"Plan updated successfully in: {filepath}")
                    else:
                        display_success(f"Plan saved as new file: {filepath}")
                        if was_active and not newplan.is_active:
                            print("  The original stays your current plan (★). "
                                  "Use 'Manage multiple plans' to switch.")
                    return True
                except Exception as e:
                    display_error(f"Error saving plan: {e}")
                    return False
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
        created_str = f"{format_date(created)} {created.strftime('%H:%M')}" if created else "Unknown"

        print(f"{idx}. {plan_name}")
        print(f"   {total:,.0f} words | {daily:,.0f}/day | {time:.0f} days")
        print(f"   Created: {created_str}\n")

    print("0. Cancel")
    print("=" * 50)

    choice = get_menu_choice("\nSelect a plan to load (0 to cancel): ", 0, len(saved_plans))
    if choice == 0:
        return None
    filepath = saved_plans[choice - 1]['path']

    try:
        loaded_plan = plan_storage.load_plan(filepath)
        display_success(f"Loaded plan: {loaded_plan.name}")
        return loaded_plan
    except Exception as e:
        display_error(f"Error loading plan: {e}")
        input("\nPress Enter to continue...")
        return None


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

    choice = get_menu_choice("\nEnter your choice (0-4): ", 0, 4)

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
