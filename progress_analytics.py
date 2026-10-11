"""Progress analytics and visualization module for writing plans."""

import datetime
import sys
from typing import Dict, List, Tuple, Optional
import plotext as plt
import config
from ui_utils import get_menu_choice
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box


console = Console()


def _today():
    return datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def elapsed_writing_days(plan_obj) -> List[datetime.datetime]:
    """
    The days the writing pace is measured over (A1).

    Every writing day of the plan up to yesterday (rest days with a goal of 0
    left out; missed days included), plus every day with words logged:
    today once you've written, rest days you wrote on, days outside the plan.
    """
    today = _today()
    days = {d for d in plan_obj.plan_days() if d < today and not plan_obj.is_rest_day(d)}
    days |= {datetime.datetime.strptime(k, '%Y-%m-%d') for k, w in plan_obj.progress.items() if w > 0}
    return sorted(days)


def average_words_per_writing_day(plan_obj) -> float:
    """Words written in the plan (pre-existing excluded) per elapsed writing day."""
    days = elapsed_writing_days(plan_obj)
    return plan_obj.get_plan_written() / len(days) if days else 0


def _is_future_rest_day(plan_obj, date) -> bool:
    """A rest day ahead: goal 0 inside the plan; spare or weekend-off days after it."""
    end = plan_obj.end_date
    if end is not None and plan_obj.start_date <= date <= end:
        return plan_obj.is_rest_day(date)
    return plan_obj.is_spare_day(date) or (plan_obj.weekend_mode == "spare" and plan_obj.is_weekend(date))


def writing_day_position(plan_obj, words) -> float:
    """
    How many writing days of the schedule `words` cover (fractional).

    Follows each day's goal, so a pattern or a recalculation doesn't distort
    it. Starts from the same baseline as is_on_track() (schedule_adjustment).
    Words beyond the end are counted at the plan's daily goal.
    """
    goals = plan_obj.build_schedule()['goals']
    cumulative = -plan_obj.schedule_adjustment
    position = 0.0
    if words <= cumulative:
        return position
    for day in plan_obj.plan_days():
        goal = goals[day.strftime('%Y-%m-%d')]
        if goal <= 0:
            continue
        if cumulative + goal >= words:
            return position + (words - cumulative) / goal
        cumulative += goal
        position += 1
    return position + (words - cumulative) / max(plan_obj.daily, 1)


def calculate_days_ahead_behind(plan_obj) -> float:
    """
    Writing days ahead (positive) or behind (negative) the schedule (A1).

    Compares where the words written sit on the schedule with where the
    expected words (goals through yesterday, decision 4) sit. It used to
    divide by the current daily goal, which changes after each recalculation.
    """
    _, info = plan_obj.is_on_track()
    if 'status' not in info:
        return 0
    return (writing_day_position(plan_obj, info['actual_words'])
            - writing_day_position(plan_obj, info['expected_words']))


def calculate_statistics(plan_obj) -> Dict:
    """
    Calculate comprehensive statistics about writing progress.

    Args:
        plan_obj: Plan instance with progress data

    Returns:
        Dictionary containing various statistics
    """
    if not plan_obj.start_date or not plan_obj.progress:
        return {
            'total_written': 0,
            'days_recorded': 0,
            'average_per_day': 0,
            'best_day': None,
            'worst_day': None,
            'current_streak': 0,
            'longest_streak': 0,
            'completion_eta': None,
            'days_ahead_behind': 0,
        }

    # Basic stats
    total_written = plan_obj.get_total_written()
    days_recorded = plan_obj.get_days_with_progress()

    # Average per writing day: missed days count, rest days don't (pre-existing words excluded)
    average_per_day = average_words_per_writing_day(plan_obj)

    # Best and worst writing days
    best_day = None
    worst_day = None
    best_count = 0
    worst_count = float('inf')

    for date_str, word_count in plan_obj.progress.items():
        if word_count > 0:  # Only consider days with actual writing
            if word_count > best_count:
                best_count = word_count
                best_day = (date_str, word_count)
            if word_count < worst_count:
                worst_count = word_count
                worst_day = (date_str, word_count)

    # Current streak
    current_streak = plan_obj.get_current_streak()

    # Calculate longest streak
    longest_streak = calculate_longest_streak(plan_obj)

    # Calculate ETA
    completion_eta = calculate_completion_eta(plan_obj)

    # Check if ahead or behind
    is_on_track, track_info = plan_obj.is_on_track()
    days_ahead_behind = calculate_days_ahead_behind(plan_obj)

    return {
        'total_written': total_written,
        'days_recorded': days_recorded,
        'average_per_day': average_per_day,
        'best_day': best_day,
        'worst_day': worst_day,
        'current_streak': current_streak,
        'longest_streak': longest_streak,
        'completion_eta': completion_eta,
        'days_ahead_behind': days_ahead_behind,
        'is_on_track': is_on_track,
        'track_info': track_info,
    }


