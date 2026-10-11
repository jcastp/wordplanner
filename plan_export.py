"""Export functionality for writing plans."""

import csv
from datetime import datetime, timedelta
from pathlib import Path
import plan
import config
import user_preferences


def get_exports_directory():
    """
    Get or create the exports directory.

    Checks user preferences for a custom save directory first.
    If not set, uses the default from config.

    Raises:
        PermissionError: If directory cannot be created due to permissions
        OSError: If directory creation fails for other reasons
    """
    # Check for custom save directory in user preferences
    custom_dir = user_preferences.get_custom_save_directory()

    if custom_dir:
        # Use custom directory with exports subdirectory
        exports_dir = Path(custom_dir) / config.EXPORTS_SUBDIRECTORY
    else:
        # Otherwise, use default behavior
        save_dir = Path(config.SAVE_DIRECTORY)

        # If SAVE_DIRECTORY is absolute (for testing), use it directly
        if save_dir.is_absolute():
            exports_dir = save_dir / config.EXPORTS_SUBDIRECTORY
        else:
            # Otherwise, use it relative to home directory (normal usage)
            exports_dir = Path.home() / config.SAVE_DIRECTORY / config.EXPORTS_SUBDIRECTORY

    try:
        exports_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise PermissionError(f"Permission denied: Cannot create exports directory at {exports_dir}")
    except OSError as e:
        raise OSError(f"Failed to create exports directory: {e}")

    return exports_dir


def export_to_csv(plan_obj, filepath=None):
    """
    Export plan to CSV format.

    Columns: Date, Day_of_Week, Day_Number, Daily_Goal, Actual_Words,
             Cumulative_Goal, Cumulative_Actual, Status

    Args:
        plan_obj: Plan object to export
        filepath: Optional custom filepath (defaults to exports directory)

    Returns:
        Path to the exported file
    """
    if not plan_obj.start_date:
        raise ValueError("Plan must have a start date to export")

    # Determine filepath
    if filepath is None:
        filename = f"{plan_obj.name or 'plan'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filename = filename.replace(' ', '_')
        filepath = get_exports_directory() / filename
    else:
        filepath = Path(filepath)

    # Calculate total days including spare days
    total_days = plan_obj.total_calendar_days

    # Prepare data
    rows = []
    cumulative_goal = 0
    cumulative_actual = 0
    writing_day_number = 0

    for day_idx in range(total_days):
        current_date = plan_obj.start_date + timedelta(days=day_idx)
        date_str = current_date.strftime('%Y-%m-%d')
        day_of_week = current_date.strftime('%A')

        # Check if spare day
        is_spare = plan_obj.is_spare_day(current_date)

        if is_spare:
            daily_goal = 0
            day_type = "Spare"
        else:
            writing_day_number += 1
            daily_goal = plan_obj.get_daily_goal(date=current_date)
            cumulative_goal += daily_goal
            day_type = "Writing"

        # Get actual progress
        actual_words = plan_obj.get_progress_for_date(current_date)
        if actual_words is None:
            actual_words = 0

        cumulative_actual += actual_words

        # Determine status
        status = plan_obj.get_progress_status_for_date(current_date)

        rows.append({
            'Date': date_str,
            'Day_of_Week': day_of_week,
            'Day_Number': writing_day_number if not is_spare else '',
            'Day_Type': day_type,
            'Daily_Goal': f'{daily_goal:.0f}' if daily_goal > 0 else '0',
            'Actual_Words': f'{actual_words:.0f}' if actual_words > 0 else '',
            'Cumulative_Goal': f'{cumulative_goal:.0f}',
            'Cumulative_Actual': f'{cumulative_actual:.0f}',
            'Status': status.capitalize()
        })

    # Write to CSV
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['Date', 'Day_of_Week', 'Day_Number', 'Day_Type', 'Daily_Goal',
                         'Actual_Words', 'Cumulative_Goal', 'Cumulative_Actual', 'Status']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    except PermissionError:
        raise PermissionError(f"Permission denied: Cannot write to {filepath}")
    except OSError as e:
        raise OSError(f"Failed to write CSV file {filepath}: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error writing CSV: {e}")

    return filepath


