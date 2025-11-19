"""
Configuration Module

This module stores application-wide configuration constants and settings
for the wordplanner application.
"""

# Directory configuration
SAVE_DIRECTORY = ".wordplanner"
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

# Multiple plans management
PLAN_STATUSES = ["active", "archived", "completed"]
DEFAULT_PLAN_STATUS = "active"

PLAN_CATEGORIES = [
    "novel",
    "short-story",
    "novella",
    "blog",
    "article",
    "academic",
    "screenplay",
    "poetry",
    "non-fiction",
    "other"
]

PLAN_CATEGORY_DESCRIPTIONS = {
    "novel": "Full-length novel (50,000+ words)",
    "short-story": "Short story (under 10,000 words)",
    "novella": "Novella (10,000-50,000 words)",
    "blog": "Blog post or series",
    "article": "Article or essay",
    "academic": "Academic paper or thesis",
    "screenplay": "Screenplay or script",
    "poetry": "Poetry collection",
    "non-fiction": "Non-fiction book or content",
    "other": "Other writing project"
}

# Sorting options for plans
PLAN_SORT_OPTIONS = {
    "name": "Sort by name (A-Z)",
    "created": "Sort by creation date (newest first)",
    "modified": "Sort by last modified (newest first)",
    "completion": "Sort by completion percentage",
    "deadline": "Sort by deadline (end date)"
}
