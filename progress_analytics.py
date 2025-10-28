"""Progress analytics and visualization module for writing plans."""

import datetime
import sys
from typing import Dict, List, Tuple, Optional
import plotext as plt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box


console = Console()


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

    # Average words per day (only counting days with progress)
    average_per_day = total_written / days_recorded if days_recorded > 0 else 0

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
    days_ahead_behind = track_info.get('difference', 0) / plan_obj.daily if plan_obj.daily > 0 else 0

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

        # Skip spare days - they don't break the streak
        if plan_obj.is_spare_day(current_date):
            current_date += datetime.timedelta(days=1)
            continue

        # Check if progress was recorded for this day
        if date_key in plan_obj.progress and plan_obj.progress[date_key] > 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            # Streak broken
            current_streak = 0

        current_date += datetime.timedelta(days=1)

    return max_streak


def calculate_completion_eta(plan_obj) -> Optional[datetime.datetime]:
    """
    Calculate estimated completion date based on current progress velocity.

    Args:
        plan_obj: Plan instance with progress data

    Returns:
        Estimated completion date or None if not enough data
    """
    if not plan_obj.start_date or not plan_obj.progress:
        return None

    total_written = plan_obj.get_total_written()
    remaining = plan_obj.get_remaining_words()

    if remaining <= 0:
        return datetime.datetime.now()  # Already completed

    days_recorded = plan_obj.get_days_with_progress()
    if days_recorded == 0:
        return None

    # Calculate average velocity (words per day)
    average_per_day = total_written / days_recorded

    if average_per_day <= 0:
        return None

    # Estimate days needed
    days_needed = remaining / average_per_day

    # Calculate ETA from today
    today = datetime.datetime.now()
    eta = today + datetime.timedelta(days=days_needed)

    return eta


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
    table.add_row("Average per Day", f"{stats['average_per_day']:,.0f} words")
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
            status_text = f"AHEAD by {abs(stats['days_ahead_behind']):.1f} days"
        table.add_row("Schedule Status", f"[green]{status_text}[/green]")
    else:
        status_text = f"BEHIND by {abs(stats['days_ahead_behind']):.1f} days"
        table.add_row("Schedule Status", f"[red]{status_text}[/red]")

    # ETA
    if stats['completion_eta']:
        eta_date = stats['completion_eta']
        days_until = (eta_date - datetime.datetime.now()).days
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
    plan_end = current_date + datetime.timedelta(days=int(plan_obj.time) + len(plan_obj.spare_days_dates))
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

    # Get dates with progress
    progress_dates = sorted([datetime.datetime.strptime(d, '%Y-%m-%d') for d in plan_obj.progress.keys()])

    if not progress_dates:
        print("No progress data to display")
        return

    # Limit to last 30 days or all progress, whichever is smaller
    display_dates = progress_dates[-30:]

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

    # Get dates with progress
    progress_dates = sorted([datetime.datetime.strptime(d, '%Y-%m-%d') for d in plan_obj.progress.keys()])

    if len(progress_dates) < 3:
        print("Need at least 3 days of progress data for velocity graph")
        return

    day_numbers = []
    dates_str = []
    velocities = []

    # Calculate 3-day moving average
    window_size = 3
    for i in range(len(progress_dates) - window_size + 1):
        window_dates = progress_dates[i:i + window_size]
        window_words = sum(plan_obj.get_progress_for_date(d) or 0 for d in window_dates)
        avg_velocity = window_words / window_size

        # Use the middle date of the window
        middle_date = window_dates[window_size // 2]
        day_numbers.append(i)
        dates_str.append(middle_date.strftime('%m/%d'))
        velocities.append(avg_velocity)

    # Add target line (average daily goal)
    target = [plan_obj.daily] * len(velocities)

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
            choice_str = input("\nEnter your choice (0-6): ").strip()
            if not choice_str:
                print("Please enter a number.")
                continue
            choice = int(choice_str)

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
            else:
                print("Invalid choice. Please try again.")
        except ValueError as e:
            print(f"Invalid input. Please enter a number. (Error: {e})")
        except KeyboardInterrupt:
            print("\nReturning to plan menu...")
            return
