"""Export functionality for writing plans."""

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
import config
import plan_storage
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


def export_filename(plan_obj, extension):
    """A safe export file name: <plan name>_<timestamp>.<extension> (X2)."""
    stem = plan_storage.safe_filename_stem(plan_obj.name)
    return f"{stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"


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
        filepath = get_exports_directory() / export_filename(plan_obj, "csv")
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


def ical_escape(text):
    """Escape a TEXT value (RFC 5545 3.3.11): backslash, semicolon, comma, newline."""
    return (str(text).replace('\\', '\\\\').replace(';', '\\;')
            .replace(',', '\\,').replace('\r\n', '\\n').replace('\n', '\\n'))


def ical_fold(line):
    """
    Fold a content line at 75 octets (RFC 5545 3.1).

    Continuation lines start with a space. Splits never break a UTF-8
    character.
    """
    parts = []
    current, size, limit = "", 0, 75
    for char in line:
        char_size = len(char.encode('utf-8'))
        if size + char_size > limit:
            parts.append(current)
            current, size, limit = " ", 1, 75
        current += char
        size += char_size
    parts.append(current)
    return "\r\n".join(parts)


def export_to_ical(plan_obj, filepath=None):
    """
    Export plan to iCal/ICS format for calendar apps (RFC 5545).

    One all-day event per plan day: the word goal on writing days, a
    transparent "rest day" event on spare days and other days with a goal of
    0. Event UIDs come from the plan's plan_id and the date, so re-importing
    after a rename updates the events instead of duplicating them.

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
        filepath = get_exports_directory() / export_filename(plan_obj, "ics")
    else:
        filepath = Path(filepath)

    plan_name = plan_obj.name or 'Writing Plan'
    dtstamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//wordplanner//Writing Plan//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{ical_escape(plan_name)}",
        "X-WR-CALDESC:Writing plan generated by wordplanner",
    ]

    writing_day_number = 0
    for current_date in plan_obj.plan_days():
        date_str = current_date.strftime('%Y%m%d')
        # All-day events: DTEND is the (exclusive) next day
        end_str = (current_date + timedelta(days=1)).strftime('%Y%m%d')
        daily_goal = plan_obj.get_daily_goal(date=current_date)

        if plan_obj.is_spare_day(current_date) or daily_goal == 0:
            kind = "spare" if plan_obj.is_spare_day(current_date) else "rest"
            summary = f"{kind.capitalize()} day - {plan_name}"
            description = "Rest day (no writing required)"
            transparency = "TRANSPARENT"
        else:
            kind = "writing"
            writing_day_number += 1
            summary = f"Write {daily_goal:,.0f} words - {plan_name}"
            description = (f"Writing goal: {daily_goal:,.0f} words\n"
                           f"Day {writing_day_number} of the plan\n"
                           f"Total goal: {plan_obj.total:,.0f} words")
            transparency = "OPAQUE"

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{kind}-{date_str}-{plan_obj.plan_id}@wordplanner",
            f"DTSTAMP:{dtstamp}",
            f"DTSTART;VALUE=DATE:{date_str}",
            f"DTEND;VALUE=DATE:{end_str}",
            f"SUMMARY:{ical_escape(summary)}",
            f"DESCRIPTION:{ical_escape(description)}",
            "STATUS:CONFIRMED",
            f"TRANSP:{transparency}",
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")
    content = "".join(ical_fold(line) + "\r\n" for line in lines)

    # Write to file (newline='' keeps the CRLF line endings exactly)
    try:
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
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
        filepath = get_exports_directory() / export_filename(plan_obj, "md")
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
    lines.append(f"- **Total Word Goal**: {plan_obj.total:,.0f} words")
    if plan_obj.preexisting_words:
        lines.append(f"- **Written Before the Plan**: {plan_obj.preexisting_words:,.0f} words")
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

        lines.append(f"- **Words Written**: {total_written:,.0f} words ({completion:.1f}%)")
        lines.append(f"- **Remaining**: {remaining:,.0f} words")
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

                lines.append(f"- **{date_str}**: {daily_goal:,.0f} words → {actual:,.0f} written {status_symbol}")
            else:
                lines.append(f"- **{date_str}**: {daily_goal:,.0f} words")

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
                     f"{milestone['words']:,.0f} | {day_text} | {status} |")

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
