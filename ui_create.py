"""
Creating plans: from scratch and from templates.

Split out of planea.py (issues-program.org Q3).
"""

import copy
import plan
import plan_templates
import config
from ui_utils import (
    get_yes_no,
    get_positive_number,
    get_date_input,
    get_menu_choice,
    display_header,
    display_success,
    display_error,
)
from pattern_utils import choose_writing_pattern, get_pattern_intensity_config
import ui_modify
import ui_plan_actions
import user_preferences
import ui_settings
from formatting import date_hint, format_date


def choose_calculation_method():
    """Display calculation method menu and return user choice."""
    display_header("CALCULATION METHOD")
    print("\nWhat do you know about your writing project?")
    print("\n1. I know my goal (total words) and daily capacity")
    print("   → Calculate how many days I'll need")
    print("\n2. I know my daily capacity and available time")
    print("   → Calculate total words I'll write")
    print("\n3. I know my goal (total words) and available time")
    print("   → Calculate daily words I need to write")
    print("\n0. Go back")
    print("=" * 50)

    return get_menu_choice("\nEnter your choice (0-3): ", 0, 3)


def ask_for_pre_existing_words_count(total_goal=None):
    """
    Ask user if they have words already written for this project.
    Returns the word count without recording it yet.

    Args:
        total_goal: Optional total goal to check against

    Returns:
        Number of pre-existing words, or 0 if none
    """
    print("\n" + "=" * 50)
    print("PRE-EXISTING WORDS")
    print("=" * 50)
    print("\nDo you have words already written for this project?")
    if total_goal:
        print(f"(Your total goal is {total_goal:,.0f} words)")
    print("(Pre-existing words will be subtracted when calculating your plan)")

    if not get_yes_no("\nHave you already written some words?", default='n'):
        return 0

    while True:
        words_written = get_positive_number("\nHow many words have you already written? ", max_value=config.MAX_WORDS)

        if words_written <= 0:
            display_error("Word count must be positive")
            continue

        # Check if it exceeds the total goal
        if total_goal and words_written >= total_goal:
            print(f"\n⚠ Warning: You've already written {words_written:,.0f} words")
            print(f"  This equals or exceeds your goal of {total_goal:,.0f} words!")
            print(f"  You may have already completed your goal!")

            if get_yes_no("Continue anyway?", default='n'):
                return words_written
            else:
                continue

        # Show impact
        if total_goal:
            remaining = total_goal - words_written
            completion_pct = (words_written / total_goal) * 100

            print(f"\n✓ Pre-existing words: {words_written:,.0f}")
            print(f"  Progress: {completion_pct:.1f}% of goal")
            print(f"  Remaining to write: {remaining:,.0f} words")

        if get_yes_no("\nConfirm this word count?", default='y'):
            return words_written


