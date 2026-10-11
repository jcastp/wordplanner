# wordplanner - Word Count Planner

A comprehensive writing planning tool inspired by [pacemaker.press](https://pacemaker.press) that helps writers calculate, visualize, and manage their writing goals through an interactive console interface.

## Overview

Writing requires managing three key variables:
- **Total words** - Your total word count goal (e.g., 50,000 words for NaNoWriMo)
- **Daily words** - How many words you can write per day (e.g., 1,667 words/day)
- **Time (days)** - How long you have to write (e.g., 30 days)

Given any two variables, **wordplanner** calculates the third and provides:
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
  - Streak tracking indicator
- **Automatic Plan Adjustments** - Stay on track with smart recalculation
  - When ahead: reduce daily goals OR finish early (you choose)
  - When behind: increase daily goals OR extend deadline (you choose)
  - Prompted automatically after updating progress
  - Calculate remaining words and days
- **Progress Persistence** - All progress saved automatically
  - Automatic save prompts when progress updated
  - Progress stored in plan file
  - Loads with plan on app restart

#### Progress Graphs & Analytics
- **Visual Progress Tracking** - See your writing journey through graphs
  - Cumulative line graph: Expected vs actual word count over time
  - Daily bar chart: Compare daily words written vs planned goals
  - Velocity graph: Track writing speed with 3-day moving average
  - Milestone progress chart: Visual progress toward 25%, 50%, 75%, 100%
- **Comprehensive Statistics** - Detailed analytics about your writing
  - Average words per day (actual vs planned)
  - Best and worst writing days with counts
  - Current streak and longest streak tracking
  - Schedule status: ahead, on track, or behind
  - Estimated completion date based on velocity
  - Days ahead or behind schedule
- **Terminal-Based Visualization** - Beautiful graphs in your terminal
  - Powered by plotext for clean, readable charts
  - No external tools needed
  - View individual graphs or all at once
  - Interactive analytics menu

#### Weekend-Specific Planning
- **Weekend Modes** - Configure how weekends are handled
  - Same as weekdays: Write the same daily goal every day
  - Different goal: Set specific word count for weekends (higher for extra time, or lower for rest)
  - Weekends as spare days: No writing on weekends (0 words)
- **Customizable Weekend Days** - Define which days are weekends
  - Default: Saturday and Sunday
  - Custom: Any combination of days (e.g., Friday-Saturday for different work schedules)
- **Weekend Quick Actions** - Fast spare day management
  - Mark all Saturdays as spare
  - Mark all Sundays as spare
  - Mark all weekends as spare
  - Integrated into spare days menu

#### Individual Day Customization
- **Custom Daily Goals** - Override goals for specific dates
  - Set custom word count for any individual day
  - Perfect for special events, busy days, or extra writing time
  - Overrides pattern-based goals and weekend settings
  - View all customized days at a glance
- **Flexible Management** - Easy to adjust
  - Add custom goals for specific dates
  - Remove custom goals (revert to pattern/weekend settings)
  - Clear all custom goals at once

#### Plan Templates
- **Pre-configured Templates** - Start writing faster with ready-made plans
  - NaNoWriMo: 50,000 words in 30 days (1,667 words/day)
  - Short Story: 5,000 words in 7 days
  - Novel Draft: 80,000 words in 60 days
  - Blog Post: 1,500 words in 1 day
  - Academic Paper: 10,000 words in 14 days
  - Novella: 30,000 words in 30 days
  - Screenplay: 25,000 words in 45 days
  - Weekly Goal: 7,000 words in 7 days
  - Daily Sprint (1K): 30,000 words at 1,000/day
  - Daily Habit (500): 15,000 words at 500/day
- **Template Customization** - Adapt templates to your needs
  - Modify word count, duration, or daily goals
  - Choose start date
  - Apply suggested writing patterns
  - Configure suggested weekend modes
  - Save customized templates for reuse
- **Smart Suggestions** - Templates include recommended settings
  - Suggested writing patterns for optimal pacing
  - Recommended weekend configurations
  - Intensity recommendations

#### Flexible Plan Management
- Save & Load Plans - Save multiple writing projects with custom names
- Modify Plans - Change any value and automatically recalculate
  - Adjust total words, daily goals, or time
  - Choose which variable to recalculate
  - Modify multiple values at once
  - Change writing pattern
  - Change start date
  - Configure weekend settings
  - Edit individual day goals
  - Rename the plan
- Plan Actions Menu - Streamlined workflow for managing plans
  - Update progress
  - View progress summary
  - View progress graphs & analytics
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
- **Organized storage** - All exports saved to ~/.wordplanner/exports/

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
  - **Running total** on each day up to today - words written so far against the total, and the completion percentage (e.g. `2,100/80,000` and `2.62%`); pre-existing words count, and wide totals are shortened (`102.0k/150k`)
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
- Positive number validation - Ensures all values are valid and rejects negatives
- Flexible date formats - Multiple ways to input dates
- Enhanced error handling with comprehensive validation:
  - Division by zero protection in all calculations
  - Negative number rejection with clear error messages
  - Corrupted JSON file recovery
  - File I/O error handling (permissions, missing files, empty files)
  - Invalid data validation with helpful feedback
  - Graceful degradation when errors occur

#### Multiple Plans Management
Organize and manage multiple writing projects simultaneously:
- **Plan Organization** - Keep all your projects organized
  - Status management: Active, Archived, Completed
  - 10 predefined categories (novel, blog, academic, screenplay, etc.)
  - Custom tagging system for flexible organization
  - Active plan indicator (★) for quick focus
  - Last modified tracking for all plans
- **Filtering & Sorting** - Find plans quickly
  - Filter by status (active/archived/completed)
  - Filter by category (novel, blog, article, etc.)
  - Filter by custom tags
  - Sort by name, creation date, modification date, completion %, or deadline
  - Search across all plans by name, tags, or category
- **Plan Comparison** - Analyze multiple plans side-by-side
  - Compare word goals, daily goals, and timelines
  - View completion status and progress
  - Summary statistics for compared plans
  - Rich terminal tables with color coding
- **Archive Management** - Keep your workspace clean
  - Archive completed or paused projects
  - Unarchive plans when ready to resume
  - Mark plans as completed for record keeping
  - Archived plans hidden from main views but easily accessible
- **Plan Statistics** - Overall insights across all projects
  - Total word goals and words written
  - Breakdown by status and category
  - Tag usage analysis
  - Average completion tracking
  - Plans with progress reporting
- **Current Plan** - Focus on what matters
  - Make one plan the current plan (★)
  - "Continue the current plan" right from the main menu
  - Only one current plan at a time for focus
  - Current-plan indicator (★) shown in all plan listings
- **Open and delete plans** from the plan manager (deleting asks first and also removes the plan's backup)
- **Changing the save directory** offers to move your existing plans to the new folder

## Installation

### Requirements

- Python 3.13+ (see .python-version file)
- uv package manager (recommended) or pip

### Setup with uv (recommended)

```bash
# Clone the repository
git clone <repository-url>
cd wordplanner

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install rich plotext
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
   Saved to: ~/.wordplanner/plans/
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
            You met your daily goal!

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
   Result: ✓ Exported to ~/.wordplanner/exports/MyPlan_20251028_120000.ics

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
   Result: ✓ Exported to ~/.wordplanner/exports/MyPlan_20251028_120000.csv

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
   Result: ✓ Exported to ~/.wordplanner/exports/MyPlan_20251028_120000.md

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

### Example 7: Weekend Planning for Work-Life Balance

Goal: Write 20,000 words in 30 days with different weekend goals

1. Create Plan with Weekend Configuration
   ```
   Choose: "Create a new plan from scratch"
   Select: "Calculate daily words needed"
   Total words: 20000
   Days available: 30
   Result: 667 words/day average

   "Would you like to configure weekend-specific settings?" → Yes

   Choose weekend mode:
   1. Same as weekdays
   2. Different goal
   3. Weekends as spare days

   Select: "2. Different goal"
   Weekend daily goal: 1000
   Result: Weekends have 1,000 words/day, weekdays have lower goals
   ```

2. Or Mark Weekends as Spare (Weekdays Only Writing)
   ```
   During plan creation:
   "Would you like to configure weekend-specific settings?" → Yes
   Select: "3. Weekends as spare days"
   Result: All Saturdays and Sundays automatically marked as spare
          Writing days redistributed across weekdays only
   ```

3. Quick Action: Add All Weekends as Spare (Existing Plan)
   ```
   Choose: "Modify plan" → "Spare days"
   Select: "6. Mark all weekends as spare"
   Result: All future weekend days marked as spare
          Plan duration automatically extends
   ```

4. Customize Specific Weekend Days
   ```
   "Customize which days are considered 'weekend'?" → Yes
   Enter day numbers: 4,5,6
   Result: Friday, Saturday, Sunday set as weekend days
           Perfect for non-traditional work schedules
   ```

### Example 8: Customizing Individual Day Goals

Goal: Adjust specific days for events, deadlines, or special circumstances

1. Set Higher Goal for a Free Day
   ```
   Choose: "Modify plan" → "Edit individual day goals"
   Select: "1. Set custom goal for a specific day"
   Date: 2025-11-15
   Current goal: 1,000 words
   New goal: 2500
   Result: November 15 now has 2,500-word goal
           Other days unchanged
   ```

2. Set Lower Goal for a Busy Day
   ```
   Choose: "Modify plan" → "Edit individual day goals"
   Select: "1. Set custom goal for a specific day"
   Date: 2025-11-20
   Current goal: 1,000 words
   New goal: 300
   Result: November 20 reduced to 300 words
           Perfect for days with other commitments
   ```

3. View All Custom Goals
   ```
   Choose: "Modify plan" → "Edit individual day goals"

   Display shows:
   Current custom goals (3):
     2025-11-10 (Friday): 1,500 words
     2025-11-15 (Wednesday): 2,500 words
     2025-11-20 (Monday): 300 words
   ```

4. Remove Custom Goal (Revert to Default)
   ```
   Select: "2. Remove custom goal"
   Date: 2025-11-15
   Result: Removed custom goal
           Goal reverted to: 1,000 words (pattern-based)
   ```

### Example 9: Quick Start with Templates

Goal: Start a new writing project quickly using pre-configured templates

1. NaNoWriMo Challenge
   ```
   Choose: "Create plan from template"

   Display shows template categories:
   Popular:
     1. NaNoWriMo: 50,000 words in 30 days (1,667 words/day)
        National Novel Writing Month - Write a 50,000 word novel in 30 days
     2. Short Story: 5,000 words in 7 days (714 words/day)
        Complete a short story in one week
     3. Blog Post: 1,500 words in 1 day (1,500 words/day)
        Write a comprehensive blog post

   Select: "1" (NaNoWriMo)

   Template details shown:
     Total words: 50,000
     Duration: 30 days
     Daily goal: 1,667 words/day
     Suggested pattern: flat
     Suggested weekend mode: different

   "Use this template as-is?" → Yes
   Start date: 2025-11-01
   "Apply suggested 'flat' pattern?" → Yes
   "Configure weekend settings as suggested?" → Yes
     Suggested weekend goal: 2,500 words/day
     "Use this weekend goal?" → Yes

   Result: Complete NaNoWriMo plan created in seconds!
   ```

2. Customize a Template
   ```
   Choose: "Create plan from template"
   Select: "3" (Novel Draft)

   "Use this template as-is?" → No

   Customize:
     "Change total word count?" → Yes
       Enter total words: 100000
     "Change duration (days)?" → Yes
       Enter number of days: 90

   Result: 100,000 word novel in 90 days (1,111 words/day)
           Customized from template
   ```

3. Weekly Writing Habit Template
   ```
   Select: "8" (Weekly Writing Goal)

   Template: 7,000 words in 7 days (1,000 words/day)

   "Use this template as-is?" → Yes
   Start date: [Today]
   "Apply suggested 'flat' pattern?" → Yes

   Result: Consistent daily writing habit
           Perfect for maintaining momentum
   ```

4. Academic Writing Template
   ```
   Select: "5" (Academic Paper)

   Template: 10,000 words in 14 days
   Suggested weekend mode: spare (focus on weekdays)

   "Configure weekend settings as suggested?" → Yes

   Result: Academic paper plan
           No weekend work (weekdays only: 1,429 words/day)
   ```

### Example 10: Managing Multiple Writing Projects

Goal: Organize and track multiple writing projects simultaneously

1. View All Plans Overview
   ```
   Choose: "Manage multiple plans" → "View all plans overview"

   Display shows:
   My Writing Plans
   ================
   Total Plans: 5
   Active: 3 | Archived: 1 | Completed: 1

   ★ Current plan: Novel Draft 2

   Active Plans (3):
   ★ • Novel Draft 2
      50,000 words | [novel] | Tags: fiction, urgent
      Progress: 45% complete, ✓ on track

     • Blog Series
      10,000 words | [blog] | Tags: tech, tutorial
      Progress: 80% complete, ✓ ahead

     • Short Story Collection
      15,000 words | [short-story] | Tags: fiction
      Progress: 10% complete, ⚠ behind
   ```

2. Filter by Category
   ```
   Choose: "Filter and sort plans" → "Filter by category"
   Select: "novel"

   Result: Shows only novel projects
           Perfect for focusing on long-form work
   ```

3. Set the Current Plan
   ```
   Choose: "Set the current plan (★)"
   Select: "Blog Series"

   Result: ★ Blog Series is the current plan
           The main menu now offers "Continue the current plan: ★ Blog Series"
   ```

4. Add Tags to a Plan
   ```
   Choose: "Manage plan categories and tags" → "Add tags to plan"
   Select: "Novel Draft 2"
   Enter tags: deadline, priority-high

   Result: ✓ Tags added
           Easy to filter by deadline or priority later
   ```

5. Compare Multiple Plans
   ```
   Choose: "Compare plans"
   Select plans: 1,2,3

   Display shows comparison table:
   ┌─────────────┬───────────┬───────────┬──────────────┐
   │ Metric      │ Novel     │ Blog      │ Short Story  │
   ├─────────────┼───────────┼───────────┼──────────────┤
   │ Total Words │ 50,000    │ 10,000    │ 15,000       │
   │ Daily Goal  │ 1,000     │ 500       │ 750          │
   │ Days        │ 50        │ 20        │ 20           │
   │ Completion  │ 45%       │ 80%       │ 10%          │
   │ Status      │ on_track  │ ahead     │ behind       │
   └─────────────┴───────────┴───────────┴──────────────┘

   Summary: 3 plans, 75,000 total words
   ```

6. Archive Completed Plan
   ```
   Choose: "Archive/Unarchive plans" → "Mark plan as completed"
   Select: "Blog Series"

   Result: ✓ Blog Series marked as completed!
           Moved to completed section
           Active flag automatically cleared
   ```

7. View Statistics Dashboard
   ```
   Choose: "View plan statistics"

   Display shows:
   Overall Statistics:
   Total Plans: 5
     • Active: 2
     • Archived: 1
     • Completed: 2

   Writing Goals:
     • Total word goal: 150,000 words
     • Total words written: 67,500 words
     • Plans with progress: 4
     • Avg completion (active): 27.5%

   Categories in use:
     • novel: 2 plans
     • blog: 2 plans
     • short-story: 1 plan

   Tags in use (8):
     deadline, fiction, priority-high, tech, tutorial, urgent
   ```

8. Search for Plans
   ```
   Choose: "Search plans"
   Enter query: "fiction"

   Result: Found 3 plans with 'fiction'
           • Novel Draft 2 [novel]
           • Novel Draft 1 (Archived) [novel]
           • Short Story Collection [short-story]
   ```

### Example 11: Analyzing Your Writing Progress with Graphs

Goal: Visualize your progress and analyze your writing patterns

1. View Statistics Summary
   ```
   Choose: "Plan Actions" → "View progress graphs & analytics"
   Select: "View statistics summary"

   Display shows:
     Total Words Written: 8,450
     Total Goal: 10,000
     Remaining: 1,550
     Completion: 84.5%

     Days with Progress: 12
     Average per Day: 704 words
     Planned Daily Goal: 1,000 words
     Best Day: Mon Oct 21: 1,250 words
     Worst Day: Wed Oct 23: 350 words

     Current Streak: 5 days
     Longest Streak: 7 days

     Schedule Status: BEHIND by 1.2 days
     Estimated Completion: 2025-11-02 (5 days)
   ```

2. View Cumulative Progress Graph
   ```
   Select: "Cumulative progress (Expected vs Actual)"

   Display shows line graph with:
   - Blue line: Expected cumulative word count
   - Orange line: Actual cumulative word count
   - X-axis: Dates
   - Y-axis: Total words

   Insight: You can see exactly where you fell behind and when you caught up
   ```

3. View Daily Progress Bar Chart
   ```
   Select: "Daily progress bar chart"

   Display shows bar chart with:
   - Side-by-side bars for each day (last 30 days)
   - Planned words vs Actual words
   - Easy to spot high and low performance days

   Insight: Identify patterns like strong weekdays vs weak weekends
   ```

4. View Writing Velocity
   ```
   Select: "Writing velocity over time"

   Display shows line graph with:
   - Velocity line: 3-day moving average of words per day
   - Target line: Your planned daily goal
   - Shows if your pace is improving or declining

   Insight: See if you're speeding up or slowing down over time
   ```

5. View Milestone Progress
   ```
   Select: "Milestone progress chart"

   Display shows horizontal bars for:
   - 25% milestone: Completed
   - 50% milestone: Completed
   - 75% milestone: Completed
   - 100% milestone: In progress (84.5%)

   Insight: Visual celebration of your progress milestones
   ```

6. View All Graphs at Once
   ```
   Select: "View all graphs"

   Result: Statistics table followed by all four graphs displayed sequentially
   Perfect for a comprehensive progress review session
   ```

## Development

### Running Tests

The project includes a test suite of 848 tests covering the planning logic, storage, exports, analytics and the interactive screens (driven with scripted answers). Tests never touch your real `~/.wordplanner`: every test saves into a temporary directory.

#### Prerequisites

The test tools (pytest, pytest-cov, pytest-mock, freezegun, faker) are in the `test` extra, and uv installs them by default:

```bash
# Using uv (recommended): `uv sync` installs them, `uv run` keeps them installed
uv sync

# Or using pip
pip install -e ".[test]"
```

#### Running Tests

```bash
# Run all tests
uv run pytest

# Run all tests with coverage (fails under 80%, see .coveragerc)
uv run pytest --cov

# Same, plus an HTML report in htmlcov/
uv run pytest --cov --cov-report=html

# Run a specific file, or a single test
uv run pytest tests/test_plan.py
uv run pytest tests/test_plan.py::TestClass::test_name

# Run only failed tests from last run
uv run pytest --lf

# Run tests matching a pattern (e.g., all pattern-related tests)
uv run pytest -k "pattern"
```

#### Test Coverage

Coverage is opt-in (`--cov`), so running one file or one test never fails on the threshold. A full run with `--cov` must reach 80%; it is currently about 88%, with the planning model (`plan.py`) at 94% and every screen module at 76% or more.

#### Test Organization

```
tests/
├── conftest.py                # Pytest fixtures and test configuration
├── test_plan.py               # Plan class tests (65 tests)
├── test_storage.py            # Save/load tests (12 tests)
├── test_edge_cases.py         # Edge case tests (30 tests)
├── test_ui_utils.py           # UI utilities tests (22 tests)
├── test_error_handling.py     # Error handling tests (28 tests)
└── test_multiple_plans.py     # Multiple plans tests (35+ tests)
```

Additional test scripts:
- `test_error_handling.py` - Standalone error handling test suite
- `test_multiple_plans.py` - Standalone multiple plans test suite

## File Structure

```
wordplanner/
├── planea.py                     # Entry point: main menu, Ctrl+C / end-of-input handling
├── ui_create.py                  # Creating plans (from scratch, from templates)
├── ui_plan_actions.py            # Plan actions menu, results, calendar, leaving a plan
├── ui_modify.py                  # Modify plan, spare days, custom goals, weekends, start date
├── ui_progress.py                # Progress entry, ahead/behind offers, recalculation
├── ui_files.py                   # Save, load and export screens
├── ui_settings.py                # Save directory settings
├── plan.py                       # Core Plan class: schedule, calculations, all plan changes
├── calendar_view.py              # Calendar visualization with Rich
├── plan_storage.py               # Save/load functionality
├── plan_export.py                # Export functionality (CSV, iCal, Markdown)
├── progress_analytics.py         # Progress graphs and analytics
├── plan_templates.py             # Pre-configured plan templates
├── plan_manager.py               # Multiple plans management functions
├── plan_manager_ui.py            # Multiple plans management UI
├── ui_utils.py                   # UI utilities (validation, menus, messages)
├── pattern_utils.py              # Pattern configuration utilities
├── user_preferences.py           # User preferences and settings
├── file_utils.py                 # Atomic file writes with backups
├── config.py                     # Application configuration constants
├── tests/                        # Test suite (101+ tests)
│   ├── conftest.py               # Pytest fixtures
│   ├── test_plan.py              # Plan class tests (65 tests)
│   ├── test_storage.py           # Storage tests (12 tests)
│   ├── test_edge_cases.py        # Edge case tests (30 tests)
│   ├── test_ui_utils.py          # UI utilities tests (22 tests)
│   ├── test_error_handling.py    # Error handling tests (28 tests)
│   └── test_multiple_plans.py    # Multiple plans tests (35+ tests)
├── README.md                     # This file - user documentation
├── TEST_RESULTS.md               # Test suite results and coverage analysis
├── CLAUDE.md                     # Developer documentation for AI
├── ERROR_HANDLING_IMPROVEMENTS.md      # Error handling documentation
├── MULTIPLE_PLANS_MANAGEMENT.md        # Multiple plans feature documentation
├── IMPLEMENTATION_SUMMARY.md           # Implementation summary
├── future-improvements.md        # Roadmap and planned features
├── TESTING_PLAN.md               # Testing strategy
├── bugs.md                       # Known bugs tracking
├── pyproject.toml                # Project dependencies
├── pytest.ini                    # Pytest configuration
├── .coveragerc                   # Code coverage configuration
└── .python-version               # Python version (3.13+)
```

## Storage

Plans are automatically saved to:
```
~/.wordplanner/plans/
```

Each plan is stored as a JSON file with format:
```
PlanName_YYYYMMDD_HHMMSS.json
```

Exported files are saved to:
```
~/.wordplanner/exports/
```

Exports are named with the plan name and timestamp in the appropriate format:
- CSV: `PlanName_YYYYMMDD_HHMMSS.csv`
- iCal: `PlanName_YYYYMMDD_HHMMSS.ics`
- Markdown: `PlanName_YYYYMMDD_HHMMSS.md`

## What's New

### Version 1.7 (Latest)
- **Multiple Plans Management** - Organize multiple writing projects:
  - Plan organization by status (active, archived, completed)
  - 10 predefined categories (novel, blog, academic, screenplay, etc.)
  - Custom tagging system for flexible organization
  - Active plan indicator (★) to focus on current project
  - Filtering by status, category, or tags
  - Sorting by name, date, completion %, or deadline
  - Side-by-side plan comparison with summary statistics
  - Search functionality across all plans
  - Archive/unarchive operations with automatic flag management
  - Plan statistics dashboard with overall insights
  - Full backward compatibility with old plan files
  - 23 management functions + 23 UI functions
  - Comprehensive test suite with 35+ passing tests
- **Better Error Handling** - Robust validation and error recovery:
  - Division by zero protection in all calculations
  - Negative number rejection with helpful error messages
  - Corrupted JSON file recovery
  - File I/O error handling (permissions, missing files, empty files)
  - Invalid data validation with context-aware errors
  - Empty input handling across all fields
  - KeyboardInterrupt (Ctrl+C) handling
  - Graceful degradation when errors occur
  - 28 error handling tests, all passing
- **Enhanced Input Validation** - Better user experience:
  - Explicit negative number checking
  - Empty input validation
  - Max value limits where appropriate
  - Clear, specific error messages
  - Shows invalid value in error message
  - Optional `allow_negative` parameter where needed

### Version 1.6
- **Weekend-Specific Planning** - Flexible weekend configuration:
  - Three weekend modes: same as weekdays, different goal, or spare days
  - Set custom word counts for weekends (higher or lower than weekdays)
  - Automatically mark all weekends as spare days
  - Customizable weekend days definition (not just Sat-Sun)
  - Integrated into plan creation workflow
- **Weekend Quick Actions** - Fast spare day management:
  - Mark all Saturdays as spare
  - Mark all Sundays as spare
  - Mark all weekends as spare
  - Added to spare days menu for quick access
- **Individual Day Customization** - Per-day goal overrides:
  - Set custom word goals for any specific date
  - Override pattern-based and weekend settings for individual days
  - Perfect for busy days, extra writing time, or special events
  - View all customized days at a glance
  - Remove custom goals to revert to default
  - Clear all custom goals at once
- **Plan Templates** - Quick start with pre-configured templates:
  - 10 ready-to-use templates for common writing goals
  - Popular templates: NaNoWriMo, Short Story, Blog Post
  - Long form: Novel Draft, Novella, Screenplay
  - Academic: Research Paper or Thesis Chapter
  - Habits: Weekly Goal, 1K Daily Sprint, 500 Daily Habit
  - Templates organized by category for easy browsing
  - Each template includes suggested patterns and weekend modes
  - Full customization available (modify any template before creating)
  - Instant plan creation or customize to your needs
- **Enhanced Plan Display** - Better visibility:
  - Weekend settings shown in plan summary
  - Custom day goals count displayed
  - Weekend goal information in results
- **Updated Modify Menu** - New configuration options:
  - Option 8: Configure weekend settings
  - Option 9: Edit individual day goals
  - Easy access to all customization features

### Version 1.5
- **Progress Graphs & Analytics** - Visual progress tracking and comprehensive statistics:
  - Cumulative line graph showing expected vs actual word count over time
  - Daily bar chart comparing words written vs planned goals
  - Velocity graph tracking writing speed with 3-day moving average
  - Milestone progress chart for 25%, 50%, 75%, 100% completion
  - Terminal-based graphs using plotext library
- **Comprehensive Writing Statistics** - Detailed analytics dashboard:
  - Average words per day (actual vs planned)
  - Best and worst writing days identification
  - Current streak and longest streak tracking
  - Schedule status: ahead, on track, or behind
  - Estimated completion date based on current velocity
  - Days ahead or behind schedule calculation
- **Interactive Analytics Menu** - Easy access to all graphs and stats:
  - View individual graphs or all at once
  - Statistics summary table
  - Integrated into Plan Actions menu
  - No external tools required

### Version 1.4
- **Export Functionality** - Share plans in multiple formats:
  - CSV export for spreadsheets (Excel, Google Sheets)
  - iCal/ICS export for calendar apps (Google Calendar, Apple Calendar, Outlook)
  - Markdown export for readable documentation
  - Export all formats at once
  - Automatic file naming with timestamps
  - Organized exports directory (~/.wordplanner/exports/)
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

### Recently Completed ✅
- ✅ Plan Templates - Pre-configured plans (NaNoWriMo, Short Story, etc.) [v1.6]
- ✅ Multiple Plans Management - Organize and manage multiple projects [v1.7]
- ✅ Better Error Handling - Comprehensive validation and recovery [v1.7]
- ✅ Enhanced Input Validation - Clear error messages and better UX [v1.7]

### Next Up (High Priority)
- Holiday Templates - Quick marking of common holidays
- Writing Session Timer - Integrated pomodoro-style timer
- Comprehensive testing suite expansion
- Web interface prototype

### Coming Soon (Medium Priority)
- Notifications and reminders
- Advanced calendar features
- Plan groups/folders for hierarchical organization
- Bulk operations (multi-select plans)

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
6. Organize with categories and tags - Use the category system for project types and tags for flexible organization
7. Set one active plan - Focus on your current priority by marking it as active (★)
8. Archive completed work - Keep your workspace clean by archiving finished or paused projects
9. Compare plans regularly - Use plan comparison to track progress across multiple projects
10. Use the search function - Quickly find plans by name, tag, or category

### Multiple Plans Management Tips

1. **Use categories consistently** - Assign appropriate categories (novel, blog, academic, etc.) to all plans
2. **Tag strategically** - Use a consistent set of tags like "urgent", "client-work", "deadline", "fiction"
3. **Set one active plan** - Mark your main focus project as active for quick access
4. **Archive regularly** - Move completed or paused projects to archived status
5. **Search before creating** - Use search to check if a similar plan already exists
6. **Compare for insights** - Use plan comparison to identify patterns and adjust strategies
7. **Review statistics** - Check the statistics dashboard weekly for overall progress tracking

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

Q: Can I see graphs of my writing progress?
A: Yes! Use "View progress graphs & analytics" from the Plan Actions menu. You'll get four types of graphs: cumulative progress (expected vs actual), daily bar chart, writing velocity over time, and milestone progress. Plus comprehensive statistics including average words per day, best/worst days, streaks, and estimated completion date.

Q: Can I set different writing goals for weekends?
A: Yes! During plan creation, you can configure weekend-specific settings with three modes: (1) Same as weekdays - write the same amount every day, (2) Different goal - set a specific word count for weekends (higher for extra time or lower for rest), or (3) Weekends as spare days - no writing on weekends. You can also customize which days count as "weekend" for non-traditional schedules.

Q: How do I mark all weekends as spare days quickly?
A: Use the weekend quick actions in the spare days menu. Choose "Modify plan" then "Spare days" and select option 4, 5, or 6 to mark all Saturdays, all Sundays, or all weekends as spare days automatically. You can also configure weekends as spare during plan creation for a cleaner workflow.

Q: Can I customize the word goal for a specific day?
A: Yes! Use "Modify plan" then "Edit individual day goals" to set custom word counts for any specific date. This is perfect for busy days (set lower goal), extra writing time (set higher goal), or special events. Custom goals override pattern-based goals and weekend settings. You can view all customized days, remove individual customizations, or clear all at once.

Q: Is there a quick way to start a new plan without entering all the details?
A: Yes! Use "Create plan from template" from the main menu. Choose from 10 pre-configured templates including NaNoWriMo (50,000 words in 30 days), Short Story (5,000 words in 7 days), Novel Draft (80,000 words in 60 days), Academic Paper, and more. Each template includes suggested patterns and weekend modes. You can use templates as-is or customize them before creating your plan.

Q: Can I export my plan to Google Calendar or other calendar apps?
A: Yes! Use the "Export plan" option and choose iCal/ICS format. The exported .ics file can be imported into Google Calendar, Apple Calendar, Outlook, and most other calendar applications. You'll get daily events with your word goals and spare days marked.

Q: Can I export my plan to Excel or Google Sheets?
A: Yes! Use the "Export plan" option and choose CSV format. The exported CSV file can be opened in Excel, Google Sheets, or any spreadsheet application. It includes day-by-day data with your goals, actual progress, cumulative totals, and status indicators.

Q: What export formats are available?
A: Three formats: CSV (for spreadsheets), iCal/ICS (for calendar apps), and Markdown (for readable documentation). You can export to a single format or all three at once. All exports are saved to ~/.wordplanner/exports/

Q: Where are my plans stored?
A: In ~/.wordplanner/plans/ as JSON files.

Q: Can I manage multiple writing projects at once?
A: Yes! Use "Manage multiple plans" from the main menu. You can organize plans by status (active, archived, completed), assign categories (novel, blog, academic, etc.), add custom tags, filter and sort plans, compare plans side-by-side, and view statistics across all your projects. The active plan feature (★) helps you focus on your current project.

Q: How do I organize my plans by project type?
A: Use the category system! Each plan can be assigned one of 10 categories: novel, short-story, novella, blog, article, academic, screenplay, poetry, non-fiction, or other. Filter by category to see only specific types of projects. You can also use custom tags for more flexible organization like "urgent", "client-work", or "hobby".

Q: What happens if I have too many plans?
A: Archive completed or paused plans to keep your workspace clean. Archived plans are hidden from main views but remain easily accessible. You can also mark plans as completed for record keeping. Use the search function to quickly find any plan by name, tag, or category.

Q: Can I compare multiple plans to see which is ahead of schedule?
A: Yes! Use "Compare plans" to view multiple plans side-by-side in a rich table format. You'll see word goals, daily goals, completion percentages, on-track status, and summary statistics. Perfect for managing deadlines across multiple projects.

Q: What does the ★ symbol mean next to plan names?
A: That's the active plan indicator! You can set one plan as your "currently active" project for quick focus. Only one plan can be active at a time. Use "Set active plan" from the Manage multiple plans menu.

Q: Can I share my plan with others?
A: You can share the JSON file manually, or export to CSV/Markdown for easier sharing. Cloud sync is on the long-term roadmap.

Q: What happens if I enter invalid data or negative numbers?
A: The app now has comprehensive error handling that validates all inputs. Negative numbers are rejected with clear messages, division by zero is prevented, and corrupted files are handled gracefully. If you encounter an error, you'll get a helpful message explaining what went wrong and how to fix it.

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
