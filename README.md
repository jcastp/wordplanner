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

#### Writing Patterns (Variable Daily Goals)
Distribute your writing goals with different patterns to match your energy and schedule:
- **Flat/Steady** - Same daily goal every day (default)
- **Valley** - Start high, ease in middle, finish high (momentum approach)
- **Mountain** - Start easy, peak in middle, ease at end (warm-up/cool-down)
- **Rising** - Gradually increase goals over time (building momentum)
- **Declining** - Gradually decrease goals over time (front-loaded effort)
- **Random** - Varied daily goals within a range (flexible approach)
- Configurable intensity - Choose mild, moderate, or extreme variation
- Pattern preview - See your plan visualized before committing
- Change anytime - Modify pattern after plan creation

#### Progress Tracking & Recalculation
- **Track Your Progress** - Record actual words written each day
  - Quick entry for today
  - Enter/edit progress for any past date
  - View all progress entries
  - Progress dashboard with stats
  - Streak tracking with 🔥 indicator
- **Automatic Plan Adjustments** - Stay on track with smart recalculation
  - When ahead: reduce daily goals OR finish early (you choose)
  - When behind: increase daily goals OR extend deadline (you choose)
  - Prompted automatically after updating progress
  - Calculate remaining words and days
- **Progress Persistence** - All progress saved automatically
  - Automatic save prompts when progress updated
  - Progress stored in plan file
  - Loads with plan on app restart

#### Flexible Plan Management
- Save & Load Plans - Save multiple writing projects with custom names
- Modify Plans - Change any value and automatically recalculate
  - Adjust total words, daily goals, or time
  - Choose which variable to recalculate
  - Modify multiple values at once
  - Change writing pattern
  - Change start date
- Plan Actions Menu - Streamlined workflow for managing plans
  - Update progress
  - View progress summary
  - Modify plan values
  - View calendar visualizations
  - Export plan
  - Save changes

#### Export Functionality
Share and use your plans in other applications:
- **CSV Export** - Spreadsheet format for data analysis
  - Day-by-day breakdown with dates and goals
  - Progress tracking columns (actual vs goal)
  - Cumulative word counts
  - Status indicators (Exceeded, Met, Partial, Missed, Future)
  - Spare days clearly marked
  - Import into Excel, Google Sheets, etc.
- **iCal/ICS Export** - Calendar format for scheduling apps
  - Daily events with word goals
  - Spare days as transparent events
  - Compatible with Google Calendar, Apple Calendar, Outlook
  - Reminders and notifications (app-dependent)
  - Full calendar integration
- **Markdown Export** - Readable text format
  - Complete plan overview
  - Progress summary with stats
  - Daily schedule grouped by week
  - Milestones table (25%, 50%, 75%, 100%)
  - Perfect for sharing or documentation
- **Export All** - Generate all three formats at once
- **Automatic naming** - Files named with plan name and timestamp
- **Organized storage** - All exports saved to ~/.planeapalabras/exports/

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
  - Daily word goals clearly displayed (pattern-aware)
  - **Progress indicators** with color coding:
    - ✓ Green - Goal met or exceeded
    - ~ Yellow - Partial progress
    - ✗ Red - Missed day
    - Blue - Future days
  - Spare days marked in orange
  - Weekend highlighting
  - Week numbers
- Weekly summary - Week-by-week breakdown showing:
  - Date ranges for each week
  - Writing days vs spare days per week
  - Daily goal ranges for variable patterns
  - Weekly word totals
  - Cumulative progress
- Milestone tracking - Key progress points at 25%, 50%, 75%, 100%
- Progress summary in calendar header - Shows completion % and on-track status
- Start date set during plan creation - No prompts when viewing calendar

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

### Example 3: Using Writing Patterns

Goal: Write 30,000 words in 30 days with a Mountain pattern (warm-up/cool-down)

1. Create Plan with Pattern
   ```
   Choose: "Calculate daily words needed"
   Total words: 30000
   Days available: 30
   Result: 1,000 words/day average

   "Would you like to use a variable writing pattern?" → Yes
   Select: "Mountain - Start easy, peak in middle, ease at end"
   Intensity: Moderate (default)
   Result: Daily goals range from ~580 to ~1,860 words
   ```

