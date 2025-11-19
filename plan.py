import datetime
from datetime import timedelta
import math
import json

"""class for the Plan."""


class Plan():
    """simple class to store a plan and its attributes."""
    def __init__(self, daily=0, total=0, time=0, words=0, name=None, start_date=None, created_date=None, spare_days_dates=None, source_file=None, pattern="flat", pattern_config=None, progress=None, weekend_mode="same", weekend_daily=0, weekend_days=None, custom_daily_goals=None, status="active", tags=None, category=None, is_active=False, last_modified=None):
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

        self.daily = daily
        self.total = total
        self.time = time  # Writing days (not including spare days)
        self.words = words # this is the amount of words in the current plan
        self.name = name  # Name/title of the writing project
        self.start_date = start_date  # When the writing plan starts
        self.created_date = created_date or datetime.datetime.now()  # When this plan was created
        self.spare_days_dates = spare_days_dates or []  # List of actual dates (datetime objects) with 0 words
        self.source_file = source_file  # Path to the file this plan was loaded from (None for new plans)
        self.pattern = pattern  # Pattern type: flat, valley, mountain, rising, declining, random
        self.pattern_config = pattern_config or {}  # Pattern-specific configuration
        self._daily_goals_cache = None  # Cache for calculated daily goals
        self.progress = progress or {}  # Dictionary mapping date strings (YYYY-MM-DD) to actual word counts
        self.weekend_mode = weekend_mode  # "same", "different", "spare"
        self.weekend_daily = weekend_daily  # Daily goal for weekends (if mode is "different")
        self.weekend_days = weekend_days or [5, 6]  # Saturday=5, Sunday=6 (0-indexed from Monday)
        self.custom_daily_goals = custom_daily_goals or {}  # Date string -> custom word count

        # Multiple plans management fields
        self.status = status  # "active", "archived", "completed"
        self.tags = tags or []  # List of tag strings (e.g., ["urgent", "fiction"])
        self.category = category  # Category string (e.g., "novel", "blog", "academic")
        self.is_active = is_active  # Boolean flag for the currently active plan
        self.last_modified = last_modified or datetime.datetime.now()  # When this plan was last modified

    @property
    def spare_days(self):
        """Get count of spare days for backward compatibility."""
        return len(self.spare_days_dates)

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
        self.daily = self.total / self.time
        self.invalidate_daily_goals_cache()

    def calculate_time(self):
        """Calculate the time needed to complete your work."""
        if self.daily <= 0:
            raise ValueError(f"Cannot calculate time: daily words must be greater than 0 (got {self.daily})")
        if self.total < 0:
            raise ValueError(f"Cannot calculate time: total cannot be negative (got {self.total})")
        self.time = self.total / self.daily
        self.invalidate_daily_goals_cache()

    def calculate_words(self):
        """calculate the number or words."""
        if self.daily < 0:
            raise ValueError(f"Cannot calculate total words: daily cannot be negative (got {self.daily})")
        if self.time < 0:
            raise ValueError(f"Cannot calculate total words: time cannot be negative (got {self.time})")
        self.total = self.daily * self.time
        self.invalidate_daily_goals_cache()

    def show(self):
        """Shows basic data."""
        print(self.total, self.time, self.daily)

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

        num_days = int(self.time)
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
        adjustment = self.total / current_total
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
        adjustment = self.total / current_total
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
        adjustment = self.total / current_total
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
        adjustment = self.total / current_total
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
        adjustment = self.total / current_total
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
            # Check if it's a spare day first
            if self.is_spare_day(date):
                return 0

            # Check for custom daily goal for this specific date
            date_key = date.strftime('%Y-%m-%d')
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

        # Calculate total calendar days (writing days + spare days)
        total_calendar_days = int(self.time) + self.spare_days

        # Sum up all daily goals
        total_words = 0
        current_date = self.start_date

        for day_num in range(total_calendar_days):
            daily_goal = self.get_daily_goal(date=current_date)
            total_words += daily_goal
            current_date += timedelta(days=1)

        # Update the plan's total
        self.total = total_words
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
        """Get total words written so far across all days."""
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

        actual_words = self.get_total_written()
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
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid numeric value in plan data: {e}")

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
            progress=data.get('progress', {}),
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
