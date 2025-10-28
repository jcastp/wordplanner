"""Plan templates module for common writing goals."""

import datetime
import plan


class PlanTemplate:
    """Base class for plan templates."""

    def __init__(self, name, description, total, time=None, daily=None,
                 suggested_pattern=None, suggested_weekend_mode=None):
        """
        Initialize a plan template.

        Args:
            name: Template name
            description: Template description
            total: Total word count
            time: Number of days (optional if daily is provided)
            daily: Daily word count (optional if time is provided)
            suggested_pattern: Suggested writing pattern
            suggested_weekend_mode: Suggested weekend mode
        """
        self.name = name
        self.description = description
        self.total = total
        self.time = time
        self.daily = daily
        self.suggested_pattern = suggested_pattern
        self.suggested_weekend_mode = suggested_weekend_mode

    def create_plan(self, start_date=None, customize=False):
        """
        Create a plan from this template.

        Args:
            start_date: Plan start date (default: today)
            customize: Whether to allow customization

        Returns:
            Plan object based on template
        """
        if start_date is None:
            start_date = datetime.datetime.now()

        # Create plan with template values
        new_plan = plan.Plan(
            total=self.total,
            name=self.name,
            start_date=start_date
        )

        # Calculate the missing value
        if self.time and not self.daily:
            new_plan.time = self.time
            new_plan.calculate_daily()
        elif self.daily and not self.time:
            new_plan.daily = self.daily
            new_plan.calculate_time()
        else:
            # Both provided, use them directly
            new_plan.time = self.time
            new_plan.daily = self.daily

        return new_plan

    def __str__(self):
        """String representation of template."""
        if self.time and self.daily:
            return f"{self.name}: {self.total:,} words in {self.time} days ({self.daily:,.0f} words/day)"
        elif self.time:
            return f"{self.name}: {self.total:,} words in {self.time} days"
        elif self.daily:
            return f"{self.name}: {self.total:,} words at {self.daily:,.0f} words/day"
        else:
            return f"{self.name}: {self.total:,} words"


# Pre-defined templates
TEMPLATES = {
    'nanowrimo': PlanTemplate(
        name="NaNoWriMo",
        description="National Novel Writing Month - Write a 50,000 word novel in 30 days",
        total=50000,
        time=30,
        suggested_pattern="flat",
        suggested_weekend_mode="different"  # More time on weekends
    ),
    'short_story': PlanTemplate(
        name="Short Story",
        description="Complete a short story in one week",
        total=5000,
        time=7,
        suggested_pattern="rising",
        suggested_weekend_mode="different"
    ),
    'novel_draft': PlanTemplate(
        name="Novel Draft",
        description="Complete a full novel draft",
        total=80000,
        time=60,  # ~2 months at reasonable pace
        suggested_pattern="valley",
        suggested_weekend_mode="same"
    ),
    'blog_post': PlanTemplate(
        name="Blog Post",
        description="Write a comprehensive blog post",
        total=1500,
        time=1,
        suggested_pattern="flat",
        suggested_weekend_mode="same"
    ),
    'academic_paper': PlanTemplate(
        name="Academic Paper",
        description="Research paper or thesis chapter",
        total=10000,
        time=14,
        suggested_pattern="rising",
        suggested_weekend_mode="spare"  # Focus on weekdays
    ),
    'novella': PlanTemplate(
        name="Novella",
        description="A novella-length work (20,000-40,000 words)",
        total=30000,
        time=30,
        suggested_pattern="mountain",
        suggested_weekend_mode="different"
    ),
    'screenplay': PlanTemplate(
        name="Screenplay",
        description="Full-length screenplay (approx. 25,000 words / 100 pages)",
        total=25000,
        time=45,
        suggested_pattern="valley",
        suggested_weekend_mode="same"
    ),
    'weekly_goal': PlanTemplate(
        name="Weekly Writing Goal",
        description="Consistent weekly writing habit",
        total=7000,
        time=7,
        suggested_pattern="flat",
        suggested_weekend_mode="same"
    ),
    'sprint_1k': PlanTemplate(
        name="1K Daily Sprint",
        description="Build a daily 1,000 word habit for 30 days",
        total=30000,
        daily=1000,
        suggested_pattern="flat",
        suggested_weekend_mode="same"
    ),
    'sprint_500': PlanTemplate(
        name="500 Word Daily Habit",
        description="Gentle daily writing habit - 500 words per day",
        total=15000,
        daily=500,
        suggested_pattern="flat",
        suggested_weekend_mode="same"
    ),
}


def get_template(template_key):
    """
    Get a template by key.

    Args:
        template_key: Template identifier

    Returns:
        PlanTemplate or None if not found
    """
    return TEMPLATES.get(template_key)


def get_all_templates():
    """
    Get all available templates.

    Returns:
        Dictionary of all templates
    """
    return TEMPLATES


def list_templates_by_category():
    """
    Get templates organized by category.

    Returns:
        Dictionary of categories with template lists
    """
    return {
        'Popular': ['nanowrimo', 'short_story', 'blog_post'],
        'Long Form': ['novel_draft', 'novella', 'screenplay'],
        'Academic': ['academic_paper'],
        'Habits': ['weekly_goal', 'sprint_1k', 'sprint_500'],
    }


def create_custom_template(name, description, total, time=None, daily=None):
    """
    Create a custom template.

    Args:
        name: Template name
        description: Template description
        total: Total word count
        time: Number of days (optional)
        daily: Daily word count (optional)

    Returns:
        PlanTemplate object
    """
    return PlanTemplate(
        name=name,
        description=description,
        total=total,
        time=time,
        daily=daily
    )
