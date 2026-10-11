"""
Progress entry, the ahead/behind offers and recalculation from progress.

Split out of planea.py (issues-program.org Q3).
"""

import copy
from datetime import datetime, timedelta
import plan
from ui_utils import (
    get_yes_no,
    get_menu_choice,
    display_success,
    display_error,
    display_warning,
)
import ui_files
from formatting import date_hint, format_date, format_date_weekday, parse_date


def recalculate_plan_from_progress(current_plan):
    """
    Recalculate plan based on actual progress, redistributing remaining words
    across remaining days while keeping the end date fixed.
    """
    print("\n" + "=" * 50)
    print("RECALCULATE FROM PROGRESS")
    print("=" * 50)

    # Check if plan has a start date
    if not current_plan.start_date:
        display_error("This plan doesn't have a start date set.")
        print("  You need a start date to recalculate from progress.")
        input("\nPress Enter to continue...")
        return False

    # Check if there's any progress recorded
    if not current_plan.progress or len(current_plan.progress) == 0:
        display_error("No progress has been recorded yet.")
        print("  Record some progress first, then you can recalculate.")
        input("\nPress Enter to continue...")
        return False

    # Show current status
    words_completed = current_plan.get_total_written()
    words_remaining = current_plan.total - words_completed
    completion_pct = current_plan.get_completion_percentage()

    print("\nCurrent Progress:")
    print(f"  Total goal: {current_plan.total:,.0f} words")
    print(f"  Words completed: {words_completed:,.0f} words ({completion_pct:.1f}%)")
    print(f"  Words remaining: {words_remaining:,.0f} words")
    print(f"  Current daily target: {current_plan.daily:,.0f} words")

    if current_plan.start_date:
        end_date = current_plan.end_date or current_plan.start_date
        print(f"  Plan end date: {format_date(end_date)} (fixed)")

    print("\nThis will:")
    print("  • Spread the words actually left over the remaining writing days")
    print("  • Keep your end date fixed")
    print("  • Keep past daily goals (they are locked)")
    print("  • Keep your writing pattern and future custom day goals")
    if current_plan.weekend_mode == 'different':
        print("  • Keep the weekend goal in the same proportion to the weekday goal")
    print("  • Start today, or tomorrow if you have already logged words today")

    applied = offer_daily_recalculation(current_plan)
    input("\nPress Enter to continue...")
    return applied


def print_recalculation_failure(result):
    """Explain why recalculate_from_progress() could not run."""
    if result is None:
        display_error("Could not recalculate: Plan has no start date.")
        return

    reason = result.get('reason')
    if reason == 'goal_already_met':
        display_success("Congratulations! You've already met your goal!")
        print(f"  Total words completed: {result['words_completed']:,.0f}")
    elif reason == 'past_end_date':
        display_error("Cannot recalculate: Plan end date has already passed.")
        print(f"  End date was: {format_date(result['end_date'])}")
        print(f"  Words remaining: {result['words_remaining']:,.0f}")
    elif reason == 'no_remaining_days':
        display_error("Cannot recalculate: No remaining writing days.")
        print(f"  Words remaining: {result['words_remaining']:,.0f}")
    else:
        display_error(f"Recalculation failed: {reason}")


def print_recalculation_summary(result):
    """Show what recalculate_from_progress() changes (or would change)."""
    print(f"  Changes from: {format_date(result['as_of_date'])}")
    print(f"  Words remaining: {result['words_remaining']:,.0f}")
    print(f"  Remaining writing days: {result['remaining_writing_days']}")
    print(f"  Daily target: {result['old_daily']:,.0f} -> {result['new_daily']:,.0f} words")

    daily_change = result['new_daily'] - result['old_daily']
    if result['old_daily'] > 0 and abs(daily_change) >= 0.5:
        direction = "increase" if daily_change > 0 else "reduction"
        print(f"  Daily {direction}: {abs(daily_change):,.0f} words ({abs(daily_change) / result['old_daily'] * 100:.1f}%)")

    if result['pattern'] != 'flat':
        print(f"  Pattern kept: {result['pattern']}")
    if result['kept_custom_goals'] > 0:
        print(f"  Custom day goals kept: {result['kept_custom_goals']}")
    if result['weekend_daily'] is not None:
        print(f"  Weekend goal: {result['weekend_daily']:,.0f} words/day")
    if result['past_goals_preserved'] > 0:
        print(f"  Past daily goals locked: {result['past_goals_preserved']}")
    print(f"  Plan end date: {format_date(result['end_date'])} (unchanged)")


