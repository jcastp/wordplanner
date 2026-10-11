import datetime
from datetime import timedelta
import math
import json

"""class for the Plan."""


def to_midnight(value):
    """
    Normalize a plan date to midnight, dropping any time of day.

    Plan dates (start date, spare days) are compared against calendar days at
    midnight, so a stored time of day would make the start day fall outside
    the plan. Accepts datetime or date; anything else (None, legacy integer
    spare days) is returned unchanged.
    """
    if isinstance(value, datetime.datetime):
        return value.replace(hour=0, minute=0, second=0, microsecond=0)
    if isinstance(value, datetime.date):
        return datetime.datetime.combine(value, datetime.time())
    return value


def whole_days(value):
    """
    Round a number of writing days up to a whole day.

    Rounds to 6 decimals first so float noise (48.0000000001) doesn't add a day.
    """
    return math.ceil(round(value, 6))


class Plan():
    """simple class to store a plan and its attributes."""
    def __init__(self, daily=0, total=0, time=0, words=0, name=None, start_date=None, created_date=None, spare_days_dates=None, source_file=None, pattern="flat", pattern_config=None, progress=None, weekend_mode="same", weekend_daily=0, weekend_days=None, custom_daily_goals=None, status="active", tags=None, category=None, is_active=False, last_modified=None, preexisting_words=0, locked_goals=None):
        """Initialize the values."""
        # Validate numeric inputs are not negative
        if daily < 0:
            raise ValueError(f"Daily word count cannot be negative: {daily}")
        if total < 0:
            raise ValueError(f"Total word count cannot be negative: {total}")
        if time < 0:
            raise ValueError(f"Time (days) cannot be negative: {time}")
        if words < 0:
            raise ValueError(f"Words count cannot be negative: {words}")
        if weekend_daily < 0:
            raise ValueError(f"Weekend daily word count cannot be negative: {weekend_daily}")
        if preexisting_words < 0:
            raise ValueError(f"Pre-existing word count cannot be negative: {preexisting_words}")

        self.daily = daily
        self.total = total  # Full project goal, including pre-existing words
        self.preexisting_words = preexisting_words  # Words written before the plan; not scheduled
        self.time = time  # Writing days (not including spare days), always whole
        self.words = words # this is the amount of words in the current plan
        self.name = name  # Name/title of the writing project
        self.start_date = start_date  # When the writing plan starts
        self.created_date = created_date or datetime.datetime.now()  # When this plan was created
        self.spare_days_dates = [to_midnight(d) for d in (spare_days_dates or [])]  # List of actual dates (datetime objects) with 0 words
        self.source_file = source_file  # Path to the file this plan was loaded from (None for new plans)
        self.pattern = pattern  # Pattern type: flat, valley, mountain, rising, declining, random
        self.pattern_config = pattern_config or {}  # Pattern-specific configuration
        self._daily_goals_cache = None  # Cache for calculated daily goals
        self.progress = progress or {}  # Dictionary mapping date strings (YYYY-MM-DD) to actual word counts
        self.weekend_mode = weekend_mode  # "same", "different", "spare"
        self.weekend_daily = weekend_daily  # Daily goal for weekends (if mode is "different")
        self.weekend_days = weekend_days or [5, 6]  # Saturday=5, Sunday=6 (0-indexed from Monday)
        self.custom_daily_goals = custom_daily_goals or {}  # Date string -> custom word count
        self.locked_goals = locked_goals or {}  # Date string -> goal frozen once the day is past

        # Multiple plans management fields
        self.status = status  # "active", "archived", "completed"
        self.tags = tags or []  # List of tag strings (e.g., ["urgent", "fiction"])
        self.category = category  # Category string (e.g., "novel", "blog", "academic")
        self.is_active = is_active  # Boolean flag for the currently active plan
        self.last_modified = last_modified or datetime.datetime.now()  # When this plan was last modified

    @property
    def start_date(self):
        """When the writing plan starts (always at midnight, or None)."""
        return self._start_date

    @start_date.setter
    def start_date(self, value):
        self._start_date = to_midnight(value)

    @property
    def time(self):
        """Number of writing days (spare days not included). Always a whole number."""
        return self._time

    @time.setter
    def time(self, value):
        self._time = whole_days(value)

    @property
    def words_to_schedule(self):
        """Words the schedule has to cover: the goal minus words written before the plan."""
        return max(0, self.total - self.preexisting_words)

    @property
    def spare_days(self):
        """
        Number of spare days inside the plan window.

        Spare days outside the window (e.g. before a moved start date, or a
        whole year of Saturdays on a short plan) don't lengthen the plan.
        Without a start date there is no window, so all are counted.
        """
        if not self.start_date:
            return len(self.spare_days_dates)
        return self.total_calendar_days - self.time

    @property
    def end_date(self):
        """
        Last calendar day of the plan, or None without a start date or writing days.

        Walks forward from the start date until `time` writing days fit, skipping
        spare days on the way. This is the single source for the plan window.
        """
        if not self.start_date or self.time <= 0:
            return None

        spare = {d.date() for d in self.spare_days_dates if not isinstance(d, int)}
        current = self.start_date
        writing_days_left = self.time
        while True:
            if current.date() not in spare:
                writing_days_left -= 1
                if writing_days_left == 0:
                    return current
            current += timedelta(days=1)

    @property
    def total_calendar_days(self):
        """Calendar days from start to end date (writing + spare days), or 0."""
        end = self.end_date
        if end is None:
            return 0
        return (end - self.start_date).days + 1

    def plan_days(self):
        """Every calendar day of the plan, from start date to end date, as datetimes."""
        for offset in range(self.total_calendar_days):
            yield self.start_date + timedelta(days=offset)

    def is_spare_day(self, date):
        """Check if a given date is a spare day."""
        # Normalize to date only (ignore time)
        check_date = date.date() if hasattr(date, 'date') else date
        for spare_item in self.spare_days_dates:
            # Skip old format integers (shouldn't happen after migration)
            if isinstance(spare_item, int):
                continue
            spare_date_normalized = spare_item.date() if hasattr(spare_item, 'date') else spare_item
            if check_date == spare_date_normalized:
                return True
        return False

    def is_weekend(self, date):
        """Check if a given date is a weekend day."""
        return date.weekday() in self.weekend_days

    def calculate_daily(self):
        """calculate the daily amount of words needed, based on time
        and total words desired."""
        if self.time <= 0:
            raise ValueError(f"Cannot calculate daily words: time must be greater than 0 (got {self.time})")
        if self.total < 0:
            raise ValueError(f"Cannot calculate daily words: total cannot be negative (got {self.total})")
        self.daily = self.words_to_schedule / self.time
        self.invalidate_daily_goals_cache()

    def calculate_time(self):
        """Calculate the time needed to complete your work."""
        if self.daily <= 0:
            raise ValueError(f"Cannot calculate time: daily words must be greater than 0 (got {self.daily})")
        if self.total < 0:
            raise ValueError(f"Cannot calculate time: total cannot be negative (got {self.total})")
        # Round up to whole days, then spread the words evenly over them
        self.time = self.words_to_schedule / self.daily
        if self.time > 0:
            self.daily = self.words_to_schedule / self.time
        self.invalidate_daily_goals_cache()

    def calculate_words(self):
        """calculate the number or words."""
        if self.daily < 0:
            raise ValueError(f"Cannot calculate total words: daily cannot be negative (got {self.daily})")
        if self.time < 0:
            raise ValueError(f"Cannot calculate total words: time cannot be negative (got {self.time})")
        self.total = self.daily * self.time + self.preexisting_words
        self.invalidate_daily_goals_cache()

    def show(self):
        """Shows basic data."""
        print(self.total, self.time, self.daily)

    def lock_past_goals(self, as_of_date=None):
        """
        Freeze the goal of every plan day before as_of_date (default: today).

        Once locked, a day's goal never changes again, whatever is modified
        later (daily, pattern, weekends, custom goals, spare days, start date).
        Today is not locked: it isn't over yet. Already locked days are kept.

        Returns:
            Number of days newly locked
        """
        if as_of_date is None:
            as_of_date = datetime.datetime.now()
        as_of_date = to_midnight(as_of_date)

        newly_locked = 0
        for day in self.plan_days():
            if day >= as_of_date:
                break
            date_key = day.strftime('%Y-%m-%d')
            if date_key not in self.locked_goals:
                self.locked_goals[date_key] = self.get_daily_goal(date=day)
                newly_locked += 1
        return newly_locked

    def is_locked(self, date):
        """Check whether a day's goal is locked (the day is past)."""
        return date.strftime('%Y-%m-%d') in self.locked_goals

    def invalidate_daily_goals_cache(self):
        """Invalidate the cached daily goals when plan changes."""
        self._daily_goals_cache = None

    def calculate_pattern_goals(self):
        """
        Generate daily goals based on pattern.
        Returns a list of daily goals for each writing day.
        """
        # Use cache if available
        if self._daily_goals_cache is not None:
            return self._daily_goals_cache

        num_days = self.time
        if num_days <= 0:
            return []

        if self.pattern == "flat":
            # Same daily goal every day
            goals = [self.daily] * num_days

        elif self.pattern == "valley":
            # Start high, decrease to middle, increase at end
            goals = self._calculate_valley_pattern(num_days)

        elif self.pattern == "mountain":
            # Start low, increase to middle, decrease at end
            goals = self._calculate_mountain_pattern(num_days)

        elif self.pattern == "rising":
            # Gradually increase daily goals over time
            goals = self._calculate_rising_pattern(num_days)

        elif self.pattern == "declining":
            # Gradually decrease daily goals over time
            goals = self._calculate_declining_pattern(num_days)

        elif self.pattern == "random":
            # Randomized daily goals within constraints
            goals = self._calculate_random_pattern(num_days)

        else:
            # Default to flat if unknown pattern
            goals = [self.daily] * num_days

        # Cache the result
        self._daily_goals_cache = goals
        return goals

    def _calculate_valley_pattern(self, num_days):
        """Start high, decrease to middle, increase at end."""
        import math
        goals = []
        mid_point = num_days / 2

        # Configuration
        peak_multiplier = self.pattern_config.get('peak_multiplier', 1.5)
        valley_multiplier = self.pattern_config.get('valley_multiplier', 0.7)

        for day in range(num_days):
            # Create a valley curve using cosine
            # cos(0) = 1, cos(pi) = -1, cos(2pi) = 1
            progress = day / num_days
            curve = math.cos(progress * 2 * math.pi) # Goes from 1 to -1 to 1

            # Map curve to multiplier range
            # curve: 1 to -1, map to: peak_multiplier to valley_multiplier
            multiplier = valley_multiplier + (peak_multiplier - valley_multiplier) * (curve + 1) / 2

            goals.append(self.daily * multiplier)

        # Adjust to maintain total
        current_total = sum(goals)
        if current_total == 0:
            # Avoid division by zero - return flat goals if pattern calculation fails
            return [self.daily] * num_days
        adjustment = self.words_to_schedule / current_total
        goals = [g * adjustment for g in goals]

        return goals

    def _calculate_mountain_pattern(self, num_days):
        """Start low, increase to middle, decrease at end."""
        import math
        goals = []

        # Configuration
        peak_multiplier = self.pattern_config.get('peak_multiplier', 1.5)
        valley_multiplier = self.pattern_config.get('valley_multiplier', 0.7)

        for day in range(num_days):
            # Create a mountain curve using sine
            progress = day / num_days
            curve = math.sin(progress * math.pi)  # Goes from 0 to 1 to 0

            # Map curve to multiplier range
            multiplier = valley_multiplier + (peak_multiplier - valley_multiplier) * curve

            goals.append(self.daily * multiplier)

        # Adjust to maintain total
        current_total = sum(goals)
        if current_total == 0:
            # Avoid division by zero - return flat goals if pattern calculation fails
            return [self.daily] * num_days
        adjustment = self.words_to_schedule / current_total
        goals = [g * adjustment for g in goals]

        return goals

    def _calculate_rising_pattern(self, num_days):
        """Gradually increase daily goals over time."""
        goals = []

        # Configuration
        start_multiplier = self.pattern_config.get('start_multiplier', 0.5)
        end_multiplier = self.pattern_config.get('end_multiplier', 1.5)

        for day in range(num_days):
            progress = day / (num_days - 1) if num_days > 1 else 0
            multiplier = start_multiplier + (end_multiplier - start_multiplier) * progress
            goals.append(self.daily * multiplier)

        # Adjust to maintain total
        current_total = sum(goals)
        if current_total == 0:
            # Avoid division by zero - return flat goals if pattern calculation fails
            return [self.daily] * num_days
        adjustment = self.words_to_schedule / current_total
        goals = [g * adjustment for g in goals]

        return goals

    def _calculate_declining_pattern(self, num_days):
        """Gradually decrease daily goals over time."""
        goals = []

        # Configuration
        start_multiplier = self.pattern_config.get('start_multiplier', 1.5)
        end_multiplier = self.pattern_config.get('end_multiplier', 0.5)

        for day in range(num_days):
            progress = day / (num_days - 1) if num_days > 1 else 0
            multiplier = start_multiplier + (end_multiplier - start_multiplier) * progress
            goals.append(self.daily * multiplier)

        # Adjust to maintain total
        current_total = sum(goals)
        if current_total == 0:
            # Avoid division by zero - return flat goals if pattern calculation fails
            return [self.daily] * num_days
        adjustment = self.words_to_schedule / current_total
        goals = [g * adjustment for g in goals]

        return goals

    def _calculate_random_pattern(self, num_days):
        """Randomized daily goals within constraints."""
        import random

        # Configuration
        min_multiplier = self.pattern_config.get('min_multiplier', 0.5)
        max_multiplier = self.pattern_config.get('max_multiplier', 1.5)
        seed = self.pattern_config.get('seed', None)

        if seed is not None:
            random.seed(seed)

        goals = []
        for _ in range(num_days):
            multiplier = random.uniform(min_multiplier, max_multiplier)
            goals.append(self.daily * multiplier)

        # Adjust to maintain total
        current_total = sum(goals)
        if current_total == 0:
            # Avoid division by zero - return flat goals if pattern calculation fails
            return [self.daily] * num_days
        adjustment = self.words_to_schedule / current_total
        goals = [g * adjustment for g in goals]

        return goals

    def get_daily_goal(self, day_index=None, date=None):
        """
        Get the daily goal for a specific day.

        Args:
            day_index: 0-based index of the writing day
            date: datetime object (will calculate day_index from start_date)

        Returns:
            Daily word goal for that day, or 0 if it's a spare day
        """
        if date is not None:
            # Past days keep the goal they had; nothing overrides a lock
            date_key = date.strftime('%Y-%m-%d')
            if date_key in self.locked_goals:
                return self.locked_goals[date_key]

            # Check if it's a spare day
            if self.is_spare_day(date):
                return 0

            # Check for custom daily goal for this specific date
            if date_key in self.custom_daily_goals:
                return self.custom_daily_goals[date_key]

            # Check weekend mode
            if self.is_weekend(date):
                if self.weekend_mode == "spare":
                    return 0
                elif self.weekend_mode == "different":
                    return self.weekend_daily

            # Calculate day index from start_date for pattern-based goals
            if self.start_date:
                delta = date - self.start_date
                day_index = delta.days
            else:
                # Can't determine day index without start_date
                return self.daily

        if day_index is None or day_index < 0:
            return self.daily

        # Get pattern-based goals
        goals = self.calculate_pattern_goals()

        if day_index < len(goals):
            return goals[day_index]
        else:
            # Beyond plan duration
            return self.daily

    def set_custom_daily_goal(self, date, word_count):
        """
        Set a custom word goal for a specific date.

        Args:
            date: datetime object
            word_count: custom word count for this day
        """
        date_key = date.strftime('%Y-%m-%d')
        self.custom_daily_goals[date_key] = int(word_count)
        self.invalidate_daily_goals_cache()

    def remove_custom_daily_goal(self, date):
        """
        Remove a custom word goal for a specific date.

        Args:
            date: datetime object
        """
        date_key = date.strftime('%Y-%m-%d')
        if date_key in self.custom_daily_goals:
            del self.custom_daily_goals[date_key]
            self.invalidate_daily_goals_cache()

    def recalculate_total_from_daily_goals(self):
        """
        Recalculate the total word count based on current daily goals.

        This method iterates through all calendar days in the plan and sums up
        the daily goals (considering patterns, weekends, custom goals, and spare days).
        It then updates self.total to match the calculated sum.

        Returns:
            float: The new total word count
        """
        if not self.start_date:
            # Can't recalculate without a start date
            return self.total

        # Sum up all daily goals
        total_words = sum(self.get_daily_goal(date=day) for day in self.plan_days())

        # Update the plan's total (the schedule plus words written before the plan)
        self.total = total_words + self.preexisting_words
        self.invalidate_daily_goals_cache()

        return self.total

    def record_progress(self, date, word_count):
        """
        Record actual words written on a specific date.

        Args:
            date: datetime object
            word_count: number of words written (can be 0)
        """
        date_key = date.strftime('%Y-%m-%d')
        self.progress[date_key] = int(word_count)

    def get_progress_for_date(self, date):
        """
        Get the actual words written on a specific date.

        Args:
            date: datetime object

        Returns:
            Word count for that date, or None if no progress recorded
        """
        date_key = date.strftime('%Y-%m-%d')
        return self.progress.get(date_key)

    def get_total_written(self):
        """Get total words written for the project, including pre-existing words."""
        return self.preexisting_words + self.get_plan_written()

    def get_plan_written(self):
        """Get words logged as daily progress (excludes pre-existing words)."""
        return sum(self.progress.values())

    def get_remaining_words(self):
        """Calculate remaining words to write."""
        return max(0, self.total - self.get_total_written())

    def get_completion_percentage(self):
        """Get percentage of goal completed."""
        if self.total == 0:
            return 0
        return (self.get_total_written() / self.total) * 100

    def get_days_with_progress(self):
        """Get count of days with progress recorded."""
        return len(self.progress)

    def get_current_streak(self):
        """
        Get the current consecutive days streak.
        Only counts days up to today, not future days.
        """
        if not self.start_date or not self.progress:
            return 0

        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        current_date = today
        streak = 0

        # Count backwards from today
        while current_date >= self.start_date:
            date_key = current_date.strftime('%Y-%m-%d')

            # Check if this is a spare day - spare days don't break the streak
            if self.is_spare_day(current_date):
                current_date -= timedelta(days=1)
                continue

            # Check if progress was recorded for this day
            if date_key in self.progress and self.progress[date_key] > 0:
                streak += 1
            else:
                # Streak is broken
                break

            current_date -= timedelta(days=1)

        return streak

    def is_on_track(self, as_of_date=None):
        """
        Check if progress is on track based on expected progress.

        Args:
            as_of_date: datetime object to check against (default: today)

        Returns:
            Tuple of (bool, dict) where bool is True if on track,
            and dict contains detailed info
        """
        if not self.start_date:
            return True, {'message': 'No start date set'}

        if as_of_date is None:
            as_of_date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Calculate expected progress up to this date
        current_date = self.start_date
        expected_words = 0
        days_elapsed = 0

        while current_date <= as_of_date:
            # Don't count future days beyond the plan
            if days_elapsed >= self.time:
                break

            if not self.is_spare_day(current_date):
                daily_goal = self.get_daily_goal(date=current_date)
                expected_words += daily_goal
                days_elapsed += 1

            current_date += timedelta(days=1)

        actual_words = self.get_plan_written()
        difference = actual_words - expected_words

        # Calculate percentage difference
        if expected_words > 0:
            percent_diff = (difference / expected_words) * 100
        else:
            percent_diff = 0

        # Determine status
        if difference >= 0:
            status = 'ahead' if difference > 0 else 'on_track'
        else:
            status = 'behind'

        return status in ['ahead', 'on_track'], {
            'status': status,
            'expected_words': expected_words,
            'actual_words': actual_words,
            'difference': difference,
            'percent_diff': percent_diff,
            'days_elapsed': days_elapsed
        }

    def get_progress_status_for_date(self, date):
        """
        Get the progress status for a specific date.

        Returns:
            'exceeded', 'met', 'partial', 'missed', 'future', 'spare', or 'no_goal'
        """
        if not self.start_date:
            return 'no_goal'

        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Check if it's a future date
        if date > today:
            return 'future'

        # Check if it's a spare day
        if self.is_spare_day(date):
            return 'spare'

        # Check if it's before start date
        if date < self.start_date:
            return 'no_goal'

        # Get goal and actual for this date
        daily_goal = self.get_daily_goal(date=date)
        actual = self.get_progress_for_date(date)

        if actual is None:
            return 'missed'
        elif actual == 0:
            return 'missed'
        elif actual >= daily_goal:
            return 'exceeded' if actual > daily_goal else 'met'
        else:
            return 'partial'

    def recalculate_from_progress(self, as_of_date=None):
        """
        Recalculate the plan based on actual progress, redistributing remaining words
        across remaining days while keeping the end date fixed.

        Algorithm:
        - Words Remaining = Total Words - Words Completed So Far
        - New Daily Target = Words Remaining / Remaining Writing Days

        This keeps the deadline fixed and evenly distributes remaining work.

        Args:
            as_of_date: Date to calculate from (defaults to today)

        Returns:
            dict with recalculation details, or None if recalculation not possible
        """
        if not self.start_date:
            return None

        if as_of_date is None:
            as_of_date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Calculate total words written so far
        words_completed = self.get_total_written()

        # Calculate remaining words
        words_remaining = self.total - words_completed

        # If we've already completed the goal, no recalculation needed
        if words_remaining <= 0:
            return {
                'success': False,
                'reason': 'goal_already_met',
                'words_completed': words_completed,
                'words_remaining': 0
            }

        # A plan with no writing days ends before it starts
        end_date = self.end_date or self.start_date - timedelta(days=1)

        # If we're past the end date, can't recalculate
        if as_of_date > end_date:
            return {
                'success': False,
                'reason': 'past_end_date',
                'words_completed': words_completed,
                'words_remaining': words_remaining,
                'end_date': end_date
            }

        # Count remaining writing days (excluding spare days and past days)
        remaining_writing_days = 0
        current_date = as_of_date

        while current_date <= end_date:
            # Check if this is a spare day
            if not self.is_spare_day(current_date):
                remaining_writing_days += 1
            current_date += timedelta(days=1)

        # If no remaining writing days, can't recalculate
        if remaining_writing_days == 0:
            return {
                'success': False,
                'reason': 'no_remaining_days',
                'words_completed': words_completed,
                'words_remaining': words_remaining
            }

        # Calculate new daily target
        old_daily = self.daily
        new_daily = words_remaining / remaining_writing_days

        # Lock the goals of days before as_of_date so the changes below can't touch them
        past_goals_preserved = self.lock_past_goals(as_of_date)

        # Update the plan
        self.daily = new_daily

        # Reset pattern to flat (since we're redistributing evenly going forward)
        old_pattern = self.pattern
        self.pattern = "flat"
        self.pattern_config = None

        # Clear custom daily goals for future dates only (they don't make sense after recalculation)
        # Keep past custom goals for the record
        future_custom_goals = {}
        for date_str, goal in self.custom_daily_goals.items():
            goal_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            if goal_date < as_of_date:
                future_custom_goals[date_str] = goal

        cleared_goals_count = len(self.custom_daily_goals) - len(future_custom_goals)
        self.custom_daily_goals = future_custom_goals

        # Update weekend daily if weekend mode is 'different'
        if self.weekend_mode == 'different':
            # Set weekend daily to the same as regular daily for simplicity
            # User can adjust manually if they want different weekend goals
            self.weekend_daily = new_daily

        # Invalidate cache
        self.invalidate_daily_goals_cache()

        # Update last modified timestamp
        self.last_modified = datetime.datetime.now()

        return {
            'success': True,
            'words_completed': words_completed,
            'words_remaining': words_remaining,
            'remaining_writing_days': remaining_writing_days,
            'old_daily': old_daily,
            'new_daily': new_daily,
            'old_pattern': old_pattern,
            'new_pattern': self.pattern,
            'cleared_custom_goals': cleared_goals_count,
            'past_goals_preserved': past_goals_preserved,
            'end_date': end_date
        }

    def to_dict(self):
        """Convert plan to dictionary for serialization."""
        return {
            'name': self.name,
            'daily': self.daily,
            'total': self.total,
            'time': self.time,
            'words': self.words,
            'spare_days_dates': [d.isoformat() if hasattr(d, 'isoformat') else d for d in self.spare_days_dates],
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'pattern': self.pattern,
            'pattern_config': self.pattern_config,
            'progress': self.progress,
            'weekend_mode': self.weekend_mode,
            'weekend_daily': self.weekend_daily,
            'weekend_days': self.weekend_days,
            'custom_daily_goals': self.custom_daily_goals,
            # Multiple plans management fields
            'status': self.status,
            'tags': self.tags,
            'category': self.category,
            'is_active': self.is_active,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'preexisting_words': self.preexisting_words,
            'locked_goals': self.locked_goals,
        }

    @classmethod
    def from_dict(cls, data):
        """Create plan from dictionary."""
        if not isinstance(data, dict):
            raise TypeError(f"Expected dictionary, got {type(data).__name__}")

        # Convert spare days dates from ISO strings to datetime objects
        spare_days_dates = []
        try:
            start_date = datetime.datetime.fromisoformat(data['start_date']) if data.get('start_date') else None
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid start_date format in plan data: {e}")

        for item in data.get('spare_days_dates', []):
            try:
                if isinstance(item, str):
                    # New format: ISO date string
                    spare_days_dates.append(datetime.datetime.fromisoformat(item))
                elif isinstance(item, int):
                    # Old format: day number - convert to date if we have start_date
                    if start_date:
                        converted_date = start_date + timedelta(days=item - 1)
                        spare_days_dates.append(converted_date)
                    # else: skip old format spare days if no start_date
                else:
                    # Already a datetime object
                    spare_days_dates.append(item)
            except (ValueError, TypeError) as e:
                # Skip invalid spare day dates with a warning
                print(f"Warning: Skipping invalid spare day date '{item}': {e}")

        # Parse created_date with error handling
        try:
            created_date = datetime.datetime.fromisoformat(data['created_date']) if data.get('created_date') else None
        except (ValueError, TypeError) as e:
            print(f"Warning: Invalid created_date format, using None: {e}")
            created_date = None

        # Parse last_modified with error handling
        try:
            last_modified = datetime.datetime.fromisoformat(data['last_modified']) if data.get('last_modified') else None
        except (ValueError, TypeError) as e:
            # Silently default to None for old plans without last_modified
            last_modified = None

        # Validate numeric values
        try:
            daily = float(data.get('daily', 0))
            total = float(data.get('total', 0))
            time = float(data.get('time', 0))
            words = float(data.get('words', 0))
            weekend_daily = float(data.get('weekend_daily', 0))
            preexisting_words = int(data.get('preexisting_words', 0))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid numeric value in plan data: {e}")

        progress = dict(data.get('progress', {}))

        # Old files stored pre-existing words as progress on the day before the start
        if 'preexisting_words' not in data and start_date:
            pre_start_key = (start_date - timedelta(days=1)).strftime('%Y-%m-%d')
            preexisting_words = progress.pop(pre_start_key, 0)

        return cls(
            name=data.get('name'),
            daily=daily,
            total=total,
            time=time,
            words=words,
            spare_days_dates=spare_days_dates,
            start_date=start_date,
            created_date=created_date,
            pattern=data.get('pattern', 'flat'),
            pattern_config=data.get('pattern_config', {}),
            progress=progress,
            weekend_mode=data.get('weekend_mode', 'same'),
            weekend_daily=weekend_daily,
            weekend_days=data.get('weekend_days', [5, 6]),
            custom_daily_goals=data.get('custom_daily_goals', {}),
            # Multiple plans management fields (with defaults for old plans)
            status=data.get('status', 'active'),
            tags=data.get('tags', []),
            category=data.get('category'),
            is_active=data.get('is_active', False),
            last_modified=last_modified,
            preexisting_words=preexisting_words,
            locked_goals=data.get('locked_goals', {}),
        )

    def to_json(self):
        """Convert plan to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str):
        """Create plan from JSON string."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupted or invalid JSON data: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing JSON: {e}")
        return cls.from_dict(data)
