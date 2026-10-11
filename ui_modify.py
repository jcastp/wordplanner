"""
Plan modification screens: values, spare days, custom day goals, weekends,
start date, and the decision 1 adjustment question.

Split out of planea.py (issues-program.org Q3).
"""

import copy
from datetime import datetime, timedelta
import plan
import config
from ui_utils import (
    get_yes_no,
    get_positive_number,
    get_date_input,
    get_menu_choice,
    get_integer_input,
    display_success,
    display_error,
    display_warning,
    parse_date_list,
)
from pattern_utils import choose_writing_pattern
import ui_progress
from formatting import date_hint, format_date, format_date_weekday, parse_date


LOCKED_DAYS_MESSAGE = "Days before today are locked: their goals can't change."


def offer_plan_adjustment(current_plan, before, drop_after_end=(),
                          question="This changes the plan's writing days. How should the plan adjust?"):
    """
    Ask how the plan absorbs a change (decision 1) and apply the answer.

    Called after spare days, the weekend mode or a custom day goal changed.
    Each option of Plan.apply_adjustment() is previewed on a copy of the
    plan, and only the chosen one is applied.

    Args:
        current_plan: The plan, already changed
        before: A copy of the plan taken before the change
        drop_after_end: See Plan.apply_adjustment()
        question: The question shown above the options

    Returns:
        The chosen adjustment, or None if the change didn't affect the plan
    """
    old_end = before.end_date
    if not current_plan.start_date or old_end is None:
        return None
    if current_plan.build_schedule()['goals'] == before.build_schedule()['goals']:
        return None

    old_daily = before.daily
    labels = {
        'move_end': f"Move the end date (keep {old_daily:,.0f} words/day)",
        'keep_end': "Keep the end date (change the daily goal)",
        'change_total': "Keep the end date and the daily goal (change the total)",
    }
    options = [a for a in plan.Plan.ADJUSTMENTS if a != 'move_end' or old_daily > 0]

    def apply(p, adjustment):
        p.apply_adjustment(before, adjustment, drop_after_end)

    def outcome(p):
        end = format_date(p.end_date) if p.end_date else "-"
        return f"ends {end}, {p.daily:,.0f} words/day, total {p.total:,.0f} words"

    print(f"\n{question}")
    print(f"   Before: {outcome(before)}")
    for number, adjustment in enumerate(options, 1):
        preview = copy.deepcopy(current_plan)
        apply(preview, adjustment)
        print(f"{number}. {labels[adjustment]}")
        print(f"   -> {outcome(preview)}")

    choice = get_menu_choice(f"\nEnter your choice (1-{len(options)}): ", 1, len(options))
    adjustment = options[choice - 1]
    apply(current_plan, adjustment)
    display_success(f"Plan {outcome(current_plan)}")
    return adjustment