def export_to_ical(plan_obj, filepath=None):
    """
    Export plan to iCal/ICS format for calendar apps.

    Creates daily events with word goals as reminders.

    Args:
        plan_obj: Plan object to export
        filepath: Optional custom filepath (defaults to exports directory)

    Returns:
        Path to the exported file
    """
    if not plan_obj.start_date:
        raise ValueError("Plan must have a start date to export")

    # Determine filepath
    if filepath is None:
        filename = f"{plan_obj.name or 'plan'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
        filename = filename.replace(' ', '_')
        filepath = get_exports_directory() / filename
    else:
        filepath = Path(filepath)

    # Calculate total days including spare days
    total_days = plan_obj.total_calendar_days

    # Start building iCal content
    ical_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//wordplanner//Writing Plan//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{plan_obj.name or 'Writing Plan'}",
        "X-WR-TIMEZONE:UTC",
        "X-WR-CALDESC:Writing plan generated by wordplanner"
    ]

    now = datetime.utcnow()
    dtstamp = now.strftime('%Y%m%dT%H%M%SZ')

    writing_day_number = 0

    for day_idx in range(total_days):
        current_date = plan_obj.start_date + timedelta(days=day_idx)

        # Check if spare day
        is_spare = plan_obj.is_spare_day(current_date)

        if is_spare:
            # Create event for spare day
            date_str = current_date.strftime('%Y%m%d')
            uid = f"spare-{plan_obj.name or 'plan'}-{date_str}@wordplanner"

            ical_lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{dtstamp}",
                f"DTSTART;VALUE=DATE:{date_str}",
                f"DTEND;VALUE=DATE:{date_str}",
                f"SUMMARY:Spare Day - {plan_obj.name or 'Writing Plan'}",
                "DESCRIPTION:Spare day (no writing required)",
                "STATUS:CONFIRMED",
                "TRANSP:TRANSPARENT",
                "END:VEVENT"
            ])
        else:
            # Writing day
            writing_day_number += 1
            daily_goal = plan_obj.get_daily_goal(date=current_date)
            date_str = current_date.strftime('%Y%m%d')
            uid = f"writing-{plan_obj.name or 'plan'}-{date_str}@wordplanner"

            # Create event
            ical_lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{dtstamp}",
                f"DTSTART;VALUE=DATE:{date_str}",
                f"DTEND;VALUE=DATE:{date_str}",
                f"SUMMARY:Write {daily_goal:.0f} words - {plan_obj.name or 'Writing'}",
                f"DESCRIPTION:Writing goal: {daily_goal:.0f} words\\nDay {writing_day_number} of {plan_obj.time}\\nTotal goal: {plan_obj.total:,.0f} words",
                "STATUS:CONFIRMED",
                "TRANSP:OPAQUE",
                "END:VEVENT"
            ])

            # Add reminder (alarm) - 9 AM on the day
            # Note: Some calendar apps may not support alarms in all-day events

    ical_lines.append("END:VCALENDAR")

    # Write to file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\r\n'.join(ical_lines))
    except PermissionError:
        raise PermissionError(f"Permission denied: Cannot write to {filepath}")
    except OSError as e:
        raise OSError(f"Failed to write iCal file {filepath}: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error writing iCal: {e}")

    return filepath


