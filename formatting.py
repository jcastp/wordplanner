"""
How dates and colors are shown, following the user's preferences.

Dates written as numbers on screen (and in the Markdown export and command
output) go through format_date(), so the "date format" setting changes them
all. Dates already written out ("Nov 05, 2026") stay as they are, and data
never changes: plan files, progress keys, CSV and iCal always use ISO.

Typed dates go through parse_date(): ISO (YYYY-MM-DD) always works, and so
does the chosen numeric format.
"""

from datetime import datetime
from rich.console import Console
import user_preferences


# Setting -> (strftime format, how to write it in a prompt, example)
DATE_FORMATS = {
    "iso": ("%Y-%m-%d", "YYYY-MM-DD", "2026-11-05"),
    "dmy": ("%d/%m/%Y", "DD/MM/YYYY", "05/11/2026"),
    "mdy": ("%m/%d/%Y", "MM/DD/YYYY", "11/05/2026"),
    "text": ("%b %d, %Y", "YYYY-MM-DD", "Nov 05, 2026"),
}

ISO = "%Y-%m-%d"


def _date_format():
    return DATE_FORMATS[user_preferences.get_preference('date_format')]


def format_date(date):
    """A date for display, in the chosen format (e.g. 2026-11-05 or 05/11/2026)."""
    return date.strftime(_date_format()[0])


# Day and month without the year, for graph axes
DAY_MONTH = {"iso": "%m-%d", "dmy": "%d/%m", "mdy": "%m/%d", "text": "%b %d"}


def format_day_month(date):
    """A date without the year, in the chosen order (e.g. 11-05, 05/11, Nov 05)."""
    return date.strftime(DAY_MONTH[user_preferences.get_preference('date_format')])


def format_date_weekday(date):
    """A date with its weekday, e.g. "2026-11-05 (Thursday)"."""
    return f"{format_date(date)} ({date.strftime('%A')})"


def date_hint():
    """How to type a date: "YYYY-MM-DD", or "DD/MM/YYYY or YYYY-MM-DD"."""
    written = _date_format()[1]
    return written if written == "YYYY-MM-DD" else f"{written} or YYYY-MM-DD"


def parse_date(text):
    """
    A typed date, as a datetime at midnight.

    ISO always works; the chosen numeric format (DD/MM/YYYY or MM/DD/YYYY)
    works too.

    Raises:
        ValueError: if text isn't a date in either format
    """
    text = text.strip()
    formats = [ISO]
    chosen = _date_format()[0]
    if chosen != ISO and "%b" not in chosen:
        formats.append(chosen)
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError(f"'{text}' is not a date ({date_hint()})")


def colors_enabled():
    return user_preferences.get_preference('colors')


def make_console():
    """
    A Rich console for printing now: plain when colors are off.

    With colors on, Rich still honours the NO_COLOR environment variable.
    Bold and reverse (e.g. the TODAY marker) stay either way.
    """
    return Console(no_color=None if colors_enabled() else True)
