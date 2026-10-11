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

# Upper limits for numbers typed at prompts (values must also be > 0).
# MAX_DAYS also caps the search for the number of days in Plan.calculate_time().
MAX_WORDS = 10000000  # 10 million words: totals and pre-existing words
MAX_DAYS = 36500  # 100 years
MAX_DAILY_WORDS = 100000  # daily, weekend and custom day goals

# Plan defaults (weekend days, weekend mode, pattern, status) are not here on
# purpose: they are also what old plan files without those fields load as, so
# they live with the file format in Plan.__init__ / Plan.from_dict.

# Multiple plans management (the first status is what plans without one get)
PLAN_STATUSES = ["active", "archived", "completed"]

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
