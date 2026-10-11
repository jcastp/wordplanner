"""Calendar view module for displaying writing plans."""

import calendar
from datetime import datetime, timedelta
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import plan
import user_preferences
from formatting import make_console

# Width of a day column in the monthly calendar
DAY_CELL_WIDTH = 12

DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def first_weekday():
    """The first column of the monthly calendar: 0 (Monday) or 6 (Sunday), from Settings."""
    return user_preferences.get_preference('first_weekday')


def week_order():
    """Weekdays (0 = Monday) in calendar column order."""
    first = first_weekday()
    return [(first + i) % 7 for i in range(7)]


def day_number(day_date, style=""):
    """
    The first line of a calendar cell: the day of the month, marked when it's today.

    Today is shown in reverse video with the word TODAY, so it stands out
    with or without colors (NO_COLOR keeps reverse and bold).
    """
    text = Text()
    if day_date == plan.today():
        text.append(f" {day_date.day} ", style="bold reverse")
        text.append(" TODAY", style="bold")
    else:
        text.append(str(day_date.day), style=style)
    return text


def running_total(plan_obj, day_date, width=DAY_CELL_WIDTH):
    """
    The words written by the end of day_date against the total, for a calendar cell.

    Counts pre-existing words and every entry up to that day, so the last
    logged day matches the plan summary. Days still to come (after today,
    or today with nothing logged) have none, nor does a plan with no progress.

    Returns:
        ("2,100/80,000", "2.63%"), or None. A fraction wider than the cell
        is shortened to thousands ("102.3k/150k").
    """
    if not plan_obj.progress:
        return None
    today = plan.today()
    if day_date > today or (day_date == today and plan_obj.get_progress_for_date(today) is None):
        return None

    written = plan_obj.get_total_written(through=day_date)
    fraction = f"{written:,.0f}/{plan_obj.total:,.0f}"
    if len(fraction) > width:
        fraction = f"{written / 1000:,.1f}k/{plan_obj.total / 1000:,.0f}k"
    return fraction, f"{plan_obj.get_completion_percentage(through=day_date):.2f}%"


def display_calendar_view(plan_obj, start_date):
    """
    Display a beautiful calendar view of the writing plan.

    Args:
        plan_obj: Plan object with total, daily, and time attributes
        start_date: datetime object for when to start the plan
    """
    console = make_console()

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
        summary_text += f"  Written: {total_written:,.0f} words ({completion:.1f}%)\n"
        summary_text += f"  Remaining: {plan_obj.get_remaining_words():,.0f} words\n"

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
        for weekday in week_order():
            table.add_column(DAY_NAMES[weekday], justify="center", width=DAY_CELL_WIDTH,
                             style="yellow" if weekday >= 5 else None)

        # Get calendar for this month, weeks starting on the chosen day
        cal = calendar.Calendar(first_weekday()).monthdayscalendar(current_date.year, current_date.month)

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
                        cell_text = day_number(day_date, style="bold white")
                        cell_text.append("\n")

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

                        running = running_total(plan_obj, day_date)
                        if running:
                            written, percent = running
                            cell_text.append(f"\n{written}\n{percent}", style="cyan")

                        row.append(cell_text)

                        days_remaining -= 1
                        days_added_this_month += 1
                        if days_remaining == 0:
                            break
                    else:
                        # Day not in plan
                        row.append(day_number(day_date))

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
    table.add_column("Target", justify="right", style="green")
    table.add_column("Written", justify="right", style="bold white")
    table.add_column("Plan Day", justify="center", style="white")
    table.add_column("Status", justify="center")

    # Words written so far, pre-existing words included (like the targets)
    written = plan_obj.get_total_written()

    # 25%, 50%, 75%, 100%, following the schedule
    for milestone in plan_obj.milestones():
        if milestone['reached']:
            status = "[green]✓ reached[/green]"
        else:
            status = f"{milestone['words'] - written:,.0f} to go"
        table.add_row(
            f"{int(milestone['fraction'] * 100)}%",
            format_milestone_date(milestone),
            f"{milestone['words']:,.0f}",
            f"{written:,.0f}",
            str(milestone['day']) if milestone['day'] else "-",
            status
        )

    console.print(table)
    console.print()


