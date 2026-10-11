"""Calendar view module for displaying writing plans."""

import calendar
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


def get_date_input(prompt):
    """Get a valid date from user input."""
    while True:
        date_str = input(prompt)
        try:
            # Try parsing different date formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            # If we get here, no format worked
            print("Invalid date format. Please use YYYY-MM-DD (e.g., 2025-11-01)")
        except Exception as e:
            print(f"Error parsing date: {e}")


def display_calendar_view(plan_obj, start_date):
    """
    Display a beautiful calendar view of the writing plan.

    Args:
        plan_obj: Plan object with total, daily, and time attributes
        start_date: datetime object for when to start the plan
    """
    console = Console()

    # Plan window (a plan with no writing days ends before it starts)
    total_days = plan_obj.total_calendar_days
    final_end_date = plan_obj.end_date or start_date - timedelta(days=1)

    # Display plan summary
    console.print()

    # Format daily goal display based on pattern
    if plan_obj.pattern == "flat":
        daily_goal_text = f"{plan_obj.daily:,.0f} words/day"
    else:
        daily_goal_text = f"{plan_obj.daily:,.0f} words/day (average, {plan_obj.pattern} pattern)"

    summary_text = (
        f"[bold cyan]Total Words:[/bold cyan] {plan_obj.total:,.0f}\n"
        f"[bold green]Daily Goal:[/bold green] {daily_goal_text}\n"
        f"[bold yellow]Writing Days:[/bold yellow] {plan_obj.time:.0f} days\n"
    )
    if plan_obj.spare_days > 0:
        summary_text += f"[bold orange1]Spare Days:[/bold orange1] {plan_obj.spare_days:.0f} days (0 words)\n"
        summary_text += f"[bold yellow]Total Duration:[/bold yellow] {total_days:.0f} days\n"

    summary_text += (
        f"[bold magenta]Start Date:[/bold magenta] {start_date.strftime('%B %d, %Y')}\n"
        f"[bold magenta]End Date:[/bold magenta] {final_end_date.strftime('%B %d, %Y')}"
    )

    # Add progress information if any progress has been recorded
    if plan_obj.progress:
        total_written = plan_obj.get_total_written()
        completion = plan_obj.get_completion_percentage()
        on_track, info = plan_obj.is_on_track()

        summary_text += "\n\n[bold white]Progress:[/bold white]\n"
        summary_text += f"  Written: {total_written:,} words ({completion:.1f}%)\n"
        summary_text += f"  Remaining: {plan_obj.get_remaining_words():,} words\n"

        if info.get('status'):
            if info['status'] == 'ahead':
                summary_text += f"  [bold green]✓ AHEAD[/bold green] by {info['difference']:,.0f} words"
            elif info['status'] == 'on_track':
                summary_text += f"  [bold green]✓ ON TRACK[/bold green]"
            else:
                summary_text += f"  [bold red]⚠ BEHIND[/bold red] by {abs(info['difference']):,.0f} words"

    summary = Panel(summary_text, title="[bold]Your Writing Plan[/bold]", border_style="blue")
    console.print(summary)
    console.print()

    # Group days by month
    current_date = start_date
    days_remaining = total_days  # Include spare days in calendar
    max_months = 24  # Safety limit: don't show more than 24 months
    months_shown = 0

    while days_remaining > 0 and months_shown < max_months:
        months_shown += 1
        # Safety check: if current_date is past final_end_date, break to prevent infinite loop
        first_of_month = datetime(current_date.year, current_date.month, 1)
        if first_of_month > final_end_date:
            break

        # Create a table for this month
        month_name = current_date.strftime("%B %Y")
        table = Table(title=f"[bold cyan]{month_name}[/bold cyan]",
                     show_header=True,
                     header_style="bold magenta",
                     border_style="blue")

        # Add columns for days of the week
        table.add_column("Week", style="cyan", justify="center", width=6)
        table.add_column("Mon", justify="center", width=12)
        table.add_column("Tue", justify="center", width=12)
        table.add_column("Wed", justify="center", width=12)
        table.add_column("Thu", justify="center", width=12)
        table.add_column("Fri", justify="center", width=12)
        table.add_column("Sat", justify="center", width=12, style="yellow")
        table.add_column("Sun", justify="center", width=12, style="yellow")

        # Get calendar for this month
        cal = calendar.monthcalendar(current_date.year, current_date.month)

        # Track if we added any days in this month
        days_added_this_month = 0

        # Process each week
        week_num = 1
        for week in cal:
            row = [f"W{week_num}"]
            week_num += 1

            for day in week:
                if day == 0:
                    # Empty day (from previous/next month)
                    row.append("")
                else:
                    # Create date for this day
                    day_date = datetime(current_date.year, current_date.month, day)

                    # Check if this day is in our writing plan (including spare days)
                    if start_date <= day_date <= final_end_date:
                        # Format the cell
                        cell_text = Text()
                        cell_text.append(f"{day}\n", style="bold white")

                        # Check if this specific date is a spare day
                        if plan_obj.is_spare_day(day_date):
                            # Spare day
                            cell_text.append("SPARE", style="orange1 italic")
                        else:
                            # Writing day - use pattern-based goal
                            daily_goal = plan_obj.get_daily_goal(date=day_date)

                            # Get progress status for this date
                            progress_status = plan_obj.get_progress_status_for_date(day_date)

                            # Determine style based on progress status
                            if progress_status == 'exceeded':
                                style = "bold green"
                                actual = plan_obj.get_progress_for_date(day_date)
                                cell_text.append(f"{daily_goal:,.0f}w\n", style="dim white")
                                cell_text.append(f"✓{actual:,.0f}", style=style)
                            elif progress_status == 'met':
                                style = "green"
                                cell_text.append(f"{daily_goal:,.0f}w\n", style="dim white")
                                cell_text.append("✓", style=style)
                            elif progress_status == 'partial':
                                style = "yellow"
                                actual = plan_obj.get_progress_for_date(day_date)
                                cell_text.append(f"{daily_goal:,.0f}w\n", style="dim white")
                                cell_text.append(f"~{actual:,.0f}", style=style)
                            elif progress_status == 'missed':
                                style = "red"
                                cell_text.append(f"{daily_goal:,.0f}w\n", style="dim white")
                                cell_text.append("✗", style=style)
                            elif progress_status == 'future':
                                style = "blue"
                                cell_text.append(f"{daily_goal:,.0f}w", style=style)
                            elif progress_status == 'spare':
                                # Rest day: weekend rest or a goal of 0
                                cell_text.append("REST", style="orange1 italic")
                            else:
                                # No goal or other status
                                cell_text.append(f"{daily_goal:,.0f}w", style="green")

                        row.append(cell_text)

                        days_remaining -= 1
                        days_added_this_month += 1
                        if days_remaining == 0:
                            break
                    else:
                        # Day not in plan
                        row.append(f"{day}")

            table.add_row(*row)

            if days_remaining == 0:
                break

        # Print the table for this month before checking if we're done
        console.print(table)
        console.print()

        # Safety check: if we didn't add any days this month, we've gone past the plan
        if days_added_this_month == 0:
            break

        # Exit if we've finished all days
        if days_remaining <= 0:
            break

        # Move to next month
        if current_date.month == 12:
            current_date = datetime(current_date.year + 1, 1, 1)
        else:
            current_date = datetime(current_date.year, current_date.month + 1, 1)

    # Display progress milestones
    display_milestones(console, plan_obj, start_date, final_end_date)