def manage_spare_days(current_plan):
    """Interactively manage spare days for the plan."""

    # Check if start_date is set
    if not current_plan.start_date:
        display_error("You must set a start date before managing spare days.")
        print("  Please view a calendar first to set a start date.")
        return False

    fingerprint = current_plan.fingerprint()
    while True:
        plan_end_date = current_plan.end_date or current_plan.start_date
        print("\n" + "=" * 50)
        print("MANAGE SPARE DAYS")
        print("=" * 50)
        print("\nSpare days are days with 0 words (holidays, urgent matters, etc.)")
        print(f"Plan period: {format_date(current_plan.start_date)} to {format_date(plan_end_date)}")
        print(f"Writing days: {current_plan.time:.0f}")
        print(f"Spare days: {current_plan.spare_days}")

        if current_plan.spare_days_dates:
            print("\nCurrent spare days:")

            # Filter out any old integer-based spare days and convert if possible
            valid_spare_dates = []
            old_format_count = 0

            for spare_item in current_plan.spare_days_dates:
                if isinstance(spare_item, int):
                    # Old format (day number) - skip or convert if we have start_date
                    old_format_count += 1
                    if current_plan.start_date:
                        # Convert old day number to actual date
                        converted_date = current_plan.start_date + timedelta(days=spare_item - 1)
                        valid_spare_dates.append(converted_date)
                else:
                    # New format (datetime object)
                    valid_spare_dates.append(spare_item)

            # Update the list with converted dates
            if old_format_count > 0:
                current_plan.spare_days_dates = valid_spare_dates
                print(f"  (Converted {old_format_count} spare days from old format)")

            sorted_spare = sorted(valid_spare_dates)
            for spare_date in sorted_spare:
                outside = spare_date < current_plan.start_date or spare_date > plan_end_date
                note = "  (outside the plan, ignored)" if outside else ""
                print(f"  {format_date_weekday(spare_date)}{note}")

        print("\nOptions:")
        print("1. Add spare day(s)")
        print("2. Remove spare day(s)")
        print("3. Clear all spare days")
        print("\nQuick Actions:")
        print("4. Mark all Saturdays as spare")
        print("5. Mark all Sundays as spare")
        print("6. Mark all weekends as spare")
        print("0. Done")
        print("=" * 50)

        before = copy.deepcopy(current_plan)
        try:
            choice = get_menu_choice("\nEnter your choice (0-6): ", 0, 6)

            if choice == 0:
                return current_plan.fingerprint() != fingerprint  # True if the plan changed

            elif choice == 1:
                # Add spare days by date
                print("\nEnter dates to mark as spare days:")
                print(f"  Format: {date_hint()}")
                print("  Multiple dates: separated by commas")
                print("  Date range: use 'to' (e.g., <first date> to <last date>)")
                print(f"  Valid range: {format_date(current_plan.start_date)} to ~1 year later")

                dates_input = input("Date(s): ").strip()

                if not dates_input:
                    continue

                try:
                    new_spare_dates = parse_date_list(dates_input)

                    # Validate dates are reasonable (within plan period + 1 year buffer)
                    max_allowed_date = current_plan.start_date + timedelta(days=365 + current_plan.time)
                    min_allowed_date = current_plan.start_date

                    invalid_dates = []
                    for d in new_spare_dates:
                        if d < min_allowed_date or d > max_allowed_date:
                            invalid_dates.append(format_date(d))

                    if invalid_dates:
                        display_error(f"Some dates are outside the valid range:")
                        for d in invalid_dates[:5]:  # Show first 5
                            print(f"  {d}")
                        if len(invalid_dates) > 5:
                            print(f"  ... and {len(invalid_dates) - 5} more")
                        continue

                    if any(d < plan.today() for d in new_spare_dates):
                        display_error(LOCKED_DAYS_MESSAGE)
                        continue

                    # Add to spare days (avoid duplicates)
                    added_count = 0
                    for new_date in new_spare_dates:
                        # Check if already in spare days
                        is_duplicate = False
                        for existing in current_plan.spare_days_dates:
                            if new_date.date() == existing.date():
                                is_duplicate = True
                                break

                        if not is_duplicate:
                            current_plan.spare_days_dates.append(new_date)
                            added_count += 1


                    display_success(f"Added {added_count} spare day(s)")
                    if added_count < len(new_spare_dates):
                        print(f"  ({len(new_spare_dates) - added_count} were already marked as spare)")
                    offer_plan_adjustment(current_plan, before)

                except ValueError as e:
                    display_error(f"Invalid date format: {e}")
                    print(f"  Please use {date_hint()}")

            elif choice == 2:
                # Remove spare days by date
                if not current_plan.spare_days_dates:
                    display_error("No spare days to remove")
                    continue

                print("\nEnter dates to remove from spare days:")
                print(f"  Format: {date_hint()}, or comma-separated dates")
                print("  Or a range: <first date> to <last date>")

                dates_input = input("Date(s): ").strip()

                if not dates_input:
                    continue

                try:
                    dates_to_remove = parse_date_list(dates_input)

                    if any(d < plan.today() for d in dates_to_remove):
                        display_error(LOCKED_DAYS_MESSAGE)
                        continue

                    # Remove from spare days
                    removed_count = 0
                    for remove_date in dates_to_remove:
                        for i, spare_date in enumerate(current_plan.spare_days_dates[:]):
                            if remove_date.date() == spare_date.date():
                                current_plan.spare_days_dates.remove(spare_date)
                                removed_count += 1
                                break


                    display_success(f"Removed {removed_count} spare day(s)")
                    if removed_count < len(dates_to_remove):
                        print(f"  ({len(dates_to_remove) - removed_count} were not spare days)")
                    offer_plan_adjustment(current_plan, before)

                except ValueError as e:
                    display_error(f"Invalid date format: {e}")

            elif choice == 3:
                # Clear all spare days from today on (past ones are locked)
                today = plan.today()
                clearable = [d for d in current_plan.spare_days_dates if d >= today]
                if not clearable:
                    display_error("No spare days from today on to clear")
                    continue

                if get_yes_no(f"Clear all {len(clearable)} spare days from today on?", default='n'):
                    current_plan.spare_days_dates = [d for d in current_plan.spare_days_dates if d < today]
                    display_success("Spare days from today on cleared")
                    offer_plan_adjustment(current_plan, before)

            elif choice in (4, 5, 6):
                weekdays, label = {
                    4: ([5], "Saturdays"),
                    5: ([6], "Sundays"),
                    6: (current_plan.weekend_days, "weekend days"),
                }[choice]
                current_plan.mark_weekdays_as_spare(weekdays)
                added = [d for d in current_plan.spare_days_dates if d not in before.spare_days_dates]
                offer_plan_adjustment(current_plan, before, drop_after_end=added)
                added_count = sum(1 for d in added if d in current_plan.spare_days_dates)
                display_success(f"Marked {added_count} {label} as spare days")

        except ValueError as e:
            # Menu choices are validated by get_menu_choice; this catches the rest
            display_error(f"Invalid input: {e}")