2. View Pattern in Calendar
   ```
   Choose: "View calendar" → "Both views"
   See: Each day shows its specific goal
        Week 1: 580-870 words/day (easy start)
        Week 2: 1,100-1,490 words/day (ramping up)
        Weeks 3-4: 1,600-1,860 words/day (peak performance)
        Week 5: 870-580 words/day (cool down)
   ```

3. Change Pattern Later
   ```
   Choose: "Modify plan" → "Writing pattern"
   Switch to: "Rising" pattern
   Result: Goals now increase from 600 to 1,400 words/day
   Calendar automatically updates to show new daily goals
   ```

### Example 4: Tracking Progress and Adjusting Your Plan

Goal: Track daily writing progress and adjust plan if behind schedule

1. Update Today's Progress
   ```
   Choose: "Update progress" → "Quick entry (today's words)"
   Enter: 1,200 words
   Result: ✓ Progress recorded: 1,200 words
           🎉 You met your daily goal!

   Status: ✓ ON TRACK
   ```

2. Enter Missed Day from Yesterday
   ```
   Choose: "Update progress" → "Enter for a specific date"
   Date: 2025-10-27
   Enter: 600 words
   Result: ✓ Progress recorded: 600 words
           (400 words short of goal)

   Status: ⚠ BEHIND by 400 words
   ```

3. Adjust Plan (Behind Schedule)
   ```
   Prompt: "Would you like to adjust your plan? [Y/n]"
   Choose: "Increase daily goals (keep end date)"

   Proposed adjustment:
     Current daily goal: 1,000 words/day
     New daily goal: 1,057 words/day
     Remaining days: 7

   Apply? Yes
   Result: ✓ Plan adjusted!
   ```

4. View Progress Summary
   ```
   Choose: "View progress summary"

   Overall Progress:
     Total goal: 10,000 words
     Written: 3,400 words (34.0%)
     Remaining: 6,600 words
     Days recorded: 5
     Current streak: 3 days 🔥

   Schedule Status:
     ✓ ON TRACK after adjustment
   ```

5. Save Progress
   ```
   Exit progress menu
   Prompt: "Progress was updated. Save the plan? [Y/n]"
   Press: Y
   Result: ✓ Plan saved successfully
   ```

### Example 5: Loading and Modifying an Existing Plan

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

### Example 6: Exporting Your Plan

Goal: Share your writing plan with others or import it into calendar/spreadsheet apps

1. Export to Calendar App
   ```
   Choose: "Plan Actions" → "Export plan"
   Select: "iCal/ICS (for calendar apps)"
   Result: ✓ Exported to ~/.planeapalabras/exports/MyPlan_20251028_120000.ics

   Import the .ics file into:
   - Google Calendar (Settings → Import & Export)
   - Apple Calendar (File → Import)
   - Outlook (File → Open & Export → Import/Export)

   You'll see daily events with your word goals!
   ```

2. Export to Spreadsheet
   ```
   Choose: "Plan Actions" → "Export plan"
   Select: "CSV (for spreadsheets)"
   Result: ✓ Exported to ~/.planeapalabras/exports/MyPlan_20251028_120000.csv

   Open in Excel or Google Sheets to see:
   - Date, Day of Week, Day Number
   - Daily Goals and Actual Words
   - Cumulative Totals
   - Status (Exceeded, Met, Partial, Missed, Future)
   - Spare days marked

   Perfect for tracking and analysis!
   ```

3. Export to Markdown for Documentation
   ```
   Choose: "Plan Actions" → "Export plan"
   Select: "Markdown (readable text)"
   Result: ✓ Exported to ~/.planeapalabras/exports/MyPlan_20251028_120000.md

   Use for:
   - Sharing with writing partners
   - Posting on writing forums
   - Documentation/records
   - GitHub README files

   Includes overview, progress, daily schedule, and milestones!
   ```

4. Export All Formats at Once
   ```
   Choose: "Plan Actions" → "Export plan"
   Select: "All formats"
   Result: ✓ Exported 3 files:
           - MyPlan_20251028_120000.csv
           - MyPlan_20251028_120000.ics
           - MyPlan_20251028_120000.md

   All files ready for different purposes!
   ```

## File Structure