def offer_daily_recalculation(current_plan):
    """
    Spread the words actually left over the remaining days, keeping the end date.

    The result is previewed on a copy and applied only if the user agrees.

    Returns:
        True if the plan was changed
    """
    preview = copy.deepcopy(current_plan)
    result = preview.recalculate_from_progress()

    if result is None or not result['success']:
        print_recalculation_failure(result)
        return False

    print("\nProposed adjustment:")
    print_recalculation_summary(result)

    if not get_yes_no("\nApply this adjustment?", default='y'):
        print("Plan left unchanged.")
        return False

    current_plan.recalculate_from_progress(as_of_date=result['as_of_date'])
    display_success("Plan recalculated!")
    return True


def confirm_progress_date(current_plan, entry_date):
    """
    Check a date before logging progress for it (P20).

    Future dates are refused (most likely a typo, and they would count as
    written). Dates outside the plan are allowed after a warning: the words
    count toward the total but not toward any day's goal.

    Returns:
        True if progress may be logged for entry_date
    """
    today = plan.today()
    if entry_date > today:
        display_error("You can't log progress for a future date.")
        return False

    start, end = current_plan.start_date, current_plan.end_date
    if entry_date < start:
        where = f"before the plan starts ({format_date(start)})"
    elif end is not None and entry_date > end:
        where = f"after the plan ends ({format_date(end)})"
    else:
        return True

    display_warning(f"{format_date(entry_date)} is {where}. The words count toward "
                    "your total, but not toward any day's goal.")
    return get_yes_no("Log them anyway?", default='y')


def log_running_total(current_plan):
    """
    Log a day's words from the manuscript's running total.

    The day's words are the total minus everything logged before that day
    (pre-existing words included). A total below that is refused: logged
    days never go negative.

    Returns:
        True if progress was recorded
    """
    print(f"\nEnter the date ({date_hint()}), or press Enter for today:")
    date_input = input("Date: ").strip()
    if date_input:
        try:
            entry_date = parse_date(date_input)
        except ValueError:
            display_error(f"Invalid date '{date_input}'. Use {date_hint()}.")
            return False
    else:
        entry_date = plan.today()

    if not confirm_progress_date(current_plan, entry_date):
        return False

    day_label = format_date_weekday(entry_date)
    logged_before = current_plan.get_total_written(through=entry_date - timedelta(days=1))
    print(f"\nRunning total for: {day_label}")
    print(f"Logged before this day: {logged_before:,.0f} words (pre-existing words included)")
    existing = current_plan.get_progress_for_date(entry_date)
    if existing is not None:
        print(f"This day already has {existing:,.0f} words logged; they will be replaced")

    total_input = input("\nYour manuscript's total word count (or press Enter to cancel): ").strip()
    if total_input == "":
        return False
    try:
        running_total = int(total_input.replace(",", ""))
    except ValueError:
        display_error(f"Invalid number '{total_input}'.")
        return False

    word_count = current_plan.words_for_running_total(running_total, entry_date)
    if word_count < 0:
        display_error(f"That's {-word_count:,.0f} below the {logged_before:,.0f} already logged "
                      "(pre-existing words included).")
        print("  Logged days can't go negative. If an earlier entry was too high, correct it")
        print("  with \"Enter for a specific date\".")
        return False

    current_plan.record_progress(entry_date, word_count)
    display_success(f"Progress recorded: {word_count:,.0f} words on {format_date(entry_date)} "
                    f"(running total {running_total:,.0f})")

    daily_goal = current_plan.get_daily_goal(date=entry_date)
    if daily_goal > 0 and word_count >= daily_goal:
        print("🎉 You met your daily goal!")
    elif daily_goal > 0 and word_count > 0:
        print(f"   ({daily_goal - word_count:,.0f} words short of goal)")
    return True


