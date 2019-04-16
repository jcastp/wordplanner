import datetime
import math

"""class for the Plan."""


class Plan():
    """simple class to store a plan and its attributes."""
    def __init__(self, daily=0, total=0, time=0):
        """Initialize the values."""
        self.daily = daily
        self.total = total
        self.time = time

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
