import datetime
import math
import json

"""class for the Plan."""


class Plan():
    """simple class to store a plan and its attributes."""
    def __init__(self, daily=0, total=0, time=0, words=0, name=None, start_date=None, created_date=None, spare_days_dates=None, source_file=None, pattern="flat", pattern_config=None):
        """Initialize the values."""
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

    def calculate_daily(self):
        """calculate the daily amount of words needed, based on time
        and total words desired."""
        self.daily = self.total / self.time
        self.invalidate_daily_goals_cache()

    def calculate_time(self):
        """Calculate the time needed to complete your work."""
        self.time = self.total / self.daily
        self.invalidate_daily_goals_cache()

    def calculate_words(self):
        """calculate the number or words."""
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
            curve = math.cos(progress * math.pi)  # Goes from 1 to -1 to 1

            # Map curve to multiplier range
            # curve: 1 to -1, map to: peak_multiplier to valley_multiplier
            multiplier = valley_multiplier + (peak_multiplier - valley_multiplier) * (curve + 1) / 2

            goals.append(self.daily * multiplier)

        # Adjust to maintain total
        current_total = sum(goals)
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
            # Check if it's a spare day
            if self.is_spare_day(date):
                return 0

            # Calculate day index from start_date
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
        }

    @classmethod
    def from_dict(cls, data):
        """Create plan from dictionary."""
        # Convert spare days dates from ISO strings to datetime objects
        spare_days_dates = []
        start_date = datetime.datetime.fromisoformat(data['start_date']) if data.get('start_date') else None

        for item in data.get('spare_days_dates', []):
            if isinstance(item, str):
                # New format: ISO date string
                spare_days_dates.append(datetime.datetime.fromisoformat(item))
            elif isinstance(item, int):
                # Old format: day number - convert to date if we have start_date
                if start_date:
                    from datetime import timedelta
                    converted_date = start_date + timedelta(days=item - 1)
                    spare_days_dates.append(converted_date)
                # else: skip old format spare days if no start_date
            else:
                # Already a datetime object
                spare_days_dates.append(item)

        return cls(
            name=data.get('name'),
            daily=data.get('daily', 0),
            total=data.get('total', 0),
            time=data.get('time', 0),
            words=data.get('words', 0),
            spare_days_dates=spare_days_dates,
            start_date=start_date,
            created_date=datetime.datetime.fromisoformat(data['created_date']) if data.get('created_date') else None,
            pattern=data.get('pattern', 'flat'),
            pattern_config=data.get('pattern_config', {}),
        )

    def to_json(self):
        """Convert plan to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str):
        """Create plan from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