def format_milestone_date(milestone):
    """A milestone's date, or a note when pre-existing words already reach it."""
    if milestone['date'] is None:
        return "before the start"
    return milestone['date'].strftime("%b %d, %Y")


def display_milestones(console, plan_obj, start_date, end_date):
    """Display milestone information."""
    table = Table(title="[bold cyan]Milestones[/bold cyan]",
                 border_style="green",
                 show_header=True,
                 header_style="bold magenta")

    table.add_column("Progress", justify="center", style="cyan")
    table.add_column("Date", justify="center", style="yellow")
    table.add_column("Words Written", justify="right", style="green")
    table.add_column("Plan Day", justify="center", style="white")
    table.add_column("Status", justify="center")

    # 25%, 50%, 75%, 100%, following the schedule
    for milestone in plan_obj.milestones():
        table.add_row(
            f"{int(milestone['fraction'] * 100)}%",
            format_milestone_date(milestone),
            f"{milestone['words']:,}",
            str(milestone['day']) if milestone['day'] else "-",
            "[green]✓ reached[/green]" if milestone['reached'] else ""
        )

    console.print(table)
    console.print()


def display_weekly_summary(plan_obj, start_date):
    """Display a week-by-week summary of the writing plan."""
    console = Console()

    table = Table(title="[bold cyan]Weekly Summary[/bold cyan]",
                 border_style="blue",
                 show_header=True,
                 header_style="bold magenta")

    table.add_column("Week", justify="center", style="cyan", width=8)
    table.add_column("Dates", justify="center", style="yellow", width=30)
    table.add_column("Writing Days", justify="center", style="green", width=15)
    table.add_column("Spare Days", justify="center", style="orange1", width=12)
    table.add_column("Daily Goal", justify="right", style="green", width=15)
    table.add_column("Weekly Total", justify="right", style="bold green", width=15)
    table.add_column("Cumulative", justify="right", style="bold cyan", width=15)

    total_days = plan_obj.total_calendar_days
    current_date = start_date
    week_num = 1
    cumulative_words = 0
    days_remaining = total_days

    while days_remaining > 0:
        # Calculate days in this week
        days_in_week = min(7, days_remaining)
        week_end = current_date + timedelta(days=days_in_week - 1)

        # Count writing days and spare days in this week, and sum daily goals
        writing_days_in_week = 0
        spare_days_in_week = 0
        weekly_words = 0
        daily_goals_in_week = []

        check_date = current_date
        for i in range(days_in_week):
            if plan_obj.is_spare_day(check_date):
                spare_days_in_week += 1
            else:
                writing_days_in_week += 1
                daily_goal = plan_obj.get_daily_goal(date=check_date)
                daily_goals_in_week.append(daily_goal)
                weekly_words += daily_goal
            check_date += timedelta(days=1)

        cumulative_words += int(weekly_words)

        # Calculate average daily goal for this week (for display)
        avg_daily_goal = sum(daily_goals_in_week) / len(daily_goals_in_week) if daily_goals_in_week else 0

        # Format date range
        date_range = f"{current_date.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}"

        # If pattern is flat, show single value; otherwise show average or range
        if plan_obj.pattern == "flat":
            daily_goal_str = f"{plan_obj.daily:,.0f}"
        else:
            if daily_goals_in_week:
                min_goal = min(daily_goals_in_week)
                max_goal = max(daily_goals_in_week)
                if abs(max_goal - min_goal) < 1:  # Nearly the same
                    daily_goal_str = f"{avg_daily_goal:,.0f}"
                else:
                    daily_goal_str = f"{min_goal:,.0f}-{max_goal:,.0f}"
            else:
                daily_goal_str = "-"

        table.add_row(
            f"{week_num}",
            date_range,
            f"{writing_days_in_week}",
            f"{spare_days_in_week}" if spare_days_in_week > 0 else "-",
            daily_goal_str,
            f"{int(weekly_words):,}",
            f"{cumulative_words:,}"
        )

        current_date = week_end + timedelta(days=1)
        days_remaining -= days_in_week
        week_num += 1

    console.print()
    console.print(table)
    console.print()