def export_to_markdown(plan_obj, filepath=None):
    """
    Export plan to Markdown format.

    Creates a readable text-based overview of the plan.

    Args:
        plan_obj: Plan object to export
        filepath: Optional custom filepath (defaults to exports directory)

    Returns:
        Path to the exported file
    """
    if not plan_obj.start_date:
        raise ValueError("Plan must have a start date to export")

    # Determine filepath
    if filepath is None:
        filename = f"{plan_obj.name or 'plan'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filename = filename.replace(' ', '_')
        filepath = get_exports_directory() / filename
    else:
        filepath = Path(filepath)

    # Build markdown content
    lines = []

    # Title
    lines.append(f"# {plan_obj.name or 'Writing Plan'}")
    lines.append("")

    # Plan Overview
    lines.append("## Plan Overview")
    lines.append("")
    lines.append(f"- **Total Word Goal**: {plan_obj.total:,} words")
    if plan_obj.preexisting_words:
        lines.append(f"- **Written Before the Plan**: {plan_obj.preexisting_words:,} words")
    lines.append(f"- **Average Daily Goal**: {plan_obj.daily:,.0f} words/day")
    lines.append(f"- **Writing Days**: {plan_obj.time} days")

    if plan_obj.spare_days > 0:
        lines.append(f"- **Spare Days**: {plan_obj.spare_days} days")
        lines.append(f"- **Total Duration**: {plan_obj.total_calendar_days} days")

    lines.append(f"- **Start Date**: {plan_obj.start_date.strftime('%B %d, %Y')}")

    end_date = plan_obj.end_date or plan_obj.start_date - timedelta(days=1)
    lines.append(f"- **End Date**: {end_date.strftime('%B %d, %Y')}")

    lines.append(f"- **Writing Pattern**: {plan_obj.pattern.capitalize()}")

    if plan_obj.created_date:
        lines.append(f"- **Created**: {plan_obj.created_date.strftime('%B %d, %Y')}")

    lines.append("")

    # Progress (if any)
    if plan_obj.progress:
        lines.append("## Progress")
        lines.append("")

        total_written = plan_obj.get_total_written()
        completion = plan_obj.get_completion_percentage()
        remaining = plan_obj.get_remaining_words()

        lines.append(f"- **Words Written**: {total_written:,} words ({completion:.1f}%)")
        lines.append(f"- **Remaining**: {remaining:,} words")
        lines.append(f"- **Days Tracked**: {plan_obj.get_days_with_progress()}")

        streak = plan_obj.get_current_streak()
        if streak > 0:
            lines.append(f"- **Current Streak**: {streak} day{'s' if streak != 1 else ''} 🔥")

        # On-track status
        on_track, info = plan_obj.is_on_track()
        if info.get('status'):
            status_emoji = {
                'ahead': '✅',
                'on_track': '✅',
                'behind': '⚠️'
            }
            emoji = status_emoji.get(info['status'], '')

            if info['status'] == 'ahead':
                lines.append(f"- **Status**: {emoji} AHEAD by {info['difference']:,.0f} words")
            elif info['status'] == 'on_track':
                lines.append(f"- **Status**: {emoji} ON TRACK")
            else:
                lines.append(f"- **Status**: {emoji} BEHIND by {abs(info['difference']):,.0f} words")

        lines.append("")

    # Daily Schedule
    lines.append("## Daily Schedule")
    lines.append("")

    # Show pattern variation if not flat
    if plan_obj.pattern != "flat":
        lines.append(f"*Using {plan_obj.pattern} pattern - daily goals vary*")
        lines.append("")

    total_days = plan_obj.total_calendar_days
    writing_day_number = 0

    # Group by week for better readability
    current_week_start = plan_obj.start_date
    week_num = 1

    for day_idx in range(total_days):
        current_date = plan_obj.start_date + timedelta(days=day_idx)

        # Check if new week
        if day_idx > 0 and current_date.weekday() == 0:  # Monday
            week_num += 1
            lines.append("")

        if day_idx == 0 or current_date.weekday() == 0:
            lines.append(f"### Week {week_num}")
            lines.append("")

        date_str = current_date.strftime('%a, %B %d, %Y')

        # Check if spare day
        is_spare = plan_obj.is_spare_day(current_date)

        if is_spare:
            lines.append(f"- **{date_str}**: *Spare Day* (0 words)")
        else:
            writing_day_number += 1
            daily_goal = plan_obj.get_daily_goal(date=current_date)

            # Check for progress
            actual = plan_obj.get_progress_for_date(current_date)
            if actual is not None and actual > 0:
                status = plan_obj.get_progress_status_for_date(current_date)
                status_symbol = {
                    'exceeded': '✅',
                    'met': '✅',
                    'partial': '⚠️',
                    'missed': '❌'
                }.get(status, '')

                lines.append(f"- **{date_str}**: {daily_goal:.0f} words → {actual:,.0f} written {status_symbol}")
            else:
                lines.append(f"- **{date_str}**: {daily_goal:.0f} words")

    lines.append("")

    # Milestones
    lines.append("## Milestones")
    lines.append("")

    lines.append("| Progress | Date | Words | Plan Day | Status |")
    lines.append("|----------|------|-------|----------|--------|")

    for milestone in plan_obj.milestones():
        date_text = milestone['date'].strftime('%b %d, %Y') if milestone['date'] else "before the start"
        day_text = str(milestone['day']) if milestone['day'] else "-"
        status = "✅ reached" if milestone['reached'] else ""
        lines.append(f"| {int(milestone['fraction'] * 100)}% | {date_text} | "
                     f"{milestone['words']:,} | {day_text} | {status} |")

    lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(f"*Generated by wordplanner on {datetime.now().strftime('%B %d, %Y at %H:%M')}*")

    # Write to file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    except PermissionError:
        raise PermissionError(f"Permission denied: Cannot write to {filepath}")
    except OSError as e:
        raise OSError(f"Failed to write Markdown file {filepath}: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error writing Markdown: {e}")

    return filepath


def get_available_export_formats():
    """Return list of available export formats."""
    return ['csv', 'ical', 'markdown']