def calculate_longest_streak(plan_obj) -> int:
    """
    Calculate the longest consecutive days streak in the entire plan history.

    Args:
        plan_obj: Plan instance with progress data

    Returns:
        Length of longest streak
    """
    if not plan_obj.start_date or not plan_obj.progress:
        return 0

    # Get all dates with progress, sorted
    progress_dates = sorted([datetime.datetime.strptime(d, '%Y-%m-%d') for d in plan_obj.progress.keys()])

    if not progress_dates:
        return 0

    max_streak = 0
    current_streak = 0
    current_date = plan_obj.start_date

    # Check from start date to last progress date
    end_date = max(progress_dates)

    while current_date <= end_date:
        date_key = current_date.strftime('%Y-%m-%d')

        # Writing counts (even on a rest day); rest days without words
        # don't break the streak (P19)
        if plan_obj.progress.get(date_key, 0) > 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        elif not plan_obj.is_rest_day(current_date):
            # Streak broken
            current_streak = 0

        current_date += datetime.timedelta(days=1)

    return max_streak


def calculate_completion_eta(plan_obj) -> Optional[datetime.datetime]:
    """
    Estimate the finishing date at the current pace (A1).

    Spends the average words per writing day on each writing day from today
    on (tomorrow if today's words are already logged), skipping rest days:
    rest days of the plan, then spare days and weekends off after its end.

    Args:
        plan_obj: Plan instance with progress data

    Returns:
        Estimated completion date (midnight), or None if there's no pace yet
    """
    if not plan_obj.start_date or not plan_obj.progress:
        return None

    remaining = plan_obj.get_remaining_words()
    if remaining <= 0:
        return _today()  # Already completed

    average_per_day = average_words_per_writing_day(plan_obj)
    if average_per_day <= 0:
        return None

    day = plan_obj.default_recalculation_date()
    for _ in range(config.MAX_DAYS):
        if not _is_future_rest_day(plan_obj, day):
            remaining -= average_per_day
            if remaining <= 1e-9:
                return day
        day += datetime.timedelta(days=1)
    return None