def update_progress(current_plan):
    """Update progress for the writing plan."""
    if not current_plan.start_date:
        display_error("You must set a start date before tracking progress.")
        print("  Please view a calendar first to set a start date.")
        input("\nPress Enter to continue...")
        return

    progress_updated = False
    # Offer to adjust the plan at most once per visit to this screen
    adjustment_offered = False

    while True:
        print("\n" + "=" * 50)
        print("UPDATE PROGRESS")
        print("=" * 50)
        print("\nOptions:")
        print("1. Quick entry (today's words)")
        print("2. Enter for a specific date")
        print("3. View all progress entries")
        print("4. Enter your running total (manuscript word count)")
        print("0. Done")
        print("=" * 50)

        try:
            choice = get_menu_choice("\nEnter your choice (0-4): ", 0, 4)

            if choice == 0:
                # Prompt to save if progress was updated
                if progress_updated:
                    if get_yes_no("\nProgress was updated. Save the plan?", default='y'):
                        ui_files.save_plan_prompt(current_plan, ask=False)
                return

            elif choice == 1:
                # Quick entry for today
                today = plan.today()
                print(f"\nEntering progress for: {format_date_weekday(today)}")
                if not confirm_progress_date(current_plan, today):
                    continue

                # Check if it's a spare day
                if current_plan.is_spare_day(today):
                    print("⚠ Note: This is a spare day (0 words expected)")

                # Show existing progress if any
                existing = current_plan.get_progress_for_date(today)
                if existing is not None:
                    print(f"Current progress: {existing:,.0f} words")

                # Get goal for today
                daily_goal = current_plan.get_daily_goal(date=today)
                print(f"Goal for today: {daily_goal:,.0f} words")

                word_count_input = input("\nHow many words did you write today? (or press Enter to cancel): ").strip()

                if word_count_input == "":
                    continue

                try:
                    word_count = int(word_count_input)
                    if word_count < 0:
                        display_error("Word count cannot be negative")
                        continue

                    current_plan.record_progress(today, word_count)
                    progress_updated = True
                    display_success(f"Progress recorded: {word_count:,.0f} words")

                    # Check if goal was met
                    if word_count >= daily_goal:
                        print("🎉 You met your daily goal!")
                    elif word_count > 0:
                        remaining = daily_goal - word_count
                        print(f"   ({remaining:,.0f} words short of goal)")

                    # Check overall status and offer recalculation
                    if not adjustment_offered:
                        adjustment_offered = check_and_offer_recalculation(current_plan)

                except ValueError:
                    print("✗ Invalid input. Please enter a number.")

            elif choice == 2:
                # Enter for specific date
                print(f"\nEnter the date ({date_hint()}):")
                date_input = input("Date: ").strip()

                if date_input == "":
                    continue

                try:
                    entry_date = parse_date(date_input)

                    if not confirm_progress_date(current_plan, entry_date):
                        continue

                    print(f"\nEntering progress for: {format_date_weekday(entry_date)}")

                    # Check if it's a spare day
                    if current_plan.is_spare_day(entry_date):
                        print("Note: This is a spare day (0 words expected)")

                    # Show existing progress if any
                    existing = current_plan.get_progress_for_date(entry_date)
                    if existing is not None:
                        print(f"Current progress: {existing:,.0f} words")

                    # Get goal for this date
                    daily_goal = current_plan.get_daily_goal(date=entry_date)
                    print(f"Goal for this day: {daily_goal:,.0f} words")

                    word_count_input = input("\nWords written: ").strip()

                    if word_count_input == "":
                        continue

                    word_count = int(word_count_input)
                    if word_count < 0:
                        display_error("Word count cannot be negative")
                        continue

                    current_plan.record_progress(entry_date, word_count)
                    progress_updated = True
                    display_success(f"Progress recorded: {word_count:,.0f} words")

                    # Check overall status and offer recalculation
                    if not adjustment_offered:
                        adjustment_offered = check_and_offer_recalculation(current_plan)

                except ValueError as e:
                    display_error(f"Invalid input: {e}")

            elif choice == 3:
                # View all progress entries
                if not current_plan.progress:
                    display_error("No progress entries recorded yet")
                    input("\nPress Enter to continue...")
                    continue

                print("\n" + "=" * 50)
                print("ALL PROGRESS ENTRIES")
                print("=" * 50)

                # Sort by date
                sorted_dates = sorted(current_plan.progress.keys())

                for date_str in sorted_dates:
                    entry_date = datetime.strptime(date_str, "%Y-%m-%d")
                    word_count = current_plan.progress[date_str]
                    daily_goal = current_plan.get_daily_goal(date=entry_date)

                    status_icon = "✓" if word_count >= daily_goal else "○"
                    print(f"{status_icon} {format_date_weekday(entry_date)}: {word_count:,.0f} words (goal: {daily_goal:,.0f})")

                input("\nPress Enter to continue...")

            elif choice == 4:
                # Running total: the day's words are worked out from it
                if log_running_total(current_plan):
                    progress_updated = True
                    if not adjustment_offered:
                        adjustment_offered = check_and_offer_recalculation(current_plan)

        except ValueError as e:
            # Menu choices are validated by get_menu_choice; this catches the rest
            display_error(f"Invalid input: {e}")


