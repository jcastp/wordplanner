import datetime
import math
import json

"""class for the Plan."""


class Plan():
    """simple class to store a plan and its attributes."""
    def __init__(self, daily=0, total=0, time=0, words=0, name=None, start_date=None, created_date=None, spare_days_dates=None, source_file=None):
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

    def calculate_time(self):
        """Calculate the time needed to complete your work."""
        self.time = self.total / self.daily

    def calculate_words(self):
        """calculate the number or words."""
        self.total = self.daily * self.time

    def show(self):
        """Shows basic data."""
        print(self.total, self.time, self.daily)

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
        )

    def to_json(self):
        """Convert plan to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str):
        """Create plan from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