```
planeapalabras/
├── planea.py                  # Console interface
├── plan.py                    # Core Plan class with calculations
├── calendar_view.py           # Calendar visualization with Rich
├── plan_storage.py            # Save/load functionality
├── plan_export.py             # Export functionality (CSV, iCal, Markdown)
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

Exported files are saved to:
```
~/.planeapalabras/exports/
```

Exports are named with the plan name and timestamp in the appropriate format:
- CSV: `PlanName_YYYYMMDD_HHMMSS.csv`
- iCal: `PlanName_YYYYMMDD_HHMMSS.ics`
- Markdown: `PlanName_YYYYMMDD_HHMMSS.md`

## What's New

### Version 1.4 (Latest)
- **Export Functionality** - Share plans in multiple formats:
  - CSV export for spreadsheets (Excel, Google Sheets)
  - iCal/ICS export for calendar apps (Google Calendar, Apple Calendar, Outlook)
  - Markdown export for readable documentation
  - Export all formats at once
  - Automatic file naming with timestamps
  - Organized exports directory (~/.planeapalabras/exports/)
- **Progress in Exports** - CSV and Markdown exports include:
  - Actual word counts vs goals
  - Status indicators (Exceeded, Met, Partial, Missed, Future)
  - Cumulative progress tracking
- **Spare Days in Exports** - All formats properly handle spare days:
  - CSV marks spare days with "Spare" type
  - iCal creates transparent events for spare days
  - Markdown shows spare days in daily schedule

### Version 1.3
- **Progress Tracking** - Track actual words written each day:
  - Quick entry for today's words
  - Enter progress for any past date (edit/update anytime)
  - View all progress entries with status indicators
  - Progress dashboard with completion %, streak tracking
  - Automatic save prompts when progress is updated
  - Progress persists across app restarts
- **Plan Recalculation** - Adjust plans based on actual progress:
  - When ahead: reduce daily goals OR finish early
  - When behind: increase daily goals OR extend deadline
  - User chooses adjustment strategy each time
  - Smart prompts after updating progress
- **Calendar Progress Indicators** - Visual progress in calendar views:
  - Green checkmark (✓) - Goal met
  - Bold green with count - Goal exceeded
  - Yellow (~) with count - Partial progress
  - Red (✗) - Missed day
  - Blue - Future days
- **Start Date Management** - Set start date during plan creation
  - Calendar views use saved date automatically
  - Modify start date via "Modify plan" menu only
  - No more date prompts when viewing calendars

### Version 1.2
- **Writing Patterns** - Variable daily goals with 6 pattern types:
  - Flat (steady), Valley, Mountain, Rising, Declining, Random
  - Configurable intensity levels (mild, moderate, extreme)
  - Pattern-aware calendar views showing individual daily goals
  - Change patterns anytime via modify plan menu
- Pattern preservation - Save/load maintains pattern settings
- Weekly summary improvements - Shows goal ranges for variable patterns
- Enhanced plan display - Pattern information in summaries

### Version 1.1
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
- Weekend Planning - Different word goals for weekends vs weekdays
- Progress Graphs - Visual comparison of expected vs actual words
- Quick Actions - "Mark all weekends as spare", holiday templates, etc.
- Plan Templates - Pre-configured plans (NaNoWriMo, Short Story, etc.)

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
A: Yes! Use Writing Patterns to create variable daily goals. Choose from flat, valley, mountain, rising, declining, or random patterns when creating or modifying a plan.

Q: Can I track my actual progress?
A: Yes! Use "Update progress" from the Plan Actions menu. You can enter words for today (quick entry) or any past date. Progress is saved automatically and shown in calendar views with color-coded indicators.

Q: What happens if I fall behind schedule?
A: The app will detect when you're behind and offer to adjust your plan. You can either increase daily goals to catch up while keeping the same deadline, or extend your deadline while keeping the same daily goals. You choose!

Q: Can I export my plan to Google Calendar or other calendar apps?
A: Yes! Use the "Export plan" option and choose iCal/ICS format. The exported .ics file can be imported into Google Calendar, Apple Calendar, Outlook, and most other calendar applications. You'll get daily events with your word goals and spare days marked.

Q: Can I export my plan to Excel or Google Sheets?
A: Yes! Use the "Export plan" option and choose CSV format. The exported CSV file can be opened in Excel, Google Sheets, or any spreadsheet application. It includes day-by-day data with your goals, actual progress, cumulative totals, and status indicators.

Q: What export formats are available?
A: Three formats: CSV (for spreadsheets), iCal/ICS (for calendar apps), and Markdown (for readable documentation). You can export to a single format or all three at once. All exports are saved to ~/.planeapalabras/exports/

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