def check_and_offer_recalculation(current_plan):
    """
    Check if user is on track and offer recalculation if needed.

    Returns:
        True if the ahead/behind offer was shown
    """
    on_track, info = current_plan.is_on_track()

    if on_track and info['status'] == 'on_track':
        # Exactly on track, no need to recalculate
        return False

    print("\n" + "-" * 50)
    print("PROGRESS STATUS")
    print("-" * 50)

    if info['status'] == 'ahead':
        print(f"✓ You're AHEAD of schedule!")
        print(f"  Expected: {info['expected_words']:,.0f} words")
        print(f"  Actual: {info['actual_words']:,.0f} words")
        print(f"  Ahead by: {info['difference']:,.0f} words ({info['percent_diff']:.1f}%)")

        if get_yes_no("\nWould you like to adjust your plan?", default='n'):
            offer_ahead_recalculation(current_plan, info)

    elif info['status'] == 'behind':
        print(f"⚠ You're BEHIND schedule")
        print(f"  Expected: {info['expected_words']:,.0f} words")
        print(f"  Actual: {info['actual_words']:,.0f} words")
        print(f"  Behind by: {abs(info['difference']):,.0f} words ({abs(info['percent_diff']):.1f}%)")

        if get_yes_no("\nWould you like to adjust your plan?", default='n'):
            offer_behind_recalculation(current_plan, info)

    return True


def offer_deadline_adjustment(current_plan):
    """
    Keep the daily goal and move the end date to fit the words actually left.

    Starts today, or tomorrow if words were already logged today. The result
    is previewed on a copy and applied only if the user agrees.
    """
    preview = copy.deepcopy(current_plan)
    as_of_date = preview.default_recalculation_date()
    try:
        result = preview.adjust_time_from_progress(as_of_date=as_of_date)
    except ValueError as e:
        display_error(f"Could not adjust the deadline: {e}")
        return

    if result is None or result['new_end_date'] is None or result['old_end_date'] is None:
        display_error("Could not adjust the deadline.")
        return

    day_change = (result['new_end_date'] - result['old_end_date']).days
    print(f"\nProposed adjustment:")
    print(f"  Daily goal: {result['daily']:,.0f} words/day")
    print(f"  Writing days: {result['old_time']} -> {result['new_time']}")
    print(f"  End date: {format_date(result['old_end_date'])} -> {format_date(result['new_end_date'])}")
    if day_change < 0:
        print(f"  Finishing early by: {-day_change} days")
    elif day_change > 0:
        print(f"  Extension: {day_change} days")
    else:
        print("  End date unchanged")

    if get_yes_no("Apply this adjustment?", default='y'):
        current_plan.adjust_time_from_progress(as_of_date=as_of_date)
        display_success("Plan adjusted!")


