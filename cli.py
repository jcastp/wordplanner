"""
Command-line commands on the current plan (★), without the menus.

    planea.py log 1200                  words written today
    planea.py log --total 23450         the manuscript's running total
    planea.py log 800 --date 2026-11-03 an earlier day
    planea.py status                    today's goal, written, ahead/behind

A command loads the current plan, changes it the way the menus do (past days
are locked first), saves it over its file and prints the plan's status.
Exit codes: 0 done, 1 refused (no current plan, bad date, lower total),
2 bad usage (from argparse).
"""

import argparse
import sys
from datetime import datetime, timedelta
import plan
import plan_manager
import plan_storage


def build_parser():
    parser = argparse.ArgumentParser(
        prog="planea.py",
        description="Word count planner. Without a command, opens the interactive menus. "
                    "Commands work on the current plan (★), set in 'Manage multiple plans'.")
    commands = parser.add_subparsers(dest="command", required=True, metavar="command")

    log = commands.add_parser(
        "log", help="log words for today (or --date)",
        description="Log words for today, or for --date. The day's entry is replaced.")
    amount = log.add_mutually_exclusive_group(required=True)
    amount.add_argument("words", nargs="?", type=word_count,
                        help="words written that day")
    amount.add_argument("--total", type=word_count, metavar="WORDS",
                        help="the manuscript's running total (pre-existing words included); "
                             "the day's words are worked out from it")
    log.add_argument("--date", type=date_argument, metavar="YYYY-MM-DD",
                     help="the day to log (default: today)")

    commands.add_parser("status", help="show today's goal and where the plan stands",
                        description="Show today's goal and where the current plan stands.")
    return parser


def word_count(text):
    """A word count argument: a whole number, commas allowed (23,450)."""
    try:
        value = int(text.replace(",", ""))
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid word count: '{text}'")
    if value < 0:
        raise argparse.ArgumentTypeError("a word count can't be negative")
    return value


def date_argument(text):
    try:
        return datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid date: '{text}' (use YYYY-MM-DD)")


def fail(message):
    print(f"Error: {message}", file=sys.stderr)
    return 1


def load_current_plan():
    """The current plan (★), with past days locked as the plan menu does, or None."""
    current = plan_manager.get_active_plan()
    if current is not None and current.start_date:
        current.lock_past_goals()
        current.sync_daily()
    return current


def log_command(current, args):
    entry_date = args.date or plan.today()
    day = entry_date.strftime('%Y-%m-%d')

    if entry_date > plan.today():
        return fail(f"{day} is in the future.")
    if not current.start_date:
        return fail("the current plan has no start date.")

    if args.total is not None:
        words = current.words_for_running_total(args.total, entry_date)
        if words < 0:
            logged = current.get_total_written(through=entry_date - timedelta(days=1))
            return fail(f"a running total of {args.total:,.0f} is {-words:,.0f} below the "
                        f"{logged:,.0f} already logged before {day} (pre-existing words included). "
                        "Logged days can't go negative; correct an earlier day with --date.")
    else:
        words = args.words

    end = current.end_date
    if entry_date < current.start_date or end is None or entry_date > end:
        print(f"Note: {day} is outside the plan. The words count toward your total, "
              "but not toward any day's goal.")

    previous = current.get_progress_for_date(entry_date)
    current.record_progress(entry_date, words)
    plan_storage.save_plan(current, overwrite_source=True)

    replaced = f" (replaces {previous:,.0f})" if previous is not None else ""
    print(f"Logged {words:,.0f} words on {day}{replaced}.")
    print()
    print_status(current)
    return 0


def print_status(current):
    """Today's goal and where the plan stands, as plain text."""
    today = plan.today()
    name = current.name or "Unnamed plan"
    if not current.start_date:
        print(f"★ {name}: no start date set.")
        return

    end = current.end_date
    span = f"{current.start_date.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}" if end else "no writing days"
    print(f"★ {name} ({span})")

    if today < current.start_date:
        print(f"Starts on {current.start_date.strftime('%A, %b %d')}.")
    elif end is None or today > end:
        print("The plan's last day has passed.")
    else:
        goal = current.get_daily_goal(date=today)
        written_today = current.get_progress_for_date(today) or 0
        label = f"Today ({today.strftime('%a %b %d')})"
        if goal == 0:
            print(f"{label}: rest day" + (f", {written_today:,.0f} words written" if written_today else ""))
        else:
            mark = " ✓" if written_today >= goal else f", {goal - written_today:,.0f} to go"
            print(f"{label}: {written_today:,.0f} / {goal:,.0f} words{mark}")

    written = current.get_total_written()
    print(f"Written: {written:,.0f} / {current.total:,.0f} words "
          f"({current.get_completion_percentage():.1f}%), {current.get_remaining_words():,.0f} to go")

    if today > current.start_date:
        _, info = current.is_on_track()
        if info['status'] == 'ahead':
            print(f"Status: ✓ ahead by {info['difference']:,.0f} words")
        elif info['status'] == 'on_track':
            print("Status: ✓ on track")
        else:
            print(f"Status: ⚠ behind by {abs(info['difference']):,.0f} words")


def run(argv):
    """Run a command; returns the exit code."""
    args = build_parser().parse_args(argv)

    current = load_current_plan()
    if current is None:
        return fail("there is no current plan (★). Open 'Manage multiple plans' in "
                    "planea.py and set one.")

    if args.command == "log":
        return log_command(current, args)
    print_status(current)
    return 0