def create_plan_from_template():
    """Create a plan from a pre-defined template."""
    print("\n" + "=" * 50)
    print("CREATE FROM TEMPLATE")
    print("=" * 50)

    # Get templates by category
    categories = plan_templates.list_templates_by_category()
    all_templates = plan_templates.get_all_templates()

    # Display templates by category
    template_list = []
    option_num = 1

    for category, template_keys in categories.items():
        print(f"\n{category}:")
        for key in template_keys:
            template = all_templates[key]
            print(f"  {option_num}. {template}")
            print(f"     {template.description}")
            template_list.append((key, template))
            option_num += 1

    print(f"\n0. Cancel")
    print("=" * 50)

    # Get user choice
    choice = get_menu_choice(f"\nSelect a template (0-{len(template_list)}): ", 0, len(template_list))
    if choice == 0:
        return  # Cancel
    template_key, selected_template = template_list[choice - 1]

    # Show template details
    print("\n" + "=" * 50)
    print(f"TEMPLATE: {selected_template.name}")
    print("=" * 50)
    print(f"Description: {selected_template.description}")
    print(f"Total words: {selected_template.total:,.0f}")
    if selected_template.planned_days():
        print(f"Duration: {plan_templates.days_text(selected_template.planned_days())}")
        print(f"Daily goal: {selected_template.planned_daily():,.0f} words/day")
    if selected_template.suggested_pattern:
        print(f"Suggested pattern: {selected_template.suggested_pattern}")
    if selected_template.suggested_weekend_mode:
        print(f"Suggested weekend mode: {selected_template.suggested_weekend_mode}")

    # Ask if user wants to customize
    if not get_yes_no("\nUse this template as-is?", default='y'):
        print("\n" + "=" * 50)
        print("CUSTOMIZE TEMPLATE")
        print("=" * 50)

        # Allow customization
        if get_yes_no("Change total word count?", default='n'):
            new_total = get_positive_number("Enter total words: ", max_value=config.MAX_WORDS)
            selected_template.total = new_total

        if selected_template.time and get_yes_no("Change duration (days)?", default='n'):
            new_time = get_positive_number("Enter number of days: ", max_value=config.MAX_DAYS)
            selected_template.time = new_time
            selected_template.daily = None  # Will be recalculated

        elif selected_template.daily and get_yes_no("Change daily goal?", default='n'):
            new_daily = get_positive_number("Enter daily words: ", max_value=config.MAX_DAILY_WORDS)
            selected_template.daily = new_daily
            selected_template.time = None  # Will be recalculated

    # Ask about pre-existing words before creating the plan
    pre_existing_words = ask_for_pre_existing_words_count(total_goal=selected_template.total)

    if pre_existing_words >= selected_template.total:
        display_success("You've already met or exceeded this goal!")
        print(f"  Goal: {selected_template.total:,.0f} words")
        print(f"  Already written: {pre_existing_words:,.0f} words")
        input("\nPress Enter to continue...")
        return

    # Ask for start date
    print("\n" + "=" * 50)
    print("PLAN START DATE")
    print("=" * 50)
    print("\nWhen would you like to start writing?")
    print(f"Enter date in format {date_hint()}")
    print("Or press Enter for today's date")
    start_date = get_date_input("Start date: ")

    # Create plan from template
    newplan = selected_template.create_plan(start_date=start_date,
                                            preexisting_words=int(pre_existing_words))
    newplan.name = selected_template.name

    display_success(f"Created plan from template: {selected_template.name}")
    print(f"  Start date: {format_date(start_date)}")

    # Apply suggested pattern if available
    if selected_template.suggested_pattern:
        if get_yes_no(f"\nApply suggested '{selected_template.suggested_pattern}' pattern?", default='y'):
            newplan.pattern = selected_template.suggested_pattern
            # Same intensity choices (and random seed) as a pattern chosen by hand
            newplan.pattern_config = get_pattern_intensity_config(newplan.pattern)

            print(f"✓ Applied {newplan.pattern} pattern")

    # Apply suggested weekend mode if available
    if selected_template.suggested_weekend_mode and selected_template.suggested_weekend_mode != 'same':
        if get_yes_no(f"\nConfigure weekend settings as suggested?", default='y'):
            before = copy.deepcopy(newplan)
            if selected_template.suggested_weekend_mode == 'different':
                newplan.weekend_mode = 'different'
                # Suggest 1.5x the daily goal for weekends
                suggested_weekend_goal = int(newplan.daily * 1.5)
                print(f"\nSuggested weekend goal: {suggested_weekend_goal:,.0f} words/day")
                if get_yes_no("Use this weekend goal?", default='y'):
                    newplan.weekend_daily = suggested_weekend_goal
                else:
                    weekend_goal = get_positive_number("Enter weekend daily goal: ", max_value=config.MAX_DAILY_WORDS)
                    newplan.weekend_daily = weekend_goal
                print(f"✓ Weekend mode: different ({newplan.weekend_daily:,.0f} words/day)")
            elif selected_template.suggested_weekend_mode == 'spare':
                newplan.weekend_mode = 'spare'
                print("✓ Weekend mode: spare (no writing on weekends)")
            ui_modify.offer_plan_adjustment(newplan, before)

    # Handle plan actions
    ui_plan_actions.handle_plan_actions(newplan)


