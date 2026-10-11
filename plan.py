import datetime
from datetime import timedelta
import math
import json
import random
import config

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
    def __init__(self, daily=0, total=0, time=0, words=0, name=None, start_date=None, created_date=None, spare_days_dates=None, source_file=None, pattern="flat", pattern_config=None, progress=None, weekend_mode="same", weekend_daily=0, weekend_days=None, custom_daily_goals=None, status="active", tags=None, category=None, is_active=False, last_modified=None, preexisting_words=0, locked_goals=None, schedule_adjustment=0):
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
        self._schedule_cache = None  # (inputs, schedule) from build_schedule()
        self.progress = progress or {}  # Dictionary mapping date strings (YYYY-MM-DD) to actual word counts
        self.weekend_mode = weekend_mode  # "same", "different", "spare"
        self.weekend_daily = weekend_daily  # Daily goal for weekends (if mode is "different")
        self.weekend_days = weekend_days or [5, 6]  # Saturday=5, Sunday=6 (0-indexed from Monday)
        self.custom_daily_goals = custom_daily_goals or {}  # Date string -> custom word count
        self.locked_goals = locked_goals or {}  # Date string -> goal frozen once the day is past
        # Words added to the future schedule by "recalculate from progress" so it covers
        # what is actually left (negative when ahead). See build_schedule().
        self.schedule_adjustment = schedule_adjustment

        # Multiple plans management fields
        self.status = status  # "active", "archived", "completed"
        self.tags = tags or []  # List of tag strings (e.g., ["urgent", "fiction"])
        self.category = category  # Category string (e.g., "novel", "blog", "academic")
        self.is_active = is_active  # Boolean flag for the currently active plan
        self.last_modified = last_modified or datetime.datetime.now()  # When this plan was last modified
        self._saved_state = None  # What was last loaded or saved (see has_unsaved_changes)

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
        """
        Calculate the daily goal from the total and time (keeps the total).

        `daily` is the goal of an ordinary open day once fixed days (locked,
        spare, custom, weekend) are taken out of the words left.
        """
        if self.time <= 0:
            raise ValueError(f"Cannot calculate daily words: time must be greater than 0 (got {self.time})")
        if self.total < 0:
            raise ValueError(f"Cannot calculate daily words: total cannot be negative (got {self.total})")
        self.sync_daily()

    def calculate_time(self):
        """
        Calculate how many writing days are needed at the current daily goal (keeps the total).

        Finds the fewest whole days whose schedule fits the words at `daily`,
        then lowers `daily` slightly so the schedule adds up to exactly the total.
        Never shrinks the plan below its locked (past) writing days.
        """
        if self.daily <= 0:
            raise ValueError(f"Cannot calculate time: daily words must be greater than 0 (got {self.daily})")
        if self.total < 0:
            raise ValueError(f"Cannot calculate time: total cannot be negative (got {self.total})")

        daily = self.daily
        min_days = self.min_writing_days()

        def fits(days):
            self.time = days
            return self.total_for_daily(daily) >= self.total - 1e-6

        days = max(min_days, whole_days(self.words_to_schedule / daily))
        while not fits(days) and days < config.MAX_DAYS:
            days += 1
        while days > min_days and fits(days - 1):
            days -= 1

        self.time = days
        if self.time > 0:
            self.sync_daily()

    def writing_days_until(self, end_date):
        """Writing days (days that aren't spare dates) from the start date to end_date, inclusive."""
        if not self.start_date or end_date is None:
            return 0
        spare = {d.date() for d in self.spare_days_dates if not isinstance(d, int)}
        span = (to_midnight(end_date) - self.start_date).days + 1
        return sum(1 for offset in range(max(0, span))
                   if (self.start_date + timedelta(days=offset)).date() not in spare)

    def keep_end_date(self, end_date):
        """
        Set `time` so the plan ends on end_date (keeps the total).

        Used after spare days are added or removed: the words are spread over
        the writing days left before end_date. If end_date itself is now a
        spare day, the plan ends on the last writing day before it. Never
        shrinks the plan below its locked (past) writing days.
        """
        self.time = max(self.min_writing_days(), self.writing_days_until(end_date))
        if self.time > 0:
            self.sync_daily()

    def calculate_words(self):
        """Calculate the total from the daily goal and time (keeps the daily goal)."""
        if self.daily < 0:
            raise ValueError(f"Cannot calculate total words: daily cannot be negative (got {self.daily})")
        if self.time < 0:
            raise ValueError(f"Cannot calculate total words: time cannot be negative (got {self.time})")
        self.total = self.total_for_daily(self.daily)

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

    def min_writing_days(self):
        """Fewest writing days the plan can have without dropping locked (past) days."""
        if not self.start_date:
            return 0
        spare = {d.date() for d in self.spare_days_dates if not isinstance(d, int)}
        locked_days = (datetime.datetime.strptime(k, '%Y-%m-%d') for k in self.locked_goals)
        return sum(1 for d in locked_days if d >= self.start_date and d.date() not in spare)

    def _locked_words(self):
        """Sum of the locked goals inside the plan window."""
        goals = self.build_schedule()['goals']
        return sum(goals[k] for k in self.locked_goals if k in goals)

    # ------------------------------------------------------------------
    # The schedule: one pass that decides every day's goal
    # ------------------------------------------------------------------

    def invalidate_daily_goals_cache(self):
        """Drop the cached schedule. Not required (the cache checks its inputs), kept for callers."""
        self._schedule_cache = None

    def _schedule_key(self):
        """Everything the schedule depends on; any change rebuilds it."""
        return (
            self.total, self.preexisting_words, self.schedule_adjustment, self.time, self.start_date,
            tuple(sorted(d for d in self.spare_days_dates if not isinstance(d, int))),
            self.weekend_mode, self.weekend_daily, tuple(self.weekend_days),
            tuple(sorted(self.custom_daily_goals.items())),
            tuple(sorted(self.locked_goals.items())),
            self.pattern, json.dumps(self.pattern_config or {}, sort_keys=True, default=str),
        )

    def _random_seed(self):
        """Seed for the random pattern, stored on first use so goals don't change between runs."""
        if self.pattern_config is None:
            self.pattern_config = {}
        if 'seed' not in self.pattern_config:
            self.pattern_config['seed'] = random.randint(1, 1000000)
        return self.pattern_config['seed']

    def _pattern_weights(self, num_positions):
        """
        Relative weight of each writing-day position for the current pattern.

        Weights average 1: a flat pattern gives 1 for every day, and `daily`
        is the goal of a day with weight 1.
        """
        n = int(num_positions)
        if n <= 0:
            return []
        config_ = self.pattern_config or {}

        if self.pattern == "valley":
            # Start high, ease in the middle, finish high
            peak = config_.get('peak_multiplier', 1.5)
            valley = config_.get('valley_multiplier', 0.7)
            raw = [valley + (peak - valley) * (math.cos(p / n * 2 * math.pi) + 1) / 2 for p in range(n)]
        elif self.pattern == "mountain":
            # Start low, peak in the middle, ease at the end
            peak = config_.get('peak_multiplier', 1.5)
            valley = config_.get('valley_multiplier', 0.7)
            raw = [valley + (peak - valley) * math.sin(p / n * math.pi) for p in range(n)]
        elif self.pattern in ("rising", "declining"):
            default_start, default_end = (0.5, 1.5) if self.pattern == "rising" else (1.5, 0.5)
            start = config_.get('start_multiplier', default_start)
            end = config_.get('end_multiplier', default_end)
            raw = [start + (end - start) * (p / (n - 1) if n > 1 else 0) for p in range(n)]
        elif self.pattern == "random":
            rng = random.Random(self._random_seed())
            low = config_.get('min_multiplier', 0.5)
            high = config_.get('max_multiplier', 1.5)
            raw = [rng.uniform(low, high) for _ in range(n)]
        else:
            raw = [1.0] * n

        raw_sum = sum(raw)
        if raw_sum <= 0:
            return [1.0] * n
        return [w * n / raw_sum for w in raw]

    def build_schedule(self):
        """
        Decide the goal of every calendar day of the plan, in one pass.

        Days fall into two groups:
        - fixed: locked past days; spare days and weekend-spare days (0);
          custom goals; weekend days in "different" mode (weekend_daily);
        - adjustable: every other writing day.

        The adjustable days share the words left after the fixed days, weighted
        by the pattern. Pattern weights follow writing-day position (spare and
        weekend-spare days don't take a position), so the shape doesn't shift.
        The schedule adds up to words_to_schedule + schedule_adjustment, unless
        the fixed days alone are more than that.

        Without a start date there are no dates yet: `time` abstract writing
        days, all adjustable.

        Returns:
            dict with 'goals' ({date string: goal}, in date order), 'level' (goal
            of a weight-1 adjustable day), 'adjustable_weight', 'adjustable_days'
            and 'fixed_words'.
        """
        if self.pattern == "random":
            self._random_seed()
        key = self._schedule_key()
        if self._schedule_cache is not None and self._schedule_cache[0] == key:
            return self._schedule_cache[1]

        goals = {}
        fixed = {}
        adjustable = {}

        if self.start_date:
            days = list(self.plan_days())
            spare = {d.date() for d in self.spare_days_dates if not isinstance(d, int)}

            def is_rest_day(day):
                return day.date() in spare or (self.weekend_mode == "spare" and self.is_weekend(day))

            positions = [day.strftime('%Y-%m-%d') for day in days if not is_rest_day(day)]
            weight_of = dict(zip(positions, self._pattern_weights(len(positions))))

            for day in days:
                date_key = day.strftime('%Y-%m-%d')
                if date_key in self.locked_goals:
                    fixed[date_key] = self.locked_goals[date_key]
                elif is_rest_day(day):
                    fixed[date_key] = 0
                elif date_key in self.custom_daily_goals:
                    fixed[date_key] = self.custom_daily_goals[date_key]
                elif self.weekend_mode == "different" and self.is_weekend(day):
                    fixed[date_key] = self.weekend_daily
                else:
                    adjustable[date_key] = weight_of[date_key]
            adjustable_weight = sum(adjustable.values())
            adjustable_days = len(adjustable)
        else:
            days = []
            adjustable_weight = sum(self._pattern_weights(self.time))
            adjustable_days = self.time

        fixed_words = sum(fixed.values())
        target = self.words_to_schedule + self.schedule_adjustment - fixed_words
        level = max(0.0, target / adjustable_weight) if adjustable_weight > 0 else 0.0

        for day in days:
            date_key = day.strftime('%Y-%m-%d')
            goals[date_key] = fixed[date_key] if date_key in fixed else level * adjustable[date_key]

        schedule = {
            'goals': goals,
            'level': level,
            'adjustable_weight': adjustable_weight,
            'adjustable_days': adjustable_days,
            'fixed_words': fixed_words,
        }
        self._schedule_cache = (key, schedule)
        return schedule

    def sync_daily(self):
        """Set `daily` to the goal of an ordinary open day in the current schedule."""
        schedule = self.build_schedule()
        if schedule['adjustable_weight'] > 0:
            self.daily = schedule['level']

    def total_for_daily(self, daily):
        """
        The total that gives ordinary open days a goal of `daily`, fixed days unchanged.

        Used to "keep the daily goal" when something else changes.
        """
        schedule = self.build_schedule()
        return (self.preexisting_words + schedule['fixed_words']
                + daily * schedule['adjustable_weight'] - self.schedule_adjustment)

    def calculate_pattern_goals(self):
        """
        Pattern goals for `time` writing days, ignoring dates and overrides.

        Kept for callers that only need the pattern shape; the real per-day
        goals come from build_schedule().
        """
        weights = self._pattern_weights(self.time)
        per_weight = self.words_to_schedule / self.time if self.time > 0 else 0
        return [per_weight * w for w in weights]

    def get_daily_goal(self, day_index=None, date=None):
        """
        Get the goal for a day.

        Args:
            day_index: 0-based writing day, for plans without a start date
            date: datetime of the day (preferred)

        Returns:
            The day's goal from the schedule. Locked goals are returned even
            outside the plan window (e.g. after a start date change); other
            days outside the window have no goal (0).
        """
        if date is not None:
            date_key = date.strftime('%Y-%m-%d')
            if date_key in self.locked_goals:
                return self.locked_goals[date_key]
            if not self.start_date:
                return self.daily
            return self.build_schedule()['goals'].get(date_key, 0)

        goals = self.calculate_pattern_goals()
        if day_index is None or not 0 <= day_index < len(goals):
            return self.daily
        return goals[day_index]

    def set_custom_daily_goal(self, date, word_count):
        """
        Set a custom word goal for a specific date.

        Args:
            date: datetime object
            word_count: custom word count for this day
        """
        date_key = date.strftime('%Y-%m-%d')
        self.custom_daily_goals[date_key] = int(word_count)

    def remove_custom_daily_goal(self, date):
        """
        Remove a custom word goal for a specific date.

        Args:
            date: datetime object
        """
        date_key = date.strftime('%Y-%m-%d')
        if date_key in self.custom_daily_goals:
            del self.custom_daily_goals[date_key]

    def recalculate_total_from_daily_goals(self):
        """
        Set the total so ordinary open days keep the current daily goal.

        Used for "keep days constant, adjust total" after a change such as a
        custom goal or weekend setting.

        Returns:
            float: The new total word count
        """
        if not self.start_date:
            # Can't recalculate without a start date
            return self.total

        self.total = self.total_for_daily(self.daily)
        return self.total

    MILESTONES = (0.25, 0.50, 0.75, 1.0)

    def milestones(self, fractions=MILESTONES):
        """
        When the schedule reaches each share of the goal (P18).

        Walks the schedule day by day (spare days, weekends, patterns, custom
        and locked goals included). A milestone's words are a share of the full
        goal, pre-existing words included, like the completion percentage.
        Pre-existing words count from the start; schedule_adjustment is taken
        out so that 100% falls on the end date after a recalculation.

        Returns:
            List of dicts, one per fraction: 'fraction', 'words' (rounded),
            'date' (None if pre-existing words already reach it), 'day'
            (calendar day of the plan, 1-based, 0 if already reached) and
            'reached' (words written so far are enough)
        """
        days = list(self.plan_days())
        goals = self.build_schedule()['goals']
        written = self.get_total_written()

        result = []
        for fraction in fractions:
            target = fraction * self.total
            cumulative = self.preexisting_words - self.schedule_adjustment
            date, day_number = None, 0
            if cumulative < target - 0.5:
                # Rounding never leaves the last milestone unreached
                date, day_number = (days[-1], len(days)) if days else (None, 0)
                for number, day in enumerate(days, 1):
                    cumulative += goals[day.strftime('%Y-%m-%d')]
                    if cumulative >= target - 0.5:
                        date, day_number = day, number
                        break
            result.append({
                'fraction': fraction,
                'words': round(target),
                'date': date,
                'day': day_number,
                'reached': written >= target - 0.5,
            })
        return result

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

    def is_rest_day(self, date):
        """A plan day with a goal of 0: spare day, weekend rest day, custom or locked 0."""
        end = self.end_date
        if not self.start_date or end is None or not self.start_date <= date <= end:
            return False
        return self.get_daily_goal(date=date) == 0

    def get_current_streak(self):
        """
        Number of consecutive days with words written, counting back from today.

        Rest days (goal 0) don't break the streak; writing on one still
        counts. Today only counts once words are logged: until then the
        streak runs up to yesterday (decision 4: today isn't over yet).
        """
        if not self.start_date or not self.progress:
            return 0

        today = to_midnight(datetime.datetime.now())
        current_date = today
        streak = 0

        while current_date >= self.start_date:
            if self.progress.get(current_date.strftime('%Y-%m-%d'), 0) > 0:
                streak += 1
            elif current_date != today and not self.is_rest_day(current_date):
                break
            current_date -= timedelta(days=1)

        return streak

    def is_on_track(self, as_of_date=None):
        """
        Check if progress is on track based on expected progress.

        Compares the goals up to as_of_date (inclusive) with everything
        written, including any words already logged after it.

        Args:
            as_of_date: last day whose goal counts as expected (default:
                yesterday, because today isn't over yet; words written today
                still count, so they can only help)

        Returns:
            Tuple of (bool, dict) where bool is True if on track,
            and dict contains detailed info
        """
        if not self.start_date:
            return True, {'message': 'No start date set'}

        if as_of_date is None:
            as_of_date = to_midnight(datetime.datetime.now()) - timedelta(days=1)

        # Calculate expected progress up to this date
        goals = self.build_schedule()['goals']
        expected_words = 0
        days_elapsed = 0

        for day in self.plan_days():
            if day > as_of_date:
                break
            expected_words += goals[day.strftime('%Y-%m-%d')]
            if not self.is_spare_day(day):
                days_elapsed += 1

        # After a recalculation from progress, "on track" means following the
        # new baseline: expected words start from what had been written then
        if days_elapsed > 0:
            expected_words = max(0, expected_words - self.schedule_adjustment)

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

        - 'no_goal': outside the plan (or no start date);
        - 'spare': a rest day (goal 0) with nothing written; writing on it is 'exceeded';
        - 'future': after today, or today with nothing logged yet (decision 4);
        - 'exceeded', 'met', 'partial': words written against the goal;
        - 'missed': a past day with a goal and no words.
        """
        if not self.start_date:
            return 'no_goal'

        date = to_midnight(date)
        today = to_midnight(datetime.datetime.now())
        end = self.end_date

        # Days outside the plan have no goal
        if date < self.start_date or end is None or date > end:
            return 'no_goal'

        daily_goal = self.get_daily_goal(date=date)
        actual = self.get_progress_for_date(date) or 0

        # Rest days (spare, weekend rest, goal 0) are never missed
        if daily_goal == 0:
            return 'exceeded' if actual > 0 else 'spare'

        if date > today:
            return 'future'

        if actual >= daily_goal:
            return 'exceeded' if actual > daily_goal else 'met'
        if actual > 0:
            return 'partial'
        # Today isn't over: nothing logged yet isn't a miss (decision 4)
        return 'future' if date == today else 'missed'

    def _rebase_on_progress(self, as_of_date):
        """
        Lock days before as_of_date and point the open days at the words actually left.

        Locked days keep their planned goals (decision 2), so without an
        adjustment the open days would cover total - planned past, not what
        is really left. schedule_adjustment bridges the two.

        Each locked day is credited with what was written on it, except days
        from today on (as_of_date can be tomorrow): today isn't over, so it is
        credited with at least its goal. Progress on other days counts as written.

        Returns:
            Number of days newly locked
        """
        newly_locked = self.lock_past_goals(as_of_date)

        today = to_midnight(datetime.datetime.now())
        goals = self.build_schedule()['goals']
        locked_keys = [k for k in self.locked_goals if k in goals]

        credited = 0
        for date_key in locked_keys:
            written = self.progress.get(date_key, 0)
            if datetime.datetime.strptime(date_key, '%Y-%m-%d') < today:
                credited += written
            else:
                credited += max(self.locked_goals[date_key], written)
        written_elsewhere = sum(w for k, w in self.progress.items() if k not in locked_keys)

        locked_words = sum(self.locked_goals[k] for k in locked_keys)
        self.schedule_adjustment = locked_words - credited - written_elsewhere
        return newly_locked

    def _open_words(self):
        """Words the open (not locked) days of the schedule have to cover."""
        return self.words_to_schedule + self.schedule_adjustment - self._locked_words()

    def default_recalculation_date(self):
        """
        First day a recalculation from progress may change.

        Today is locked if words were already logged for it (the day has
        started), otherwise it is open and gets a new goal too.
        """
        today = to_midnight(datetime.datetime.now())
        if today.strftime('%Y-%m-%d') in self.progress:
            return today + timedelta(days=1)
        return today

    def move_start_date(self, new_start, shift_dated_days=False, as_of_date=None):
        """
        Move the plan to a new start date (decisions 7 and 10).

        - Spare days and custom goals stay on their calendar dates; outside
          the new window they are ignored. With shift_dated_days, the ones from
          today (as_of_date) on move by the same offset; past ones are history.
        - Progress never moves. Locked goals stay on their dates: inside the
          new window they keep their goals, outside it they are ignored.
        - Pre-existing words always follow the plan (they aren't dated).
        - The number of writing days is kept, so the end date moves too.
        - If the plan has started (locked days or progress), the open days are
          rebased to cover the words actually left, as recalculate_from_progress
          does: progress outside the new window still counts as written.

        Returns:
            dict with 'offset' (days), 'old_start', 'new_start', 'old_end',
            'new_end' and 'rebased'
        """
        new_start = to_midnight(new_start)
        old_start = self.start_date
        old_end = self.end_date
        offset = (new_start - old_start).days if old_start else 0

        if shift_dated_days and offset:
            today = to_midnight(as_of_date or datetime.datetime.now())
            shift = timedelta(days=offset)

            moved_spare = []
            for d in self.spare_days_dates:
                new_date = d + shift if d >= today else d
                if new_date not in moved_spare:
                    moved_spare.append(new_date)
            self.spare_days_dates = moved_spare

            past_goals = {}
            moved_goals = {}
            for date_key, goal in self.custom_daily_goals.items():
                date = datetime.datetime.strptime(date_key, '%Y-%m-%d')
                if date >= today:
                    moved_goals[(date + shift).strftime('%Y-%m-%d')] = goal
                else:
                    past_goals[date_key] = goal
            # A past goal is history: a shifted goal never replaces it
            self.custom_daily_goals = {**moved_goals, **past_goals}

        self.start_date = new_start

        rebased = bool(self.locked_goals or self.progress)
        if rebased:
            self._rebase_on_progress(self.default_recalculation_date())
        if self.time > 0:
            self.sync_daily()
        self.last_modified = datetime.datetime.now()

        return {
            'offset': offset,
            'old_start': old_start,
            'new_start': new_start,
            'old_end': old_end,
            'new_end': self.end_date,
            'rebased': rebased,
        }

    def _open_weekend_days(self, as_of_date):
        """Weekend days from as_of_date on whose goal comes from weekend_daily."""
        spare = {d.date() for d in self.spare_days_dates if not isinstance(d, int)}
        return sum(
            1 for day in self.plan_days()
            if day >= as_of_date and self.is_weekend(day)
            and day.date() not in spare
            and day.strftime('%Y-%m-%d') not in self.locked_goals
            and day.strftime('%Y-%m-%d') not in self.custom_daily_goals
        )

    def _remaining_writing_days(self, as_of_date):
        """Writing days from as_of_date to the end date (not spare, not weekend-spare)."""
        return sum(
            1 for day in self.plan_days()
            if day >= as_of_date
            and not self.is_spare_day(day)
            and not (self.weekend_mode == "spare" and self.is_weekend(day))
        )

    def recalculate_from_progress(self, as_of_date=None):
        """
        Recalculate the plan based on actual progress, redistributing remaining words
        across remaining days while keeping the end date fixed.

        Days before as_of_date are locked. From as_of_date on, the words
        actually left are spread over the open days with the plan's own
        pattern; future custom goals stay as they are, and weekend goals in
        "different" mode keep their ratio to the weekday goal.

        Args:
            as_of_date: First day to change (default: default_recalculation_date())

        Returns:
            dict with recalculation details, or None if recalculation not possible
        """
        if not self.start_date:
            return None

        if as_of_date is None:
            as_of_date = self.default_recalculation_date()
        as_of_date = to_midnight(as_of_date)

        words_completed = self.get_total_written()
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

        remaining_writing_days = self._remaining_writing_days(as_of_date)
        if remaining_writing_days == 0:
            return {
                'success': False,
                'reason': 'no_remaining_days',
                'words_completed': words_completed,
                'words_remaining': words_remaining
            }

        old_daily = self.daily
        weekend_ratio = (self.weekend_daily / old_daily
                         if self.weekend_mode == 'different' and old_daily > 0 else None)

        past_goals_preserved = self._rebase_on_progress(as_of_date)

        if weekend_ratio is not None:
            # Weekend days follow the weekday goal at the same ratio as before:
            # solve with weekends at 0, then share the open words between both
            self.weekend_daily = 0
            schedule = self.build_schedule()
            open_weekend_days = self._open_weekend_days(as_of_date)
            weekday_weight = schedule['adjustable_weight']
            spread = schedule['level'] * weekday_weight
            denominator = weekday_weight + weekend_ratio * open_weekend_days
            self.weekend_daily = weekend_ratio * spread / denominator if denominator > 0 else 0

        self.sync_daily()
        self.last_modified = datetime.datetime.now()

        future_custom_goals = sum(
            1 for date_str in self.custom_daily_goals
            if datetime.datetime.strptime(date_str, '%Y-%m-%d') >= as_of_date
        )

        return {
            'success': True,
            'as_of_date': as_of_date,
            'words_completed': words_completed,
            'words_remaining': words_remaining,
            'remaining_writing_days': remaining_writing_days,
            'old_daily': old_daily,
            'new_daily': self.daily,
            'pattern': self.pattern,
            'kept_custom_goals': future_custom_goals,
            'weekend_daily': self.weekend_daily if self.weekend_mode == 'different' else None,
            'past_goals_preserved': past_goals_preserved,
            'end_date': end_date
        }

    def adjust_time_from_progress(self, as_of_date=None):
        """
        Keep the daily goal and move the end date so the words actually left fit.

        Finishes early when ahead, extends the deadline when behind. Days
        before as_of_date (default: default_recalculation_date()) are locked.

        Returns:
            dict with old/new time and end date, or None without a start date
        """
        if not self.start_date:
            return None

        if as_of_date is None:
            as_of_date = self.default_recalculation_date()
        as_of_date = to_midnight(as_of_date)

        old_time = self.time
        old_end_date = self.end_date

        self._rebase_on_progress(as_of_date)
        self.calculate_time()
        self.last_modified = datetime.datetime.now()

        return {
            'old_time': old_time,
            'new_time': self.time,
            'old_end_date': old_end_date,
            'new_end_date': self.end_date,
            'daily': self.daily,
        }

    # Fields left out when checking for unsaved changes: they follow from the
    # rest (daily is synced from the schedule, past days are locked again on
    # the next visit) or change without the user doing anything
    _DERIVED_FIELDS = ('daily', 'locked_goals', 'last_modified')

    def _comparable_state(self):
        data = self.to_dict()
        for field in self._DERIVED_FIELDS:
            data.pop(field, None)
        return json.dumps(data, sort_keys=True, default=str)

    def mark_saved(self):
        """Remember the current state as saved (called after loading or saving)."""
        self._saved_state = self._comparable_state()

    def has_unsaved_changes(self):
        """True if the plan changed since it was loaded or saved, or was never saved."""
        return self._saved_state is None or self._comparable_state() != self._saved_state

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
            'schedule_adjustment': self.schedule_adjustment,
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
            schedule_adjustment = float(data.get('schedule_adjustment', 0))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid numeric value in plan data: {e}")

        progress = dict(data.get('progress', {}))

        # Old files stored pre-existing words as progress on the day before the start
        if 'preexisting_words' not in data and start_date:
            pre_start_key = (start_date - timedelta(days=1)).strftime('%Y-%m-%d')
            preexisting_words = progress.pop(pre_start_key, 0)

        loaded = cls(
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
            schedule_adjustment=schedule_adjustment,
        )

        # Files saved by the old "recalculate from progress" set a new daily goal
        # without matching the total (pattern reset to flat, pattern_config null).
        # Keep that baseline: adjust the schedule so open days keep that daily goal.
        recalculated_before = (
            'schedule_adjustment' not in data
            and 'pattern_config' in data and data['pattern_config'] is None
            and loaded.pattern == 'flat' and loaded.start_date is not None
        )
        if recalculated_before:
            loaded.schedule_adjustment = loaded.total_for_daily(loaded.daily) - loaded.total

        return loaded

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
