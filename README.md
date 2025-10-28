# planeapalabras - Word Count Planner

A comprehensive writing planning tool inspired by [pacemaker.press](https://pacemaker.press) that helps writers calculate, visualize, and manage their writing goals through an interactive console interface.

## Overview

Writing requires managing three key variables:
- **Total words** - Your word count goal (e.g., 50,000 words for NaNoWriMo)
- **Daily words** - How many words you can write per day (e.g., 1,667 words/day)
- **Time (days)** - How long you have to write (e.g., 30 days)

Given any two variables, **planeapalabras** calculates the third and provides:
- Beautiful calendar visualizations with day-by-day breakdown
- Flexible spare days management (holidays, weekends, breaks)
- Plan modification and recalculation
- Save/load functionality for multiple projects
- Weekly summaries and milestone tracking

## Features

### Core Features

#### Three Calculation Methods
Calculate any unknown variable from the other two:
1. Calculate days needed - Know your goal and daily capacity? Get your deadline
2. Calculate total words - Know your daily capacity and deadline? Get your achievable goal
3. Calculate daily words needed - Know your goal and deadline? Get your daily target

#### Flexible Plan Management
- Save & Load Plans - Save multiple writing projects with custom names
- Modify Plans - Change any value and automatically recalculate
  - Adjust total words, daily goals, or time
  - Choose which variable to recalculate
  - Modify multiple values at once
- Plan Actions Menu - Streamlined workflow for managing plans
  - Modify plan values
  - View calendar visualizations
  - Save changes

#### Spare Days Management
Mark specific dates as 0-word days for holidays, breaks, or urgent matters:
- Date-based selection - Use actual calendar dates (e.g., "2025-12-25")
- Multiple input formats:
  - Single dates: 2025-12-25
  - Multiple dates: 2025-12-25,2025-12-26,2025-12-31
  - Date ranges: 2025-12-24 to 2025-12-26
- Interactive management - Add, remove, or clear spare days anytime
- Smart display - See spare days with actual dates and day of week
- Automatic recalculation - Calendar duration extends to accommodate spare days

#### Calendar Visualization
Beautiful terminal-based calendar views powered by Rich:
- Monthly calendar - Day-by-day breakdown with:
  - Daily word goals clearly displayed
  - Spare days marked in orange
  - Weekend highlighting
  - Week numbers
- Weekly summary - Week-by-week breakdown showing:
  - Date ranges for each week
  - Writing days vs spare days per week
  - Weekly word totals
  - Cumulative progress
- Milestone tracking - Key progress points at 25%, 50%, 75%, 100%
- Customizable start date - Begin your plan on any date

#### Smart Input & Validation
- User-friendly defaults - Yes/no prompts with sensible defaults
- Date validation - Warns about dates in the past with confirmation
- Positive number validation - Ensures all values are valid
- Flexible date formats - Multiple ways to input dates
- Error handling - Clear error messages and recovery options

## Installation

### Requirements

- Python 3.13+ (see .python-version file)
- uv package manager (recommended) or pip

### Setup with uv (recommended)

```bash
# Clone the repository
git clone <repository-url>
cd planeapalabras

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install rich
# or install in editable mode
uv pip install -e .
```

## Usage

### Running the Application

```bash
python planea.py
```

Features:
- Complete feature set (all calculations, spare days, modifications)
- Rich-based calendar visualizations
- Number-based menu navigation
- Interactive spare days management
- Full plan modification capabilities
- Save/load with custom names

Navigation:
- Enter numbers to select menu options
- Follow prompts for input
- Ctrl+C to exit at any time

## Workflow Examples

### Example 1: Planning a Novel (NaNoWriMo Style)

Goal: Write a 50,000-word novel in November (30 days)

1. **Create Plan**
   ```
   Choose: "Calculate daily words needed"
   Total words: 50000
   Days available: 30
   Result: 1,667 words/day
   ```

2. Add Spare Days
   ```
   Select: "Modify plan" → "Spare days"
   Add Thanksgiving weekend: 2025-11-27 to 2025-11-29
   Result: Now need to write across 33 days (30 writing + 3 spare)
   ```

3. View Calendar
   ```
   Select: "View calendar" → "Both views"
   Start date: 2025-11-01
   See: Monthly calendar showing 1,667 words on each writing day
        Spare days marked clearly on Thanksgiving weekend
   ```

4. Save Plan
   ```
   Name: "NaNoWriMo 2025"
   Saved to: ~/.planeapalabras/plans/
   ```

### Example 2: Short Story with Weekends Off

Goal: Write a 5,000-word short story, writing only on weekdays

1. Create Plan
   ```
   Choose: "Calculate days needed"
   Total words: 5000
   Daily capacity: 500
   Result: 10 days needed
   ```

2. Add Weekend Spare Days
   ```
   Select: "Modify plan" → "Spare days"
   Add weekends: 2025-11-01,2025-11-02,2025-11-08,2025-11-09
   Result: 14 calendar days (10 writing + 4 weekend spare days)
   ```

3. Adjust if Needed
   ```
   Select: "Modify plan" → "Daily words"
   Increase to 600 words/day
   Result: Now need only 9 writing days (faster completion)
   ```

### Example 3: Loading and Modifying an Existing Plan

1. Load Plan
   ```
   Choose: "Load an existing plan"
   Select: "My Novel Draft 1"
   Review: 80,000 words, 2,000 words/day, 40 days
   ```

2. Modify the Plan
   ```
   Choose: "Modify plan"
   Change daily words from 2,000 to 1,500
   Result: Now need 54 days instead of 40
   ```

3. Update Spare Days
   ```
   Choose: "Spare days" → "Add"
   Add Christmas holiday: 2025-12-24 to 2025-12-26
   View updated calendar showing extended timeline
   ```

4. Save Changes
   ```
   Choose: "Save plan"
   Keep existing name or provide new name
   Plan updated with new values and spare days
   ```

## File Structure

```
planeapalabras/
├── planea.py                  # Console interface
├── plan.py                    # Core Plan class with calculations
├── calendar_view.py           # Calendar visualization with Rich
├── plan_storage.py            # Save/load functionality
├── README.md                  # This file - user documentation
├── CLAUDE.md                  # Developer documentation for AI
├── future-improvements.md     # Roadmap and planned features
├── todo.md                    # Original TODO list (deprecated)
├── pyproject.toml             # Project dependencies
└── .python-version            # Python version (3.13+)
```

## Storage

Plans are automatically saved to:
```
~/.planeapalabras/plans/
```

Each plan is stored as a JSON file with format:
```
PlanName_YYYYMMDD_HHMMSS.json
```

## What's New

### Version 1.1 (Latest)
- Date-based spare days - Mark specific calendar dates (e.g., 2025-12-25) instead of day numbers
- Multiple input formats - Single dates, comma-separated lists, or date ranges
- Interactive spare days manager - Add, remove, or clear spare days anytime
- Plan modification menu - Comprehensive options to modify any plan value
- User-friendly defaults - Yes/no prompts with sensible defaults ([Y/n] or [y/N])
- Date validation - Warns about past dates with confirmation option
- Backward compatibility - Automatically migrates old plans to new format
- Improved documentation - Updated README, CLAUDE.md, and new future-improvements.md

### Version 1.0
- Three calculation methods (days, words, daily)
- Save and load plans
- Calendar visualizations (monthly, weekly, milestones)
- Plan storage in JSON format

## Roadmap

See future-improvements.md for the comprehensive roadmap with 30+ planned features.

### Next Up (High Priority)
- Writing Patterns - Variable daily goals (valley, mountain, rising, declining, random)
- Weekend Planning - Different word goals for weekends vs weekdays
- Progress Tracking - Record actual words written each day
- Plan Recalculation - Adjust plans based on actual progress
- Progress Graphs - Visual comparison of expected vs actual words
- Quick Actions - "Mark all weekends as spare", holiday templates, etc.

### Coming Soon (Medium Priority)
- Plan templates (NaNoWriMo, Short Story, Academic Paper, etc.)
- Export functionality (CSV, PDF, iCal for calendar apps)
- Notifications and reminders
- Writing analytics and statistics
- Writing session timer integration

### Future Possibilities
- Web interface
- Mobile apps
- AI-powered suggestions
- Collaboration features
- Integration with writing tools (Scrivener, Word, etc.)

## Tips & Best Practices

### For Best Results

1. Be realistic with daily goals - Consider your schedule and energy levels
2. Use spare days liberally - Mark holidays, weekends, and known busy days
3. Start with the end in mind - If you have a deadline, calculate daily words needed
4. Review and adjust - Plans are meant to be modified as circumstances change
5. Save multiple versions - Create variations of your plan to explore different scenarios

### Common Use Cases

- NaNoWriMo - 50,000 words in 30 days = approximately 1,667 words/day
- Academic papers - 10,000 words in 2 weeks (weekdays only)
- Blog posts - 1,500 words in 1-2 days
- Novel drafts - 80,000-100,000 words over 2-3 months
- Short stories - 5,000-10,000 words in 1-2 weeks

### Troubleshooting

Problem: Calendar shows too many months
Solution: Your plan is very long. Consider breaking it into multiple smaller plans.

Problem: Can't add spare days
Solution: Make sure you've viewed a calendar first to set a start date.

Problem: Old plan has weird spare days
Solution: The app will automatically convert old plans to the new format. Re-save to update.

Problem: Numbers seem off after modification
Solution: The app recalculates based on the two values you provide. Check which calculation method was used.

## FAQ

Q: Can I have different word goals on different days?
A: Not yet, but "Writing Patterns" is planned (see roadmap).

Q: Can I track my actual progress?
A: Not yet, but "Progress Tracking" is high priority (see roadmap).

Q: Can I export my plan to Google Calendar?
A: Not yet, but iCal export is planned.

Q: Where are my plans stored?
A: In ~/.planeapalabras/plans/ as JSON files.

Q: Can I share my plan with others?
A: You can share the JSON file manually. Cloud sync is on the long-term roadmap.

Q: Does this work on Windows/Mac?
A: Yes! It's pure Python and should work on any platform with Python 3.13+.

## Contributing

This is a personal project, but suggestions and feedback are welcome!

### How to Contribute

- Report bugs - Open an issue describing the problem
- Suggest features - Share your ideas for improvements
- Improve documentation - Fix typos or clarify instructions
- Test - Try the app and report issues
- Star the repo - Show your support

## Support

If you find this tool helpful for your writing journey, consider:
- Sharing it with other writers
- Reporting bugs or suggesting features
- Contributing to the documentation
- Starring the repository

## License

[Your license here]

## Acknowledgments

- Inspired by [pacemaker.press](https://pacemaker.press) - a web-based writing planning tool
- Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal formatting
- Created for writers, by writers

---

Happy writing!

For questions, issues, or suggestions, please open an issue on the repository.