CUSTOM_GOAL_QUESTION = "This changes the day's goal. How should the rest of the plan adjust?"


def custom_goal_date_problem(current_plan, target_date):
    """
    Why a custom goal can't be set on target_date, as a message, or None (P17).

    The rule is Plan.custom_goal_problem(); this only words it.
    """
    problem = current_plan.custom_goal_problem(target_date)
    if problem == 'past':
        return LOCKED_DAYS_MESSAGE
    if problem == 'outside':
        start, end = current_plan.start_date, current_plan.end_date
        end_text = format_date(end or start)
        return (f"{format_date(target_date)} is outside the plan "
                f"({format_date(start)} to {end_text}).")
    if problem == 'spare':
        return (f"{format_date(target_date)} is a spare day. "
                "Remove it in 'Manage spare days' first.")
    if problem == 'weekend_rest':
        return (f"{target_date.strftime('%A')}s are rest days in this plan. "
                "Change the weekend settings first.")
    return None


def edit_individual_day_goal(current_plan):
    """Edit the word goal for a specific day."""
    dt = datetime  # Alias for strptime usage

    if not current_plan.start_date:
        display_error("You must set a start date before editing individual day goals.")
        return False

    print("\n" + "=" * 50)
    print("EDIT INDIVIDUAL DAY GOAL")
    print("=" * 50)
    print("\nThis allows you to set a custom word goal for a specific date.")
    print("This overrides pattern-based goals and weekend settings for that day.")

    plan_end_date = current_plan.end_date or current_plan.start_date
    print(f"\nPlan period: {format_date(current_plan.start_date)} to {format_date(plan_end_date)}")

    if current_plan.custom_daily_goals:
        print(f"\nCurrent custom goals ({len(current_plan.custom_daily_goals)}):")
        for date_key, word_count in sorted(current_plan.custom_daily_goals.items()):
            date_obj = dt.strptime(date_key, '%Y-%m-%d')
            print(f"  {format_date_weekday(date_obj)}: {word_count:,.0f} words")

    print("\nOptions:")
    print("1. Set custom goal for a specific day")
    print("2. Remove custom goal (revert to pattern/default)")
    print("3. Clear all custom day goals")
    print("0. Done")
    print("=" * 50)

    fingerprint = current_plan.fingerprint()
    while True:
        try:
            choice = get_menu_choice("\nEnter your choice (0-3): ", 0, 3)

            if choice == 0:
                return current_plan.fingerprint() != fingerprint  # True if the plan changed

            elif choice == 1:
                # Set custom goal
                print("\nEnter date to customize:")
                date_input = input(f"Date ({date_hint()}): ").strip()

                if not date_input:
                    continue

                try:
                    target_date = parse_date(date_input)

                    problem = custom_goal_date_problem(current_plan, target_date)
                    if problem:
                        display_error(problem)
                        continue

                    # Show current goal for this day
                    current_goal = current_plan.get_daily_goal(date=target_date)
                    print(f"\nCurrent goal for {target_date.strftime('%A')}, {format_date(target_date)}: {current_goal:,.0f} words")

                    # Get new goal
                    print("\nEnter new word goal for this day:")
                    print("  (Enter 0 to make it a rest day, or any positive number)")
                    new_goal = get_integer_input("New goal: ", min_value=0,
                                                 max_value=config.MAX_DAILY_WORDS)

                    before = copy.deepcopy(current_plan)
                    current_plan.set_custom_daily_goal(target_date, new_goal)

                    display_success(f"Set custom goal of {new_goal:,.0f} words for {format_date(target_date)}")
                    offer_plan_adjustment(current_plan, before, question=CUSTOM_GOAL_QUESTION)

                except ValueError as e:
                    display_error(f"Invalid date format: {e}")
                    print(f"  Please use {date_hint()}")

            elif choice == 2:
                # Remove custom goal
                if not current_plan.custom_daily_goals:
                    display_error("No custom day goals to remove")
                    continue

                print("\nEnter date to remove custom goal:")
                date_input = input(f"Date ({date_hint()}): ").strip()

                if not date_input:
                    continue

                try:
                    target_date = parse_date(date_input)
                    date_key = target_date.strftime('%Y-%m-%d')

                    if target_date < plan.today():
                        display_error(LOCKED_DAYS_MESSAGE)
                        continue

                    if date_key in current_plan.custom_daily_goals:
                        before = copy.deepcopy(current_plan)
                        current_plan.remove_custom_daily_goal(target_date)

                        display_success(f"Removed custom goal for {format_date(target_date)}")
                        offer_plan_adjustment(current_plan, before, question=CUSTOM_GOAL_QUESTION)
                    else:
                        display_error(f"No custom goal found for {format_date(target_date)}")

                except ValueError as e:
                    display_error(f"Invalid date format: {e}")

            elif choice == 3:
                # Clear all custom goals from today on (past ones are locked)
                today_key = plan.today().strftime('%Y-%m-%d')
                clearable = [k for k in current_plan.custom_daily_goals if k >= today_key]
                if not clearable:
                    display_error("No custom day goals from today on to clear")
                    continue

                if get_yes_no(f"Clear all {len(clearable)} custom day goals from today on?", default='n'):
                    before = copy.deepcopy(current_plan)
                    for date_key in clearable:
                        del current_plan.custom_daily_goals[date_key]

                    display_success("Custom day goals from today on cleared")
                    offer_plan_adjustment(current_plan, before, question=CUSTOM_GOAL_QUESTION)

        except ValueError as e:
            # Menu choices are validated by get_menu_choice; this catches the rest
            display_error(f"Invalid input: {e}")