def create_new_plan():
    """Handle the creation of a new plan."""
    calc_choice = choose_calculation_method()

    if calc_choice == 0:
        return  # Go back to main menu

    newplan = None
    pre_existing_words = 0

    if calc_choice == 1:
        # Know total words and daily words → calculate time
        print("\n--- Calculate days needed ---")
        total = get_positive_number("Enter your total word goal: ", max_value=config.MAX_WORDS)

        # Ask about pre-existing words
        pre_existing_words = ask_for_pre_existing_words_count(total_goal=total)

        daily = get_positive_number("Enter how many words you can write daily: ", max_value=config.MAX_DAILY_WORDS)

        if pre_existing_words >= total:
            display_success("You've already met or exceeded your goal!")
            print(f"  Goal: {total:,.0f} words")
            print(f"  Already written: {pre_existing_words:,.0f} words")
            input("\nPress Enter to continue...")
            return

        # Time is calculated for the words still to write
        newplan = plan.Plan(total=total, daily=daily, preexisting_words=int(pre_existing_words))
        newplan.calculate_time()

    elif calc_choice == 2:
        # Know daily words and time → calculate total words
        print("\n--- Calculate total words ---")
        daily = get_positive_number("Enter how many words you can write daily: ", max_value=config.MAX_DAILY_WORDS)
        time = get_positive_number("Enter how many days you have available: ", max_value=config.MAX_DAYS)

        # Ask about pre-existing words (no total yet to check against)
        pre_existing_words = ask_for_pre_existing_words_count()

        # Total = daily × time + pre-existing words
        newplan = plan.Plan(daily=daily, time=time, preexisting_words=int(pre_existing_words))
        newplan.calculate_words()

    elif calc_choice == 3:
        # Know total words and time → calculate daily words
        print("\n--- Calculate daily words needed ---")
        total = get_positive_number("Enter your total word goal: ", max_value=config.MAX_WORDS)

        # Ask about pre-existing words
        pre_existing_words = ask_for_pre_existing_words_count(total_goal=total)

        time = get_positive_number("Enter how many days you have available: ", max_value=config.MAX_DAYS)

        if pre_existing_words >= total:
            display_success("You've already met or exceeded your goal!")
            print(f"  Goal: {total:,.0f} words")
            print(f"  Already written: {pre_existing_words:,.0f} words")
            input("\nPress Enter to continue...")
            return

        # Daily is calculated for the words still to write
        newplan = plan.Plan(total=total, time=time, preexisting_words=int(pre_existing_words))
        newplan.calculate_daily()

    if newplan:
        # Writing pattern: offer the default from Settings first, if there is one
        default_pattern = user_preferences.get_preference('default_pattern')
        if default_pattern != "flat" and get_yes_no(
                f"\nUse your default writing pattern ({default_pattern})?", default='y'):
            newplan.pattern = default_pattern
            newplan.pattern_config = dict(user_preferences.get_preference('default_pattern_config'))
            display_success(f"Using {default_pattern} pattern")
        elif get_yes_no("\nWould you like to use a variable writing pattern?", default='n'):
            pattern, pattern_config = choose_writing_pattern()
            newplan.pattern = pattern
            newplan.pattern_config = pattern_config
            display_success(f"Using {pattern} pattern")

        # Ask for start date
        print("\n" + "=" * 50)
        print("PLAN START DATE")
        print("=" * 50)
        print("\nWhen would you like to start writing?")
        print(f"Enter date in format {date_hint()}")
        print("Or press Enter for today's date")
        start_date = get_date_input("Start date: ")
        newplan.start_date = start_date
        display_success(f"Plan starts on: {format_date(start_date)}")

        # Weekends: offer the default from Settings first, if there is one
        default_weekend = user_preferences.get_preference('default_weekend_mode')
        if default_weekend != "same" and get_yes_no(
                f"\nUse your default weekend setting ({ui_settings.describe_weekend_default()})?", default='y'):
            newplan.weekend_mode = default_weekend
            if default_weekend == "different":
                newplan.weekend_daily = user_preferences.get_preference('default_weekend_daily')
            # Keep the two values that were typed: recalculate the third
            recalculate = {1: newplan.calculate_time, 2: newplan.calculate_words,
                           3: newplan.calculate_daily}[calc_choice]
            recalculate()
            display_success(f"Weekends: {ui_settings.describe_weekend_default()}")
        elif get_yes_no("\nWould you like to configure weekend-specific settings?", default='n'):
            ui_modify.configure_weekend_settings(newplan)

        ui_plan_actions.handle_plan_actions(newplan)