def weekly_summary(plan_obj):
    """
    The plan in 7-day weeks from the start date, with what was written.

    Rest days are days with a goal of 0 (spare days, weekend rest days,
    custom or locked 0). Totals include pre-existing words, like the
    calendar cells and milestones. For the current week, ahead/behind
    compares everything written with the goals up to yesterday, like
    is_on_track() (today isn't expected until it's over).

    Returns:
        A list of dicts, one per week: 'number', 'start', 'end',
        'writing_days', 'rest_days', 'goals' (goals of the writing days),
        'goal' (week's goal), 'planned_total', 'started', 'ended', and for
        started weeks 'written', 'days_written', 'written_total' and
        'difference' (words ahead, negative if behind; None otherwise).
    """
    days = list(plan_obj.plan_days())
    today = plan.today()
    weeks = []

    for number, first in enumerate(range(0, len(days), 7), 1):
        week_days = days[first:first + 7]
        start, end = week_days[0], week_days[-1]
        goals = [plan_obj.get_daily_goal(date=d) for d in week_days]
        week = {
            'number': number,
            'start': start,
            'end': end,
            'writing_days': sum(1 for g in goals if g > 0),
            'rest_days': sum(1 for g in goals if g == 0),
            'goals': [g for g in goals if g > 0],
            'goal': sum(goals),
            'planned_total': plan_obj.get_planned_total(end),
            'started': start <= today,
            'ended': end < today,
            'written': None,
            'days_written': None,
            'written_total': None,
            'difference': None,
        }
        if week['started']:
            before = start - timedelta(days=1)
            week['written'] = plan_obj.get_plan_written(through=end) - plan_obj.get_plan_written(through=before)
            week['days_written'] = sum(1 for d in week_days if (plan_obj.get_progress_for_date(d) or 0) > 0)
            week['written_total'] = plan_obj.get_total_written(through=end)
            # The current week is expected only up to yesterday
            expected_through = end if week['ended'] else today - timedelta(days=1)
            week['difference'] = week['written_total'] - plan_obj.get_planned_total(expected_through)
        weeks.append(week)

    return weeks


def format_week_goal(week):
    """The daily goal of a week's writing days: one value, or the range."""
    if not week['goals']:
        return "-"
    low, high = min(week['goals']), max(week['goals'])
    if high - low < 1:
        return f"{high:,.0f}"
    return f"{low:,.0f}-{high:,.0f}"


def format_week_written(week):
    """Words written in a week, with ✓ / ~ / ✗ and the share of its goal."""
    if not week['started']:
        return ""
    written, goal = week['written'], week['goal']
    if goal > 0 and written >= goal - 0.5:
        icon = "[green]✓[/green]"
    elif not week['ended']:
        icon = ""   # still running
    elif written > 0:
        icon = "[yellow]~[/yellow]"
    else:
        icon = "[red]✗[/red]"
    text = f"{written:,.0f}"
    if icon:
        text += f" {icon}"
    if goal > 0:
        text += f" {written / goal * 100:.0f}%"
    return text


def format_difference(difference):
    """Words ahead (+, green) or behind (-, red)."""
    if difference is None:
        return ""
    if round(difference) > 0:
        return f"[green]+{difference:,.0f}[/green]"
    if round(difference) < 0:
        return f"[red]-{abs(difference):,.0f}[/red]"
    return "0"


def display_weekly_summary(plan_obj, start_date):
    """Display a week-by-week summary of the writing plan, with what was written."""
    console = make_console()
    weeks = weekly_summary(plan_obj)
    if not weeks:
        console.print("\nThis plan has no days to show.")
        return

    first, last = weeks[0]['start'], weeks[-1]['end']
    table = Table(title=f"[bold cyan]Weekly Summary[/bold cyan] "
                        f"({first.strftime('%b %d, %Y')} - {last.strftime('%b %d, %Y')})",
                 border_style="blue",
                 show_header=True,
                 header_style="bold magenta")

    table.add_column("Week", justify="center", style="cyan")
    table.add_column("Dates", justify="center", style="yellow", no_wrap=True)
    table.add_column("Days Written", justify="center", style="green")
    table.add_column("Rest Days", justify="center", style="orange1")
    table.add_column("Daily Goal", justify="right", style="green", no_wrap=True)
    table.add_column("Weekly Goal", justify="right", style="bold green")
    table.add_column("Written", justify="right", no_wrap=True)
    table.add_column("Planned Total", justify="right", style="cyan")
    table.add_column("Actual Total", justify="right", style="bold cyan")
    table.add_column("+/-", justify="right", no_wrap=True)

    for week in weeks:
        if week['started']:
            days_written = f"{week['days_written']}/{week['writing_days']}"
            actual_total = f"{week['written_total']:,.0f}"
        else:
            days_written = f"-/{week['writing_days']}"
            actual_total = ""
        table.add_row(
            str(week['number']),
            f"{week['start'].strftime('%b %d')} - {week['end'].strftime('%b %d')}",
            days_written,
            str(week['rest_days']) if week['rest_days'] else "-",
            format_week_goal(week),
            f"{week['goal']:,.0f}",
            format_week_written(week),
            f"{week['planned_total']:,.0f}",
            actual_total,
            format_difference(week['difference']),
        )

    console.print()
    console.print(table)
    console.print()