def get_writing_days(prompt, current_plan):
    """Ask for a number of writing days, not fewer than the plan's locked (past) days."""
    min_days = current_plan.min_writing_days()
    while True:
        days = get_positive_number(prompt, max_value=config.MAX_DAYS)
        if days >= min_days:
            return days
        display_error(f"The plan already has {min_days} past writing days; enter at least {min_days}.")


def describe_dated_days(dates_and_labels):
    """Print '  2026-11-07 (Saturday): spare day' lines, at most 10."""
    for date, label in dates_and_labels[:10]:
        print(f"  {format_date_weekday(date)}: {label}")
    if len(dates_and_labels) > 10:
        print(f"  ... and {len(dates_and_labels) - 10} more")


def start_date_move_warnings(before, moved):
    """
    What the user should know before a start-date move is applied (decision 7).

    Args:
        before: The plan before the move
        moved: A preview copy with the move applied

    Returns:
        List of warning strings
    """
    warnings = []
    start, end = moved.start_date, moved.end_date
    today = plan.today()

    outside = [(k, w) for k, w in moved.progress.items()
               if w and not (start <= datetime.strptime(k, '%Y-%m-%d') <= end)]
    if outside:
        words = sum(w for _, w in outside)
        warnings.append(
            f"{len(outside)} day(s) with progress ({words:,.0f} words) are outside the new plan. "
            "Progress never moves: those words still count as written, but not toward any day's goal.")

    before_days = set(before.plan_days())
    joining = [d for d in moved.plan_days() if d < today and d not in before_days
               and not before.is_locked(d)]
    if joining:
        warnings.append(
            f"{len(joining)} day(s) before today join the plan. They are past, so their "
            "goals are locked as they are now.")

    if moved.locked_goals and any(before.is_locked(d) for d in before_days if not start <= d <= end):
        warnings.append("Some past (locked) days are now outside the plan; their goals no longer count.")
    return warnings


