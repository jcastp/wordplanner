import datetime
import math
import json

"""class for the Plan."""


class Plan():
    """simple class to store a plan and its attributes."""
    def __init__(self, daily=0, total=0, time=0, words=0, name=None, start_date=None, created_date=None):
        """Initialize the values."""
        self.daily = daily
        self.total = total
        self.time = time
        self.words = words # this is the amount of words in the current plan
        self.name = name  # Name/title of the writing project
        self.start_date = start_date  # When the writing plan starts
        self.created_date = created_date or datetime.datetime.now()  # When this plan was created

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
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'created_date': self.created_date.isoformat() if self.created_date else None,
        }

    @classmethod
    def from_dict(cls, data):
        """Create plan from dictionary."""
        return cls(
            name=data.get('name'),
            daily=data.get('daily', 0),
            total=data.get('total', 0),
            time=data.get('time', 0),
            words=data.get('words', 0),
            start_date=datetime.datetime.fromisoformat(data['start_date']) if data.get('start_date') else None,
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