def offer_ahead_recalculation(current_plan, info):
    """Offer recalculation options when ahead of schedule."""
    print("\n" + "=" * 50)
    print("ADJUST PLAN (AHEAD OF SCHEDULE)")
    print("=" * 50)
    print("\nHow would you like to adjust your plan?")
    print("\n1. Reduce daily goals (keep end date)")
    print("2. Finish early (keep daily goals)")
    print("0. Keep plan as is")
    print("=" * 50)

    choice = get_menu_choice("\nEnter your choice (0-2): ", 0, 2)

    if choice == 0:
        return

    elif choice == 1:
        # Reduce daily goals (keep end date)
        offer_daily_recalculation(current_plan)
        return

    elif choice == 2:
        # Finish early
        offer_deadline_adjustment(current_plan)
        return


def offer_behind_recalculation(current_plan, info):
    """Offer recalculation options when behind schedule."""
    print("\n" + "=" * 50)
    print("ADJUST PLAN (BEHIND SCHEDULE)")
    print("=" * 50)
    print("\nHow would you like to adjust your plan?")
    print("\n1. Increase daily goals (keep end date)")
    print("2. Extend deadline (keep daily goals)")
    print("0. Keep plan as is")
    print("=" * 50)

    choice = get_menu_choice("\nEnter your choice (0-2): ", 0, 2)

    if choice == 0:
        return

    elif choice == 1:
        # Increase daily goals (keep end date)
        offer_daily_recalculation(current_plan)
        return

    elif choice == 2:
        # Extend deadline
        offer_deadline_adjustment(current_plan)
        return


def view_progress_summary(current_plan):
    """Display a comprehensive progress summary."""
    if not current_plan.start_date:
        display_error("No start date set")
        input("\nPress Enter to continue...")
        return

    print("\n" + "=" * 50)
    print("PROGRESS SUMMARY")
    print("=" * 50)

    # Overall progress
    total_written = current_plan.get_total_written()
    remaining = current_plan.get_remaining_words()
    completion = current_plan.get_completion_percentage()

    print(f"\nOverall Progress:")
    print(f"  Total goal: {current_plan.total:,.0f} words")
    print(f"  Written: {total_written:,.0f} words ({completion:.1f}%)")
    print(f"  Remaining: {remaining:,.0f} words")

    # Days with progress
    days_recorded = current_plan.get_days_with_progress()
    print(f"\n  Days recorded: {days_recorded}")

    # Current streak
    streak = current_plan.get_current_streak()
    if streak > 0:
        print(f"  Current streak: {streak} day{'s' if streak != 1 else ''} 🔥")

    # On track status
    on_track, info = current_plan.is_on_track()

    print(f"\nSchedule Status:")
    if info.get('message'):
        print(f"  {info['message']}")
    else:
        if info['status'] == 'ahead':
            print(f"  ✓ AHEAD by {info['difference']:,.0f} words ({info['percent_diff']:.1f}%)")
        elif info['status'] == 'on_track':
            print(f"  ✓ ON TRACK")
        else:
            print(f"  ⚠ BEHIND by {abs(info['difference']):,.0f} words ({abs(info['percent_diff']):.1f}%)")

        print(f"  Expected: {info['expected_words']:,.0f} words")
        print(f"  Actual: {info['actual_words']:,.0f} words")
        print(f"  Days elapsed: {info['days_elapsed']}")

    input("\nPress Enter to continue...")