def change_start_date(current_plan, new_start):
    """
    Move the plan to a new start date, as decision 7 describes.

    Shows the new window, lists the spare days and custom goals that would
    end up outside it, offers to keep them on their dates (default) or shift
    them all by the same offset, warns about progress outside the new plan,
    and applies the move only after confirmation. Each option is previewed
    on a copy.

    Returns:
        True if the start date changed
    """
    new_start = plan.to_midnight(new_start)

    if not current_plan.start_date:
        current_plan.start_date = new_start
        display_success(f"Start date set to: {format_date(new_start)}")
        return True

    if current_plan.time <= 0:
        current_plan.start_date = new_start
        display_success(f"Start date changed to: {format_date(new_start)}")
        return True

    offset = (new_start - current_plan.start_date).days
    if offset == 0:
        print("\nThat is already the start date. Nothing changed.")
        return False

    today = plan.today()
    movable = [(d, "spare day") for d in current_plan.spare_days_dates if d >= today]
    movable += [(datetime.strptime(k, '%Y-%m-%d'), f"custom goal of {g:,.0f} words")
                for k, g in current_plan.custom_daily_goals.items()
                if datetime.strptime(k, '%Y-%m-%d') >= today]
    movable.sort(key=lambda item: item[0])

    def preview(shift):
        moved = copy.deepcopy(current_plan)
        moved.move_start_date(new_start, shift_dated_days=shift)
        return moved

    def outcome(p):
        return (f"{format_date(p.start_date)} to {format_date(p.end_date)}, "
                f"{p.daily:,.0f} words/day")

    keep = preview(False)
    direction = "later" if offset > 0 else "earlier"
    print(f"\nMoving the start {abs(offset)} day(s) {direction}.")
    print(f"   Now: {outcome(current_plan)}")

    shift = False
    if movable:
        def is_outside(d):
            return not keep.start_date <= d <= keep.end_date
        outside = [(d, label) for d, label in movable if is_outside(d)]

        print("\nYour spare days and custom goals from today on:")
        if outside:
            print("These would fall outside the new plan (and be ignored) if kept on their dates:")
            describe_dated_days(outside)
        else:
            print("All of them stay inside the new plan if kept on their dates.")

        shifted = preview(True)
        print("\n1. Keep them on their dates (recommended)")
        print(f"   -> {outcome(keep)}")
        weekday_note = "" if offset % 7 == 0 else " (they land on other weekdays)"
        print(f"2. Shift all of them {abs(offset)} day(s) {direction}{weekday_note}")
        print(f"   -> {outcome(shifted)}")
        print("0. Cancel")
        choice = get_menu_choice("\nEnter your choice (0-2): ", 0, 2)
        if choice == 0:
            print("Start date not changed.")
            return False
        shift = choice == 2
        chosen = shifted if shift else keep
    else:
        chosen = keep
        print(f"   New: {outcome(chosen)}")

    warnings = start_date_move_warnings(current_plan, chosen)
    if chosen.locked_goals or chosen.progress:
        left = chosen.total - chosen.get_total_written()
        warnings.append(f"The plan has started: the open days are recalculated to cover the "
                        f"{max(0, left):,.0f} words left.")
    for warning in warnings:
        display_warning(warning)

    if not get_yes_no("\nApply the new start date?", default='y'):
        print("Start date not changed.")
        return False

    current_plan.move_start_date(new_start, shift_dated_days=shift)
    display_success(f"Start date changed to: {format_date(new_start)} "
                    f"(plan ends {format_date(current_plan.end_date)})")
    return True


def rename_plan(current_plan):
    """Change the plan's name. Returns True if it changed."""
    print(f"\nCurrent name: {current_plan.name or 'Unnamed'}")
    new_name = input("Enter a new name (or press Enter to keep it): ").strip()
    if not new_name or new_name == current_plan.name:
        print("Name unchanged.")
        return False
    current_plan.name = new_name
    display_success(f"Plan renamed to: {new_name}")
    return True