def display_statistics(plan_obj):
    """
    Display comprehensive statistics in a formatted table.

    Args:
        plan_obj: Plan instance with progress data
    """
    stats = calculate_statistics(plan_obj)

    table = Table(title="Writing Analytics", box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    # Basic progress
    table.add_row("Total Words Written", f"{stats['total_written']:,.0f}")
    table.add_row("Total Goal", f"{plan_obj.total:,.0f}")
    table.add_row("Remaining", f"{plan_obj.get_remaining_words():,.0f}")
    table.add_row("Completion", f"{plan_obj.get_completion_percentage():.1f}%")

    table.add_section()

    # Daily statistics
    table.add_row("Days with Progress", str(stats['days_recorded']))
    table.add_row("Average per Writing Day", f"{stats['average_per_day']:,.0f} words")
    table.add_row("Planned Daily Goal", f"{plan_obj.daily:,.0f} words")

    if stats['best_day']:
        date_str, word_count = stats['best_day']
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        table.add_row("Best Day", f"{date_obj.strftime('%a %b %d')}: {word_count:,.0f} words")

    if stats['worst_day'] and stats['worst_day'] != stats['best_day']:
        date_str, word_count = stats['worst_day']
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        table.add_row("Worst Day", f"{date_obj.strftime('%a %b %d')}: {word_count:,.0f} words")

    table.add_section()

    # Streaks
    table.add_row("Current Streak", f"{stats['current_streak']} days")
    table.add_row("Longest Streak", f"{stats['longest_streak']} days")

    table.add_section()

    # Progress tracking
    if stats['is_on_track']:
        status_text = "ON TRACK"
        if stats['days_ahead_behind'] > 0:
            status_text = f"AHEAD by {abs(stats['days_ahead_behind']):.1f} writing days"
        table.add_row("Schedule Status", f"[green]{status_text}[/green]")
    else:
        status_text = f"BEHIND by {abs(stats['days_ahead_behind']):.1f} writing days"
        table.add_row("Schedule Status", f"[red]{status_text}[/red]")

    # ETA
    if stats['completion_eta']:
        eta_date = stats['completion_eta']
        days_until = (eta_date - _today()).days
        table.add_row("Estimated Completion", f"{eta_date.strftime('%Y-%m-%d')} ({days_until} days)")

    console.print(table)


def plot_cumulative_progress(plan_obj):
    """
    Display a line graph showing expected vs actual cumulative word count over time.

    Args:
        plan_obj: Plan instance with progress data
    """
    if not plan_obj.start_date:
        print("Cannot generate graph: No start date set")
        return

    # Generate data points
    dates = []
    expected_cumulative = []
    actual_cumulative = []

    current_date = plan_obj.start_date
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Calculate end date (the later of today or plan end)
    plan_end = plan_obj.end_date or current_date
    end_date = max(today, plan_end)

    expected_total = 0
    actual_total = 0
    day_index = 0

    day_numbers = []
    date_labels = []
    day_num = 0

    while current_date <= end_date:
        day_numbers.append(day_num)
        date_labels.append(current_date.strftime('%m/%d'))

        # Calculate expected
        if day_index < plan_obj.time and not plan_obj.is_spare_day(current_date):
            expected_total += plan_obj.get_daily_goal(date=current_date)
            day_index += 1

        expected_cumulative.append(expected_total)

        # Calculate actual
        progress = plan_obj.get_progress_for_date(current_date)
        if progress:
            actual_total += progress

        actual_cumulative.append(actual_total)

        current_date += datetime.timedelta(days=1)
        day_num += 1

    # Create plot
    plt.clear_figure()
    plt.plot_size(width=100, height=25)

    plt.plot(day_numbers, expected_cumulative, label="Expected", marker="dot")
    plt.plot(day_numbers, actual_cumulative, label="Actual", marker="dot")

    plt.title("Cumulative Word Count: Expected vs Actual")
    plt.xlabel("Date")
    plt.ylabel("Total Words")

    # Show fewer x-axis labels to avoid clutter
    tick_interval = max(1, len(date_labels) // 10)
    plt.xticks([day_numbers[i] for i in range(0, len(day_numbers), tick_interval)],
               [date_labels[i] for i in range(0, len(date_labels), tick_interval)])

    plt.show()
    print()  # Add spacing


def plot_daily_progress(plan_obj):
    """
    Display a bar graph showing daily words written vs planned goals.

    Args:
        plan_obj: Plan instance with progress data
    """
    if not plan_obj.start_date or not plan_obj.progress:
        print("Cannot generate graph: No progress data")
        return

    # Every elapsed writing day, so missed days show as 0 (A1)
    elapsed = elapsed_writing_days(plan_obj)

    if not elapsed:
        print("No progress data to display")
        return

    # Limit to the last 30 days
    display_dates = elapsed[-30:]

    day_numbers = []
    dates_str = []
    planned = []
    actual = []

    for idx, date in enumerate(display_dates):
        day_numbers.append(idx)
        dates_str.append(date.strftime('%m/%d'))
        planned.append(plan_obj.get_daily_goal(date=date))
        actual_progress = plan_obj.get_progress_for_date(date) or 0
        actual.append(actual_progress)

    # Create plot
    plt.clear_figure()
    plt.plot_size(width=100, height=25)

    plt.multiple_bar(dates_str, [planned, actual], labels=["Planned", "Actual"])

    plt.title("Daily Word Count: Planned vs Actual (Last 30 Days)")
    plt.xlabel("Date")
    plt.ylabel("Words")

    # Show fewer x-axis labels
    tick_interval = max(1, len(dates_str) // 10)
    if tick_interval > 1:
        plt.xticks([dates_str[i] for i in range(0, len(dates_str), tick_interval)])

    plt.show()
    print()


def plot_velocity(plan_obj):
    """
    Display a line graph showing writing velocity (words per day) over time.
    Uses a 3-day moving average to smooth out variations.

    Args:
        plan_obj: Plan instance with progress data
    """
    if not plan_obj.start_date or not plan_obj.progress:
        print("Cannot generate graph: No progress data")
        return

    # Every elapsed writing day, with 0 on days without words, so gaps show (A1)
    days = elapsed_writing_days(plan_obj)

    if len(days) < 3:
        print("Need at least 3 days of progress data for velocity graph")
        return

    words = [plan_obj.get_progress_for_date(d) or 0 for d in days]
    goals = [plan_obj.get_daily_goal(date=d) for d in days]

    day_numbers = []
    dates_str = []
    velocities = []
    target = []

    # 3-day moving average of words and of the planned goals
    window_size = 3
    for i in range(len(days) - window_size + 1):
        velocities.append(sum(words[i:i + window_size]) / window_size)
        target.append(sum(goals[i:i + window_size]) / window_size)

        # Use the middle date of the window
        middle_date = days[i + window_size // 2]
        day_numbers.append(i)
        dates_str.append(middle_date.strftime('%m/%d'))

    # Create plot
    plt.clear_figure()
    plt.plot_size(width=100, height=25)

    plt.plot(day_numbers, velocities, label="Velocity (3-day avg)", marker="dot")
    plt.plot(day_numbers, target, label="Target", marker="dot")

    plt.title("Writing Velocity Over Time")
    plt.xlabel("Date")
    plt.ylabel("Words per Day (3-day average)")

    # Show fewer x-axis labels
    tick_interval = max(1, len(dates_str) // 10)
    plt.xticks([day_numbers[i] for i in range(0, len(day_numbers), tick_interval)],
               [dates_str[i] for i in range(0, len(dates_str), tick_interval)])

    plt.show()
    print()


def plot_milestone_progress(plan_obj):
    """
    Display a horizontal bar chart showing progress toward milestones.

    Args:
        plan_obj: Plan instance with progress data
    """
    if not plan_obj.start_date:
        print("Cannot generate graph: No start date set")
        return

    # Define milestones
    milestones = [25, 50, 75, 100]
    milestone_labels = ["25%", "50%", "75%", "100%"]

    completion = plan_obj.get_completion_percentage()

    # Calculate progress toward each milestone
    progress_values = []
    for milestone in milestones:
        if completion >= milestone:
            progress_values.append(100)  # Fully reached
        elif completion >= milestone - 25:
            # Partial progress toward this milestone
            progress_in_quarter = ((completion - (milestone - 25)) / 25) * 100
            progress_values.append(progress_in_quarter)
        else:
            progress_values.append(0)  # Not reached yet

    # Create plot
    plt.clear_figure()
    plt.plot_size(width=100, height=15)

    plt.bar(milestone_labels, progress_values)

    plt.title(f"Milestone Progress (Current: {completion:.1f}%)")
    plt.xlabel("Progress")

    plt.show()
    print()


def show_analytics_menu(plan_obj):
    """
    Display an interactive menu for viewing different analytics and graphs.

    Args:
        plan_obj: Plan instance with progress data
    """
    while True:
        print("\n" + "=" * 50)
        print("PROGRESS GRAPHS & ANALYTICS")
        print("=" * 50)

        if not plan_obj.progress:
            print("\nNo progress data available yet.")
            print("Record some progress first to see graphs and analytics.")
            input("\nPress Enter to return...")
            return

        print("\nStatistics & Analytics:")
        print("1. View statistics summary")
        print("\nGraphs:")
        print("2. Cumulative progress (Expected vs Actual)")
        print("3. Daily progress bar chart")
        print("4. Writing velocity over time")
        print("5. Milestone progress chart")
        print("\nOptions:")
        print("6. View all graphs")
        print("0. Back to plan menu")
        print("=" * 50)

        try:
            sys.stdout.flush()
            sys.stderr.flush()
            choice = get_menu_choice("\nEnter your choice (0-6): ", 0, 6)

            if choice == 0:
                return
            elif choice == 1:
                print()
                display_statistics(plan_obj)
                sys.stdout.flush()
                input("\nPress Enter to continue...")
            elif choice == 2:
                print()
                try:
                    plot_cumulative_progress(plan_obj)
                except Exception as e:
                    print(f"Error generating graph: {e}")
                sys.stdout.flush()
                input("Press Enter to continue...")
            elif choice == 3:
                print()
                try:
                    plot_daily_progress(plan_obj)
                except Exception as e:
                    print(f"Error generating graph: {e}")
                sys.stdout.flush()
                input("Press Enter to continue...")
            elif choice == 4:
                print()
                try:
                    plot_velocity(plan_obj)
                except Exception as e:
                    print(f"Error generating graph: {e}")
                sys.stdout.flush()
                input("Press Enter to continue...")
            elif choice == 5:
                print()
                try:
                    plot_milestone_progress(plan_obj)
                except Exception as e:
                    print(f"Error generating graph: {e}")
                sys.stdout.flush()
                input("Press Enter to continue...")
            elif choice == 6:
                print()
                display_statistics(plan_obj)
                sys.stdout.flush()
                input("\nPress Enter to view graphs...")
                print()
                plot_cumulative_progress(plan_obj)
                plot_daily_progress(plan_obj)
                plot_velocity(plan_obj)
                plot_milestone_progress(plan_obj)
                sys.stdout.flush()
                input("Press Enter to continue...")
        except ValueError as e:
            # Menu choices are validated by get_menu_choice; this catches the rest
            print(f"Error: {e}")
