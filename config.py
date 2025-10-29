"""
Configuration Module

This module stores application-wide configuration constants and settings
for the planeapalabras application.
"""

# Directory configuration
SAVE_DIRECTORY = ".planeapalabras"
PLANS_SUBDIRECTORY = "plans"
EXPORTS_SUBDIRECTORY = "exports"

# UI configuration
DEFAULT_HEADER_WIDTH = 50
DEFAULT_SECTION_WIDTH = 50

# Date format
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# Default values
DEFAULT_WEEKEND_DAYS = [5, 6]  # Saturday=5, Sunday=6 (0-indexed from Monday)
DEFAULT_WEEKEND_MODE = "same"  # Options: "same", "different", "spare"

# Pattern defaults
DEFAULT_PATTERN = "flat"
AVAILABLE_PATTERNS = ["flat", "valley", "mountain", "rising", "declining", "random"]

# Validation limits
MIN_WORDS = 1
MAX_WORDS = 10000000  # 10 million words
MIN_DAYS = 1
MAX_DAYS = 36500  # 100 years
MIN_DAILY_WORDS = 1
MAX_DAILY_WORDS = 100000

# Menu options
INITIAL_MENU_OPTIONS = {
    1: "Create a new plan from scratch",
    2: "Create plan from template",
    3: "Load an existing plan",
    0: "Exit"
}

PLAN_ACTIONS_MENU_OPTIONS = {
    1: "Update progress",
    2: "View progress summary",
    3: "View progress graphs & analytics",
    4: "Modify plan",
    5: "View calendar",
    6: "Export plan",
    7: "Save plan",
    0: "Go back to main menu"
}