def modify_plan(current_plan):
    """Allow user to modify plan values and recalculate."""
    print("\n" + "=" * 50)
    print("MODIFY PLAN")
    print("=" * 50)
    print("\nCurrent values:")
    print(f"  Name: {current_plan.name or 'Unnamed'}")
    print(f"  Total words: {current_plan.total:,.0f}")
    print(f"  Daily words: {current_plan.daily:,.0f}")
    print(f"  Writing days: {current_plan.time:.0f}")
    print(f"  Spare days: {current_plan.spare_days:.0f}")
    if current_plan.spare_days > 0:
        total_calendar_days = current_plan.time + current_plan.spare_days
        print(f"  Total calendar duration: {total_calendar_days:.0f} days")
    print(f"  Writing pattern: {current_plan.pattern}")
    if current_plan.start_date:
        print(f"  Start date: {format_date(current_plan.start_date)}")
    else:
        print(f"  Start date: Not set")
    print("\nWhat would you like to modify?")
    print("\n1. Total words")
    print("2. Daily words")
    print("3. Writing days")
    print("4. Spare days")
    print("5. Writing pattern")
    print("6. Start date")
    print("7. Modify two values (third will be calculated)")
    print("8. Weekend settings")
    print("9. Edit individual day goals")
    print("10. Recalculate from progress (redistribute remaining words)")
    print("11. Plan name")
    print("0. Cancel")
    print("=" * 50)

    while True:
        try:
            choice = get_menu_choice("\nEnter your choice (0-11): ", 0, 11)
            if choice == 0:
                return False  # No changes made

            elif choice == 1:
                # Modify total words, ask what to keep constant
                new_total = get_positive_number("\nEnter new total words: ", max_value=config.MAX_WORDS)
                print("\nKeep constant:")
                print("1. Daily words (recalculate time)")
                print("2. Time (recalculate daily words)")

                keep_choice = get_menu_choice("Enter your choice (1-2): ", 1, 2)
                if keep_choice == 1:
                    current_plan.total = new_total
                    current_plan.calculate_time()
                    return True
                elif keep_choice == 2:
                    current_plan.total = new_total
                    current_plan.calculate_daily()
                    return True

            elif choice == 2:
                # Modify daily words, ask what to keep constant
                new_daily = get_positive_number("\nEnter new daily words: ", max_value=config.MAX_DAILY_WORDS)
                print("\nKeep constant:")
                print("1. Total words (recalculate time)")
                print("2. Time (recalculate total words)")

                keep_choice = get_menu_choice("Enter your choice (1-2): ", 1, 2)
                if keep_choice == 1:
                    current_plan.daily = new_daily
                    current_plan.calculate_time()
                    return True
                elif keep_choice == 2:
                    current_plan.daily = new_daily
                    current_plan.calculate_words()
                    return True

            elif choice == 3:
                # Modify time, ask what to keep constant
                new_time = get_writing_days("\nEnter new time (days): ", current_plan)
                print("\nKeep constant:")
                print("1. Total words (recalculate daily words)")
                print("2. Daily words (recalculate total words)")

                keep_choice = get_menu_choice("Enter your choice (1-2): ", 1, 2)
                if keep_choice == 1:
                    current_plan.time = new_time
                    current_plan.calculate_daily()
                    return True
                elif keep_choice == 2:
                    current_plan.time = new_time
                    current_plan.calculate_words()
                    return True

            elif choice == 4:
                # Manage spare days
                return manage_spare_days(current_plan)

            elif choice == 5:
                # Change writing pattern
                print(f"\nCurrent pattern: {current_plan.pattern}")
                pattern, pattern_config = choose_writing_pattern()
                current_plan.pattern = pattern
                current_plan.pattern_config = pattern_config
                current_plan.invalidate_daily_goals_cache()
                display_success(f"Pattern changed to: {pattern}")
                return True

            elif choice == 6:
                # Change start date
                if current_plan.start_date:
                    print(f"\nCurrent start date: {format_date(current_plan.start_date)}")
                else:
                    print(f"\nCurrent start date: Not set")

                print(f"\nEnter new start date ({date_hint()})")
                print("Or press Enter for today's date")
                new_start_date = get_date_input("Start date: ")
                return change_start_date(current_plan, new_start_date)

            elif choice == 7:
                # Modify two values, calculate the third
                print("\nWhich value should be calculated?")
                print("1. Calculate total words (from daily × time)")
                print("2. Calculate daily words (from total ÷ time)")
                print("3. Calculate time (from total ÷ daily)")

                calc_choice = get_menu_choice("Enter your choice (1-3): ", 1, 3)
                if calc_choice == 1:
                    daily = get_positive_number("Enter daily words: ", max_value=config.MAX_DAILY_WORDS)
                    time = get_writing_days("Enter writing days: ", current_plan)
                    current_plan.daily = daily
                    current_plan.time = time
                    current_plan.calculate_words()
                    return True
                elif calc_choice == 2:
                    total = get_positive_number("Enter total words: ", max_value=config.MAX_WORDS)
                    time = get_writing_days("Enter writing days: ", current_plan)
                    current_plan.total = total
                    current_plan.time = time
                    current_plan.calculate_daily()
                    return True
                elif calc_choice == 3:
                    total = get_positive_number("Enter total words: ", max_value=config.MAX_WORDS)
                    daily = get_positive_number("Enter daily words: ", max_value=config.MAX_DAILY_WORDS)
                    current_plan.total = total
                    current_plan.daily = daily
                    current_plan.calculate_time()
                    return True

            elif choice == 8:
                # Configure weekend settings
                configure_weekend_settings(current_plan)
                return True

            elif choice == 9:
                # Edit individual day goals
                modified = edit_individual_day_goal(current_plan)
                return modified

            elif choice == 10:
                # Recalculate from progress
                modified = ui_progress.recalculate_plan_from_progress(current_plan)
                return modified

            elif choice == 11:
                return rename_plan(current_plan)
        except ValueError as e:
            # Menu choices are validated by get_menu_choice; this catches the rest
            display_error(f"Invalid input: {e}")


