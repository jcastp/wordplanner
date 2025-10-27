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

    # Calculate end date
    end_date = start_date + timedelta(days=int(plan_obj.time) - 1)

    # Display plan summary
    console.print()
    summary = Panel(
        f"[bold cyan]Total Words:[/bold cyan] {plan_obj.total:,.0f}\n"
        f"[bold green]Daily Goal:[/bold green] {plan_obj.daily:,.0f} words/day\n"
        f"[bold yellow]Duration:[/bold yellow] {plan_obj.time:.0f} days\n"
        f"[bold magenta]Start Date:[/bold magenta] {start_date.strftime('%B %d, %Y')}\n"
        f"[bold magenta]End Date:[/bold magenta] {end_date.strftime('%B %d, %Y')}",
        title="[bold]Your Writing Plan[/bold]",
        border_style="blue"
    )
    console.print(summary)
    console.print()

    # Group days by month
    current_date = start_date
    days_remaining = int(plan_obj.time)
    max_months = 24  # Safety limit: don't show more than 24 months
    months_shown = 0

    while days_remaining > 0 and months_shown < max_months:
        months_shown += 1
        # Safety check: if current_date is past end_date, break to prevent infinite loop
        first_of_month = datetime(current_date.year, current_date.month, 1)
        if first_of_month > end_date:
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

                    # Check if this day is in our writing plan
                    if start_date <= day_date <= end_date:
                        # Calculate cumulative words by this date
                        days_elapsed = (day_date - start_date).days + 1
                        cumulative_words = int(days_elapsed * plan_obj.daily)

                        # Format the cell
                        cell_text = Text()
                        cell_text.append(f"{day}\n", style="bold white")
                        cell_text.append(f"{plan_obj.daily:,.0f}w", style="green")
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
    display_milestones(console, plan_obj, start_date, end_date)


def display_milestones(console, plan_obj, start_date, end_date):
    """Display milestone information."""
    table = Table(title="[bold cyan]Milestones[/bold cyan]",
                 border_style="green",
                 show_header=True,
                 header_style="bold magenta")

    table.add_column("Progress", justify="center", style="cyan")
    table.add_column("Date", justify="center", style="yellow")
    table.add_column("Words Written", justify="right", style="green")
    table.add_column("Days Elapsed", justify="center", style="white")

    # Calculate milestones at 25%, 50%, 75%, 100%
    milestones = [0.25, 0.50, 0.75, 1.0]

    for milestone in milestones:
        days_to_milestone = int(plan_obj.time * milestone)
        words_at_milestone = int(plan_obj.total * milestone)
        date_at_milestone = start_date + timedelta(days=days_to_milestone - 1)

        table.add_row(
            f"{int(milestone * 100)}%",
            date_at_milestone.strftime("%b %d, %Y"),
            f"{words_at_milestone:,}",
            f"{days_to_milestone}"
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
    table.add_column("Daily Goal", justify="right", style="green", width=15)
    table.add_column("Weekly Total", justify="right", style="bold green", width=15)
    table.add_column("Cumulative", justify="right", style="bold cyan", width=15)

    current_date = start_date
    days_remaining = int(plan_obj.time)
    week_num = 1
    cumulative_words = 0

    while days_remaining > 0:
        # Calculate days in this week
        days_in_week = min(7, days_remaining)
        week_end = current_date + timedelta(days=days_in_week - 1)

        # Calculate words for this week
        weekly_words = int(plan_obj.daily * days_in_week)
        cumulative_words += weekly_words

        # Format date range
        date_range = f"{current_date.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}"

        table.add_row(
            f"{week_num}",
            date_range,
            f"{plan_obj.daily:,.0f}",
            f"{weekly_words:,}",
            f"{cumulative_words:,}"
        )

        current_date = week_end + timedelta(days=1)
        days_remaining -= days_in_week
        week_num += 1

    console.print()
    console.print(table)
    console.print()