def configure_weekend_settings(current_plan):
    """Configure weekend-specific settings for the plan."""
    print("\n" + "=" * 50)
    print("WEEKEND CONFIGURATION")
    print("=" * 50)
    print("\nHow would you like to handle weekends?")
    print("\n1. Same as weekdays - Write the same amount every day")
    print("2. Different goal - Set a specific word count for weekends")
    print("3. Weekends as spare days - No writing on weekends")
    print("0. Skip weekend configuration")
    print("=" * 50)

    choice = get_menu_choice("\nEnter your choice (0-3): ", 0, 3)

    if choice == 0:
        # Keep default: same as weekdays
        return

    before = copy.deepcopy(current_plan)

    if choice == 1:
        current_plan.weekend_mode = "same"
        display_success("Weekends will have the same writing goal as weekdays")

    elif choice == 2:
        current_plan.weekend_mode = "different"
        print("\nSet weekend writing goal:")
        print("(This could be higher for extra writing time, or lower for rest)")
        weekend_goal = get_positive_number("Weekend daily goal: ", max_value=config.MAX_DAILY_WORDS)
        current_plan.weekend_daily = weekend_goal
        display_success(f"Weekends will have a goal of {weekend_goal:,.0f} words/day")

    elif choice == 3:
        current_plan.weekend_mode = "spare"
        display_success("All weekends will be marked as spare days (0 words)")

    # Ask about which days are weekends
    if choice in [2, 3]:
        if get_yes_no("\nCustomize which days are considered 'weekend'?", default='n'):
            print("\nSelect weekend days (Saturday and Sunday are default):")
            print("0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday")
            days_input = input("Enter day numbers separated by commas (e.g., 5,6): ").strip()
            try:
                weekend_days = [int(d.strip()) for d in days_input.split(',')]
                weekend_days = [d for d in weekend_days if 0 <= d <= 6]
                if weekend_days:
                    current_plan.weekend_days = weekend_days
                    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                    weekend_names = [day_names[d] for d in weekend_days]
                    display_success(f"Weekend days set to: {', '.join(weekend_names)}")
                else:
                    display_warning("Invalid days, using default (Sat, Sun)")
            except ValueError:
                display_warning("Invalid input, using default weekend days (Sat, Sun)")

    # Decision 1: ask how the plan absorbs the change
    offer_plan_adjustment(current_plan, before)
