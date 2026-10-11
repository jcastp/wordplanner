# wordplanner — User Manual

This manual describes everything the planner can do, screen by screen. A single
**running example** goes through it from start to finish: a novel called *The
Lighthouse Keeper*, planned in October 2026 and written in November and December.
The example is set apart in boxes like this:

> 📖 **Running example** — what you type, and what the planner answers.

All screens and numbers in the example are real output from the program. (The
calendars are shown without colors and slightly trimmed.)

---

## Contents

1. [Getting started](#1-getting-started)
2. [Key ideas](#2-key-ideas)
3. [Creating a plan](#3-creating-a-plan)
4. [Creating a plan from a template](#4-creating-a-plan-from-a-template)
5. [The plan actions menu](#5-the-plan-actions-menu)
6. [Changing a plan](#6-changing-a-plan)
7. [Saving and loading](#7-saving-and-loading)
8. [Tracking progress](#8-tracking-progress)
9. [Calendar views](#9-calendar-views)
10. [Graphs and analytics](#10-graphs-and-analytics)
11. [Exports](#11-exports)
12. [Commands without the menus](#12-commands-without-the-menus)
13. [Managing multiple plans](#13-managing-multiple-plans)
14. [Settings](#14-settings)
15. [Files and storage](#15-files-and-storage)
16. [Reference: limits and rules](#16-reference-limits-and-rules)
17. [Troubleshooting](#17-troubleshooting)

---

## 1. Getting started

### Requirements and installation

- Python 3.13 or later
- [uv](https://docs.astral.sh/uv/) (recommended), or pip

```bash
uv sync                          # installs rich, plotext and the test tools
uv run python planea.py          # opens the menus
```

With pip: `pip install -e .` and then `python planea.py`.

### Getting around

Everything is done with numbered menus: type the number and press Enter. `0`
always goes back (or exits from the main menu). Yes/no questions show the default
in capitals: `[Y/n]` means that Enter answers *yes*.

Press **Ctrl+C** at any time to quit. If the open plan has unsaved changes, the
planner offers to save them first (see [Unsaved changes](#unsaved-changes)).

### The main menu

```
==================================================
WORD COUNT PLANNER
==================================================

What would you like to do?

1. Create a new plan from scratch
2. Create plan from template
3. Load an existing plan
4. Manage multiple plans
5. Settings
6. Continue the current plan: ★ The Lighthouse Keeper
0. Exit
```

Option 6 only appears when you have a [current plan (★)](#the-current-plan-).

### Map of the menus

```
Main menu
├── 1 Create a new plan from scratch ──┐
├── 2 Create plan from template ───────┤
├── 3 Load an existing plan ───────────┼──► Plan actions
├── 6 Continue the current plan ───────┘    ├── 1 Update progress
├── 4 Manage multiple plans                 ├── 2 View progress summary
│   ├── overview, filter/sort, search       ├── 3 Graphs & analytics
│   ├── compare, current plan (★)           ├── 4 Modify plan (11 options)
│   ├── categories & tags, archive          ├── 5 View calendar
│   └── statistics, open, delete            ├── 6 Export plan
└── 5 Settings                              └── 7 Save plan
```

---

## 2. Key ideas

A few words have a precise meaning in the planner. Knowing them makes the rest of
the manual easier to follow.

### The three variables

A plan has a **total** (words), a **daily** goal (words per day) and a **time**
(writing days). Give any two and the planner calculates the third. Whenever you
later change one, it asks which of the other two to keep.

### Writing days and calendar days

**Time** counts *writing days*. A **spare day** (a holiday, a busy day) is a
calendar day with no writing that doesn't count as a writing day, so adding one
pushes the end date back by a day, unless you choose to keep the end date. The
plan runs from its **start date** until all its writing days fit.

### Pre-existing words

If you've already written part of the project, enter those words as
**pre-existing words**. They count toward your total and your completion
percentage, but the schedule only plans the words that are left. With a total of
60,000 words and 8,000 already written, the daily goals cover 52,000 words.

### The schedule

Every day of the plan has its own goal. Most days share the words evenly (or by
a [writing pattern](#writing-patterns)), but some days have fixed goals:

|Day                                |Goal                              |
|-----------------------------------|----------------------------------|
|Spare day                          |0                                 |
|Weekend day, weekends off          |0                                 |
|Weekend day, different weekend goal|the weekend goal                  |
|Day with a custom goal             |that goal                         |
|Past day                           |locked (see below)                |
|Any other day                      |a share of the words that are left|

The goals always add up to the words still to write. The **daily goal** shown in
the plan summary is the goal of an ordinary weekday.

### Past days are locked

Days before today can't change: their goals stay as they were, so your history
stays true. You can still log words for past days, but you can't add spare days,
custom goals or other changes before today. Each time you return to the plan
actions menu, the days that have gone by are locked.

### Rest days

A day with a goal of 0 (a spare day, a weekend off, a custom goal of 0) is a
**rest day**. A rest day is never "missed", and it doesn't break your streak.

### Being on track

The planner compares the words you've written since the plan started with the
words the schedule expected **up to yesterday**. The words you write today count
straight away, but today's goal only counts once the day is over. Today with
nothing logged isn't a missed day.

---

## 3. Creating a plan

Main menu → **1. Create a new plan from scratch**.

### Step 1: what do you know?

```
1. I know my goal (total words) and daily capacity
   → Calculate how many days I'll need

2. I know my daily capacity and available time
   → Calculate total words I'll write

3. I know my goal (total words) and available time
   → Calculate daily words I need to write
```

|Option|You type                |Calculated                                     |
|------|------------------------|-----------------------------------------------|
|1     |total words, daily words|writing days (as few whole days as needed)     |
|2     |daily words, days       |total words (daily × days + pre-existing words)|
|3     |total words, days       |daily words                                    |

### Step 2: pre-existing words

You're asked whether you've already written words for this project. Answer *yes*
and type how many. The screen shows what that means for your plan. If the words
already reach the total, the planner congratulates you and doesn't create the plan.

### Step 3: writing pattern

*"Would you like to use a variable writing pattern?"* Answer *no* to keep the
same goal every day (flat), or see [Writing patterns](#writing-patterns). If you
set a default pattern in [Settings](#14-settings), you're offered that one first.

### Step 4: start date

Type a date, or press Enter for today. A date in the past is accepted only after
a warning.

### Step 5: weekends

*"Would you like to configure weekend-specific settings?"* See
[Weekend settings](#weekend-settings). If you set a default weekend setting in
Settings, it's offered first, and the planner then recalculates the value you
didn't type, keeping the two you did.

You then arrive at the [plan actions menu](#5-the-plan-actions-menu). The plan
isn't saved yet.

> 📖 **Running example — creating the plan (October 11, 2026)**
>
> You want to finish *The Lighthouse Keeper*: 60,000 words in total, 8,000 of them
> already written. You can write for 60 days starting on Monday, November 2. You
> know the total and the time, so you choose option 3:
>
> ```
> Enter your choice (0-3): 3
>
> --- Calculate daily words needed ---
> Enter your total word goal: 60000
>
> Have you already written some words? [y/N]: y
>
> How many words have you already written? 8000
>
> ✓ Pre-existing words: 8,000
>   Progress: 13.3% of goal
>   Remaining to write: 52,000 words
>
> Confirm this word count? [Y/n]: y
> Enter how many days you have available: 60
>
> Would you like to use a variable writing pattern? [y/N]: n
> Start date: 2026-11-02
>
> ✓ Plan starts on: 2026-11-02
> ```
>
> 52,000 words over 60 days is 867 words a day. You have more time at weekends,
> so you set a weekend goal of 1,200 words:
>
> ```
> Would you like to configure weekend-specific settings? [y/N]: y
> Enter your choice (0-3): 2
> Weekend daily goal: 1200
>
> ✓ Weekends will have a goal of 1,200 words/day
>
> Customize which days are considered 'weekend'? [y/N]: n
>
> This changes the plan's writing days. How should the plan adjust?
>    Before: ends 2026-12-31, 867 words/day, total 60,000 words
> 1. Move the end date (keep 867 words/day)
>    -> ends 2026-12-26, 850 words/day, total 60,000 words
> 2. Keep the end date (change the daily goal)
>    -> ends 2026-12-31, 745 words/day, total 60,000 words
> 3. Keep the end date and the daily goal (change the total)
>    -> ends 2026-12-31, 867 words/day, total 65,333 words
>
> Enter your choice (1-3): 2
>
> ✓ Plan ends 2026-12-31, 745 words/day, total 60,000 words
> ```
>
> You keep December 31 as the deadline. Writing more at weekends means only 745
> words on weekdays.

---

## 4. Creating a plan from a template

Main menu → **2. Create plan from template**. Templates are ready-made plans for
common projects:

|# |Template            |Words |Duration       |Suggested pattern|Suggested weekends|
|--|--------------------|------|---------------|-----------------|------------------|
|1 |NaNoWriMo           |50,000|30 days        |flat             |different goal    |
|2 |Short Story         |5,000 |7 days         |rising           |different goal    |
|3 |Blog Post           |1,500 |1 day          |flat             |same              |
|4 |Novel Draft         |80,000|60 days        |valley           |same              |
|5 |Novella             |30,000|30 days        |mountain         |different goal    |
|6 |Screenplay          |25,000|45 days        |valley           |same              |
|7 |Academic Paper      |10,000|14 days        |rising           |weekends off      |
|8 |Weekly Writing Goal |7,000 |7 days         |flat             |same              |
|9 |1K Daily Sprint     |30,000|1,000 words/day|flat             |same              |
|10|500 Word Daily Habit|15,000|500 words/day  |flat             |same              |

After picking one:

1. **Use this template as-is?** Answer *no* to change the total, and either the
   duration or the daily goal (the other one is recalculated).
2. **Pre-existing words**, as for a new plan.
3. **Start date**.
4. **Apply the suggested pattern?** If you say yes, you choose its intensity.
5. **Configure weekend settings as suggested?** For "different goal" the planner
   proposes 1.5 × the daily goal for weekends (you can type another), and then
   asks how the plan should adjust (see
   [When a change moves days around](#when-a-change-moves-days-around)).

The new plan takes the template's name. You can rename it later.

---

## 5. The plan actions menu

Every plan you create, load or continue opens here:

```
--------------------------------------------------
YOUR WRITING PLAN
--------------------------------------------------
Total words: 60,000 words
Already written before the plan: 8,000 words
Writing days: 57 days
Daily goal: 843 words per day
Weekend goal: 1,231 words/day (Sat, Sun)
Custom day goals: 1 day(s) customized
Spare days: 3 days (0 words)
Total calendar duration: 60 days
--------------------------------------------------
Progress: 12,950 words written (21.6%)
Remaining: 47,050 words
Status: ✓ AHEAD by 800 words
--------------------------------------------------

==================================================
PLAN ACTIONS
==================================================

1. Update progress
2. View progress summary
3. View progress graphs & analytics
4. Modify plan
5. View calendar
6. Export plan
7. Save plan
0. Go back to main menu
```

The summary at the top shows only what applies: the pre-existing words, weekend,
custom goals and spare days lines appear when the plan has them, and the progress
lines once you've logged words.

|Option                 |Section                                         |
|-----------------------|------------------------------------------------|
|1 Update progress      |[Tracking progress](#8-tracking-progress)       |
|2 View progress summary|[Progress summary](#progress-summary)           |
|3 Graphs & analytics   |[Graphs and analytics](#10-graphs-and-analytics)|
|4 Modify plan          |[Changing a plan](#6-changing-a-plan)           |
|5 View calendar        |[Calendar views](#9-calendar-views)             |
|6 Export plan          |[Exports](#11-exports)                          |
|7 Save plan            |[Saving and loading](#7-saving-and-loading)     |
|0 Go back              |asks first if there are unsaved changes         |

---

## 6. Changing a plan

Plan actions → **4. Modify plan**:

```
1. Total words
2. Daily words
3. Writing days
4. Spare days
5. Writing pattern
6. Start date
7. Modify two values (third will be calculated)
8. Weekend settings
9. Edit individual day goals
10. Recalculate from progress (redistribute remaining words)
11. Plan name
0. Cancel
```

### Total, daily and writing days (options 1–3 and 7)

Change one value and choose which of the other two stays fixed. For example,
**1. Total words** asks you to keep either the daily words (the number of days is
recalculated) or the time (the daily goal is recalculated). Option 7 lets you
type two values and calculates the third.

You can't make the plan shorter than the days that have already gone by (they're
locked).

### When a change moves days around

Adding or removing spare days, changing the weekend settings, or setting a custom
day goal changes how many words the other days need. After such a change, the
planner shows three ways to absorb it, each with a preview of the result, and
applies the one you pick:

|Option                              |What stays                     |What changes  |
|------------------------------------|-------------------------------|--------------|
|Move the end date                   |the daily goal                 |the end date  |
|Keep the end date                   |the end date and the total     |the daily goal|
|Keep the end date and the daily goal|the end date and the daily goal|the total     |

If the change doesn't affect any day's goal, nothing is asked.

### Spare days (option 4)

```
MANAGE SPARE DAYS
Plan period: 2026-11-02 to 2026-12-31
Writing days: 60
Spare days: 0

1. Add spare day(s)
2. Remove spare day(s)
3. Clear all spare days

Quick Actions:
4. Mark all Saturdays as spare
5. Mark all Sundays as spare
6. Mark all weekends as spare
0. Done
```

Dates can be typed in three ways:

|Input                     |Meaning                    |
|--------------------------|---------------------------|
|`2026-12-25`              |one date                   |
|`2026-12-24,2026-12-31`   |several dates              |
|`2026-12-24 to 2026-12-26`|a range, both ends included|

- Dates before today are refused, because past days are locked. *Clear all* only
  clears spare days from today on.
- Dates must fall between the start date and about a year after the plan.
- Spare days outside the plan are kept but ignored, and listed as
  *"(outside the plan, ignored)"*.
- The quick actions mark every Saturday, Sunday or weekend day from today to the
  end of the plan. The end moves later as days are added, so it extends to cover
  them. If you then choose to keep the end date, the days marked after it are
  dropped again.

> 📖 **Running example — Christmas off**
>
> You won't write from December 24 to 26:
>
> ```
> Date(s): 2026-12-24 to 2026-12-26
> ✓ Added 3 spare day(s)
>
> This changes the plan's writing days. How should the plan adjust?
>    Before: ends 2026-12-31, 745 words/day, total 60,000 words
> 1. Move the end date (keep 745 words/day)
>    -> ends 2027-01-03, 735 words/day, total 60,000 words
> 2. Keep the end date (change the daily goal)
>    -> ends 2026-12-31, 810 words/day, total 60,000 words
> 3. Keep the end date and the daily goal (change the total)
>    -> ends 2026-12-31, 745 words/day, total 57,309 words
>
> Enter your choice (1-3): 2
> ```
>
> The deadline stays December 31. The plan now has 57 writing days and 3 spare
> days, and the daily goal is 810.

### Writing patterns (option 5)

A pattern changes how words are spread over the plan instead of giving every day
the same goal. The goals still average out to the daily goal and still add up to
the words left.

|Pattern      |Shape                                          |
|-------------|-----------------------------------------------|
|Flat / Steady|the same goal every day (default)              |
|Valley       |start high, ease in the middle, finish high    |
|Mountain     |start easy, peak in the middle, ease at the end|
|Rising       |goals grow over the plan                       |
|Declining    |goals shrink over the plan                     |
|Random       |goals vary at random within a range            |

Every pattern except flat asks for an **intensity**, which sets how far the
goals move from the average:

|Intensity         |Valley / Mountain|Rising / Declining / Random|
|------------------|-----------------|---------------------------|
|Mild              |0.8× – 1.2×      |0.8× – 1.2×                |
|Moderate (default)|0.7× – 1.5×      |0.5× – 1.5×                |
|Extreme           |0.5× – 2.0×      |0.3× – 2.0×                |

The random pattern is saved with the plan, so its goals don't change each time
you open the plan. Patterns follow the *writing* days: spare days and fixed-goal
days are skipped.

### Start date (option 6)

Moving the start date shows the new period and daily goal before anything
changes. If you have spare days or custom goals from today on, you can keep them
on their dates (recommended) or move them all by the same number of days. Then:

- Logged words never move. Words that end up outside the plan still count toward
  your total, but not toward any day's goal.
- If the plan has started, the remaining days are recalculated to cover the
  words that are left.
- The move is only applied after you confirm.

> 📖 **Running example — a "what if" (November 10)**
>
> You wonder what would happen if you restarted the plan on November 16:
>
> ```
> Moving the start 14 day(s) later.
>    Now: 2026-11-02 to 2026-12-31, 843 words/day
>
> Your spare days and custom goals from today on:
> All of them stay inside the new plan if kept on their dates.
>
> 1. Keep them on their dates (recommended)
>    -> 2026-11-16 to 2027-01-14, 631 words/day
> 2. Shift all of them 14 day(s) later
>    -> 2026-11-16 to 2027-01-14, 631 words/day
> 0. Cancel
>
> Enter your choice (0-2): 1
>
> ⚠ 8 day(s) with progress (7,350 words) are outside the new plan. Progress
>   never moves: those words still count as written, but not toward any day's goal.
> ⚠ The plan has started: the open days are recalculated to cover the 44,650
>   words left.
>
> Apply the new start date? [Y/n]: n
> ```
>
> You answer *no*, and the plan stays as it was.

### Weekend settings (option 8)

```
1. Same as weekdays - Write the same amount every day
2. Different goal - Set a specific word count for weekends
3. Weekends as spare days - No writing on weekends
```

- **Different goal**: weekend days get their own goal, higher or lower than
  weekdays.
- **Weekends as spare days**: weekend days have a goal of 0.
- For options 2 and 3, you can say which days count as the weekend: type the day
  numbers (`0`=Monday … `6`=Sunday), e.g. `4,5` for Friday and Saturday. The
  default is Saturday and Sunday.

The planner then asks how the plan should adjust.

### Individual day goals (option 9)

Give any future day of the plan its own goal: a busy day gets fewer words, a free
day more, and `0` turns it into a rest day. A custom goal overrides the pattern
and the weekend goal for that day.

```
1. Set custom goal for a specific day
2. Remove custom goal (revert to pattern/default)
3. Clear all custom day goals
```

A custom goal can't be set on a past day, on a day outside the plan, on a spare
day (remove the spare day first) or on a weekend day when weekends are off
(change the weekend settings first).

> 📖 **Running example — a busy Wednesday**
>
> On November 18 you have a workshop, so you plan only 300 words:
>
> ```
> Date (YYYY-MM-DD): 2026-11-18
>
> Current goal for Wednesday, 2026-11-18: 810 words
> New goal: 300
>
> ✓ Set custom goal of 300 words for 2026-11-18
>
> This changes the day's goal. How should the rest of the plan adjust?
>    Before: ends 2026-12-31, 810 words/day, total 60,000 words
> 1. Move the end date (keep 810 words/day)
>    -> ends 2027-01-01, 802 words/day, total 60,000 words
> 2. Keep the end date (change the daily goal)
>    -> ends 2026-12-31, 822 words/day, total 60,000 words
> 3. Keep the end date and the daily goal (change the total)
>    -> ends 2026-12-31, 810 words/day, total 59,490 words
>
> Enter your choice (1-3): 2
> ```
>
> The plan is now set: **822 words on weekdays, 1,200 on weekends, 300 on November
> 18, nothing from December 24 to 26, finishing on December 31.**

### Recalculate from progress (option 10)

Spreads the words you actually have left over the remaining writing days and
keeps the end date. This is the same as *"Increase/Reduce daily goals"* in
[the ahead/behind offer](#when-youre-ahead-or-behind).

### Plan name (option 11)

Type a new name, or press Enter to keep the current one.

---

## 7. Saving and loading

### Saving

Plan actions → **7. Save plan**.

- **A new plan** asks for a name (or offers to keep the template's name).
- **A plan loaded from a file** asks you to choose:
  1. **Overwrite the original file**, or
  2. **Save as a new file (with timestamp)**, where you can also change the name.
     The copy is a separate plan: it gets its own identity and is never the
     current plan (★).

Each save keeps the previous version of the file as a `.bak` backup.

> 📖 **Running example — saving**
>
> ```
> Would you like to save this plan? [Y/n]: y
> Enter a name for this plan: The Lighthouse Keeper
> ✓ Plan saved successfully to: ~/.wordplanner/plans/The_Lighthouse_Keeper_20261011_100000_000000.json
> ```

### Loading

Main menu → **3. Load an existing plan** lists every saved plan with its total,
daily goal, days and creation date. You can also open plans from
[Manage multiple plans](#13-managing-multiple-plans), or open the current plan
straight from the main menu with **Continue**.

### Unsaved changes

The planner knows whether the open plan has changed since it was last saved or
loaded:

- **Going back to the main menu** with unsaved changes asks: save and go back,
  go back without saving, or stay in the plan.
- **After logging progress**, leaving the progress screen asks *"Progress was
  updated. Save the plan?"*.
- **Ctrl+C** (or end of input) asks whether to save. If it can't ask (a second
  Ctrl+C, for example), it saves a copy as a new plan named
  *"<name> (recovered)"*, so the original file is never overwritten without your
  confirmation.

---

## 8. Tracking progress

Plan actions → **1. Update progress**:

```
1. Quick entry (today's words)
2. Enter for a specific date
3. View all progress entries
4. Enter your running total (manuscript word count)
0. Done
```

|Option            |Use it when                                                       |
|------------------|------------------------------------------------------------------|
|1 Quick entry     |you know how many words you wrote today                           |
|2 Specific date   |you forgot to log a past day, or want to correct one              |
|3 View all entries|you want a list of every logged day with its goal (✓ met, ○ short)|
|4 Running total   |you know your manuscript's word count, not the day's words        |

- Logging a day **replaces** that day's entry. It doesn't add to it.
- Future dates are refused.
- Days before the start or after the end can be logged after a warning: the words
  count toward your total, but not toward any day's goal.
- **Running total**: the day's words are your manuscript's total minus everything
  logged before that day, pre-existing words included. A total lower than that is
  refused (a day can't have negative words). If an earlier entry was too high,
  correct it with option 2.

### When you're ahead or behind

The first time you log words on a visit to this screen, the planner checks
whether you're on track. If you're ahead or behind, it shows by how much and asks
*"Would you like to adjust your plan?"*:

|You are|Option 1                            |Option 2                          |
|-------|------------------------------------|----------------------------------|
|Behind |Increase daily goals (keep end date)|Extend deadline (keep daily goals)|
|Ahead  |Reduce daily goals (keep end date)  |Finish early (keep daily goals)   |

Both options show a preview first and only change the plan when you confirm.
Both start **today**, or **tomorrow** if you've already logged words today. They
keep past goals as they were, keep your pattern and future custom goals, and keep
the weekend goal in the same proportion to the weekday goal.

A recalculation can't run when the goal is already met, when the plan's end date
has passed, or when no writing days are left.

> 📖 **Running example — the first week (Sunday, November 8)**
>
> The first week was uneven. You open the plan with *Continue the current plan*
> and log the past days with option 2:
>
> ```
> Date: 2026-11-02
> Entering progress for: 2026-11-02 (Monday)
> Goal for this day: 822 words
> Words written: 900
> ✓ Progress recorded: 900 words
> ```
>
> The check after this first entry says you're behind (the other days aren't
> logged yet), so you answer *no* for now. You log November 3 (750), 5 (1,100) and
> 7 (1,400). You wrote nothing on the 4th and 6th. Option 3 lists the entries:
>
> ```
> ✓ 2026-11-02 (Monday): 900 words (goal: 822)
> ○ 2026-11-03 (Tuesday): 750 words (goal: 822)
> ✓ 2026-11-05 (Thursday): 1,100 words (goal: 822)
> ✓ 2026-11-07 (Saturday): 1,400 words (goal: 1,200)
> ```
>
> You save when leaving the screen. In the evening your manuscript is at 12,950
> words, so you log today with the running total (option 4):
>
> ```
> Running total for: 2026-11-08 (Sunday)
> Logged before this day: 12,150 words (pre-existing words included)
> Your manuscript's total word count (or press Enter to cancel): 12950
> ✓ Progress recorded: 800 words on 2026-11-08 (running total 12,950)
>    (400 words short of goal)
>
> ⚠ You're BEHIND schedule
>   Expected: 5,310 words
>   Actual: 4,950 words
>   Behind by: 360 words (6.8%)
>
> Would you like to adjust your plan? [y/N]: y
>
> 1. Increase daily goals (keep end date)
> 2. Extend deadline (keep daily goals)
> 0. Keep plan as is
>
> Enter your choice (0-2): 1
>
> Proposed adjustment:
>   Changes from: 2026-11-09
>   Words remaining: 47,050
>   Remaining writing days: 50
>   Daily target: 822 -> 843 words
>   Daily increase: 21 words (2.6%)
>   Custom day goals kept: 1
>   Weekend goal: 1,231 words/day
>   Past daily goals locked: 1
>   Plan end date: 2026-12-31 (unchanged)
>
> Apply this adjustment? [Y/n]: y
> ✓ Plan recalculated!
> ```
>
> The words were logged today, so the change starts tomorrow. Weekdays now need
> 843 words, weekends 1,231 (the same ratio as before), and November 18 keeps its
> 300. Your past goals stay as they were.

### Progress summary

Plan actions → **2. View progress summary**: total written and remaining, days
recorded, current streak, and where you stand against the schedule.

> 📖 **Running example — the summary right after the recalculation**
>
> ```
> Overall Progress:
>   Total goal: 60,000 words
>   Written: 12,950 words (21.6%)
>   Remaining: 47,050 words
>
>   Days recorded: 5
>   Current streak: 2 days 🔥
>
> Schedule Status:
>   ✓ AHEAD by 800 words (19.3%)
>   Expected: 4,150 words
>   Actual: 4,950 words
>   Days elapsed: 6
> ```
>
> Why *ahead*? The recalculation set the schedule to the words you've actually
> written, so the expected words through yesterday are now exactly what you wrote
> (4,150). Today's 800 words already count, but today's goal only counts once the
> day is over.

---

## 9. Calendar views

Plan actions → **5. View calendar**: a monthly calendar, a weekly summary, or
both.

### Monthly calendar

One table per month, with the plan's details and progress at the top and a
milestones table at the end. Each day shows:

|Mark                    |Meaning                                                  |
|------------------------|---------------------------------------------------------|
|`822w`                  |the day's goal                                           |
|`✓900`                  |goal met or exceeded (with the words written)            |
|`~750`                  |partly written                                           |
|`✗`                     |a past day with a goal and no words                      |
|`SPARE`                 |a spare day                                              |
|`TODAY`                 |today (in reverse video, so it shows without colors too) |
|`12.9k/60k` and `21.58%`|running total up to that day, pre-existing words included|

Weekends are highlighted, and weeks are numbered. The first column can be Monday
or Sunday ([Settings](#14-settings)).

> 📖 **Running example — the calendar on November 8**
>
> ```
>                                    November 2026
> ┏━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
> ┃ Week  ┃     Mon     ┃     Tue      ┃     Wed     ┃     Thu      ┃     Fri     ┃     Sat      ┃     Sun     ┃
> ┡━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
> │  W1   │             │              │             │              │             │              │      1      │
> │  W2   │      2      │      3       │      4      │      5       │      6      │      7       │   8  TODAY  │
> │       │    822w     │     822w     │    822w     │     822w     │    822w     │    1,200w    │   1,200w    │
> │       │    ✓900     │     ~750     │      ✗      │    ✓1,100    │      ✗      │    ✓1,400    │    ~800     │
> │       │ 8,900/60,0… │ 9,650/60,000 │ 9,650/60,0… │  10.8k/60k   │  10.8k/60k  │  12.2k/60k   │  12.9k/60k  │
> │       │   14.83%    │    16.08%    │   16.08%    │    17.92%    │   17.92%    │    20.25%    │   21.58%    │
> │  W3   │      9      │      10      │     11      │      12      │     13      │      14      │     15      │
> │       │    843w     │     843w     │    843w     │     843w     │    843w     │    1,231w    │   1,231w    │
> │  W4   │     16      │      17      │     18      │      19      │     20      │      21      │     22      │
> │       │    843w     │     843w     │    300w     │     843w     │    843w     │    1,231w    │   1,231w    │
> ```
>
> December shows `SPARE` on the 24th, 25th and 26th. The milestones table shows
> when each quarter of the book should be reached:
>
> ```
> ┃ Progress ┃     Date     ┃ Target ┃ Written ┃ Plan Day ┃    Status    ┃
> │   25%    │ Nov 10, 2026 │ 15,000 │  12,950 │    9     │ 2,050 to go  │
> │   50%    │ Nov 27, 2026 │ 30,000 │  12,950 │    26    │ 17,050 to go │
> │   75%    │ Dec 13, 2026 │ 45,000 │  12,950 │    42    │ 32,050 to go │
> │   100%   │ Dec 31, 2026 │ 60,000 │  12,950 │    60    │ 47,050 to go │
> ```

### Weekly summary

One row per week (seven days counted from the start date), with: days written
out of the week's writing days, rest days, the daily goal (or its range when it
varies), the weekly goal, the words written that week with the share of the goal,
planned and actual running totals, and how far ahead (+) or behind (−) you are at
the end of the week. For the week you're in, the planned total and the +/− count
goals only up to yesterday (today counts once it's over), so +/− is always the
actual total minus the planned total.

> 📖 **Running example**
>
> ```
> ┃ Week ┃      Dates      ┃ Days Written ┃ Rest Days ┃ Daily Goal ┃ Weekly Goal ┃   Written ┃ Planned Total ┃ Actual Total ┃  +/- ┃
> │  1   │ Nov 02 - Nov 08 │     5/7      │     -     │  822-1,200 │       6,510 │ 4,950 76% │        12,150 │       12,950 │ +800 │
> │  2   │ Nov 09 - Nov 15 │     -/7      │     -     │  843-1,231 │       6,677 │           │        20,027 │              │      │
> │  3   │ Nov 16 - Nov 22 │     -/7      │     -     │  300-1,231 │       6,134 │           │        26,161 │              │      │
> │  8   │ Dec 21 - Dec 27 │     -/4      │     3     │  843-1,231 │       3,760 │           │        56,628 │              │      │
> │  9   │ Dec 28 - Dec 31 │     -/4      │     -     │        843 │       3,372 │           │        60,000 │              │      │
> ```

---

## 10. Graphs and analytics

Plan actions → **3. View progress graphs & analytics**:

```
1. View statistics summary
2. Cumulative progress (Expected vs Actual)
3. Daily progress bar chart
4. Writing velocity over time
5. Milestone progress chart
6. View all graphs
```

|View               |Shows                                                                                                                                      |
|-------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
|Statistics summary |totals, average per writing day, best and worst day, current and longest streak, schedule status in writing days, estimated completion date|
|Cumulative progress|a line graph of the words expected vs. written over time                                                                                   |
|Daily bar chart    |goal vs. words written for each day (the last 30 days)                                                                                     |
|Writing velocity   |words per day as a 3-day moving average, against your goal (needs 3 days of data)                                                          |
|Milestone progress |bars for 25%, 50%, 75% and 100%                                                                                                            |

Graphs are drawn in the terminal. Averages are per **writing day that has gone
by**, including days with no words, so gaps lower the average. The estimated
completion date spends that average on each coming writing day, skipping rest
days.

> 📖 **Running example — statistics on November 8**
>
> ```
> │ Total Words Written     │ 12,950                    │
> │ Total Goal              │ 60,000                    │
> │ Remaining               │ 47,050                    │
> │ Completion              │ 21.6%                     │
> ├─────────────────────────┼───────────────────────────┤
> │ Days with Progress      │ 5                         │
> │ Average per Writing Day │ 707 words                 │
> │ Planned Daily Goal      │ 843 words                 │
> │ Best Day                │ Sat Nov 07: 1,400 words   │
> │ Worst Day               │ Tue Nov 03: 750 words     │
> ├─────────────────────────┼───────────────────────────┤
> │ Current Streak          │ 2 days                    │
> │ Longest Streak          │ 2 days                    │
> ├─────────────────────────┼───────────────────────────┤
> │ Schedule Status         │ AHEAD by 0.7 writing days │
> │ Estimated Completion    │ 2027-01-17 (70 days)      │
> ```
>
> 4,950 words over 7 writing days is 707 a day, less than the 843 you need. At that
> pace you'd finish on January 17, more than two weeks late. That's a reason to
> write a little more every day.

---

## 11. Exports

Plan actions → **6. Export plan**: CSV, iCal, Markdown, or all three. Files go
to the `exports` folder (see [Files and storage](#15-files-and-storage)) and are
named `<Plan name>_<YYYYMMDD_HHMMSS>.<csv|ics|md>`.

### CSV (spreadsheets)

One row per day of the plan, ready for Excel, LibreOffice or Google Sheets:

```
Date,Day_of_Week,Day_Number,Day_Type,Daily_Goal,Actual_Words,Cumulative_Goal,Cumulative_Actual,Status
2026-11-02,Monday,1,Writing,822,900,822,900,Exceeded
2026-11-03,Tuesday,2,Writing,822,750,1644,1650,Partial
2026-11-04,Wednesday,3,Writing,822,,2466,1650,Missed
2026-11-08,Sunday,7,Writing,1200,800,6510,4950,Partial
2026-11-09,Monday,8,Writing,843,,7353,4950,Future
```

`Day_Type` is `Writing` or `Spare`. `Status` is one of Exceeded, Met, Partial,
Missed, Future or Spare. Dates are always `YYYY-MM-DD`, whatever your date format
setting.

### iCal / ICS (calendar apps)

One all-day event per day of the plan, such as *"Write 822 words - The Lighthouse
Keeper"*, with the plan day and the total goal in the description. Spare and rest
days are marked "free" so they don't block your calendar. Import the file into
Google Calendar, Apple Calendar, Outlook and similar apps. Each plan has a stable
identity, so importing a newer export of the same plan updates its events
instead of duplicating them (in apps that support this).

When you export to iCal (alone or with *All formats*), the planner asks:

```
Add a reminder on each writing day? [Y/n]: y
Reminder time (HH:MM, or press Enter for 09:00): 19:30
```

Each writing day's event then gets a reminder at that time. Rest and spare days
get none. Calendar apps handle imported reminders differently: Apple Calendar and
Thunderbird keep them, while some apps (Google Calendar, for one) ignore them on
import and use your default notifications instead.

### Markdown (reading and sharing)

A readable report: plan overview, progress, the daily schedule week by week
(with ✅ / ⚠️ next to logged days) and the milestones table.

```markdown
# The Lighthouse Keeper

## Plan Overview

- **Total Word Goal**: 60,000 words
- **Written Before the Plan**: 8,000 words
- **Average Daily Goal**: 843 words/day
...
### Week 1

- **Mon, November 02, 2026**: 822 words → 900 written ✅
- **Tue, November 03, 2026**: 822 words → 750 written ⚠️
```

---

## 12. Commands without the menus

For everyday logging you don't need the menus. These commands work on the
**current plan (★)**: they load it, change it, save it over its file and print
where it stands.

```bash
uv run python planea.py status                     # today's goal, words written, ahead/behind
uv run python planea.py log 1200                   # words written today (replaces today's entry)
uv run python planea.py log --total 23,450         # the manuscript's running total
uv run python planea.py log 800 --date 2026-11-03  # an earlier day
uv run python planea.py --help                     # help (also: log --help)
```

- Word counts may contain commas (`23,450`).
- `--date` accepts `YYYY-MM-DD` or your chosen date format.
- Past days are locked first, as in the menus.
- Exit codes: `0` done, `1` refused (no current plan, a future date, a running
  total below what's logged), `2` wrong usage. This makes the commands easy to use
  in shell aliases and scripts. For a daily reminder, run `planea.py status` from
  your shell startup file or a cron job.

> 📖 **Running example — logging from the terminal (November 9 and 10)**
>
> Monday morning:
>
> ```
> $ planea.py status
> ★ The Lighthouse Keeper (Nov 02, 2026 - Dec 31, 2026)
> Today (Mon Nov 09): 0 / 843 words, 843 to go
> Written: 12,950 / 60,000 words (21.6%), 47,050 to go
> Status: ⚠ behind by 400 words
> ```
>
> Yesterday is over now, so its 1,200-word goal counts: you wrote 800, which puts
> you 400 behind. In the evening the manuscript is at 13,850:
>
> ```
> $ planea.py log --total 13,850
> Logged 900 words on 2026-11-09.
>
> ★ The Lighthouse Keeper (Nov 02, 2026 - Dec 31, 2026)
> Today (Mon Nov 09): 900 / 843 words ✓
> Written: 13,850 / 60,000 words (23.1%), 46,150 to go
> Status: ✓ ahead by 500 words
> ```
>
> On Tuesday you log 1,000 words, and then remember that you did write 500 words on
> November 4:
>
> ```
> $ planea.py log 1000
> Logged 1,000 words on 2026-11-10.
> ...
> $ planea.py log 500 --date 2026-11-04
> Logged 500 words on 2026-11-04.
>
> ★ The Lighthouse Keeper (Nov 02, 2026 - Dec 31, 2026)
> Today (Tue Nov 10): 1,000 / 843 words ✓
> Written: 15,350 / 60,000 words (25.6%), 44,650 to go
> Status: ✓ ahead by 1,157 words
> ```
>
> Mistakes are refused with exit code 1, and nothing changes:
>
> ```
> $ planea.py log --total 9000
> Error: a running total of 9,000 is 5,350 below the 14,350 already logged before
> 2026-11-10 (pre-existing words included). Logged days can't go negative; correct
> an earlier day with --date.
>
> $ planea.py log 100 --date 2026-11-20
> Error: 2026-11-20 is in the future.
> ```

---

## 13. Managing multiple plans

Main menu → **4. Manage multiple plans**:

```
1. View all plans overview
2. Filter and sort plans
3. Search plans
4. Compare plans
5. Set the current plan (★)
6. Manage plan categories and tags
7. Archive/Unarchive plans
8. View plan statistics
9. Open a plan
10. Delete a plan
```

### The current plan (★)

One plan can be the **current plan**. It's marked ★ everywhere, the main menu
offers *Continue the current plan*, and the [commands](#12-commands-without-the-menus)
work on it. Choose it with option 5, where `0` clears it.

### Overview (1)

Your plans grouped by status, with totals. Active plans show their completion
and whether they're on track (or when they start).

> 📖 **Running example — making it the current plan, with a category and tags**
>
> After saving, you set *The Lighthouse Keeper* as the current plan (option 5),
> choose the category `novel` and add the tags `draft, fiction` (option 6). The
> overview now shows:
>
> ```
> Total Plans: 1
> Active: 1 | Archived: 0 | Completed: 0
> Total Word Goal: 60,000 words
> Total Written: 8,000 words
>
> ★ Current plan: The Lighthouse Keeper
>
> Active Plans (1):
> ----------------------------------------------------------------------
> ★ • The Lighthouse Keeper
>    60,000 words | [novel] | Tags: draft, fiction
>    Not started yet (starts 2026-11-02)
> ```

### Filter and sort (2)

- Filter by **status** (active, archived, completed), **category** or **tag**.
- Sort all plans by name (A–Z), creation date, last modified, completion % or
  deadline (end date).

### Search (3)

Finds plans whose name, tags or category contain the text you type (case doesn't
matter).

### Compare (4)

Pick two or more plans (e.g. `1,3,4`) to see them side by side: total, daily
goal, days, category, status, completion, words written, remaining, start date
and on-track status. A summary with combined totals follows.

### Categories and tags (6)

- **Categories** (one per plan): novel, short-story, novella, blog, article,
  academic, screenplay, poetry, non-fiction, other.
- **Tags** (any number): free words separated by commas. They're stored in
  lowercase, and a tag is never added twice.
- You can also remove tags and list every tag and category in use.

### Archive, unarchive, complete (7)

Statuses are **active**, **archived** and **completed**. Archiving or completing
a plan also stops it being the current plan. Unarchiving makes it active again.

### Statistics (8)

Totals across all plans: plans by status, total word goal and words written,
plans with progress, average completion of active plans, categories and tags in
use, and the current plan.

### Open and delete (9, 10)

*Open* takes you to the plan actions menu. *Delete* asks for confirmation and
removes the plan file and its backup. This can't be undone.

---

## 14. Settings

Main menu → **5. Settings**. Each option shows its current value.

|Setting                    |What it does                                                                                                                                                                                                                                                  |
|---------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|**Save directory location**|Where plans and exports are kept (`<folder>/plans`, `<folder>/exports`). The folder is created if needed and checked for write access. If plans are left in the old folder, the planner offers to move them. *Reset to default* goes back to `~/.wordplanner`.|
|**Defaults for new plans** |A writing pattern (with intensity) and a weekend setting (same, a different goal, or no writing) offered first when you create a plan from scratch. Templates keep their own suggestions.                                                                     |
|**First day of the week**  |Monday or Sunday as the first column of the monthly calendar.                                                                                                                                                                                                 |
|**Date format**            |`2026-11-05`, `05/11/2026`, `11/05/2026` or `Nov 05, 2026`. Used on screen, in the Markdown export and in commands. You can type dates as `YYYY-MM-DD` or in your numeric format. Plan files, CSV and iCal always use `YYYY-MM-DD`.                           |
|**Colors**                 |Turn off colors in tables, the calendar and graphs. The symbols (✓ ~ ✗) and the TODAY marker stay. The `NO_COLOR` environment variable also turns colors off.                                                                                                 |

---

## 15. Files and storage

|What       |Where (default)                                              |
|-----------|-------------------------------------------------------------|
|Plans      |`~/.wordplanner/plans/<Name>_<date>_<time>.json`             |
|Backups    |`~/.wordplanner/plans/<file>.json.bak` (the previous version)|
|Exports    |`~/.wordplanner/exports/`                                    |
|Preferences|`~/.wordplanner/preferences.json`                            |

- Plans are plain JSON. Files are written safely (to a temporary file, then
  renamed), so a crash can't leave a half-written plan.
- File names come from the plan name: spaces become `_` and symbols such as
  `/` or `:` are dropped.
- Plan files from older versions of the planner still load. Old formats are
  converted when they're read.
- A plan's *last modified* date only changes when its content actually changed.

---

## 16. Reference: limits and rules

|Limit                              |Value                                               |
|-----------------------------------|----------------------------------------------------|
|Total words, pre-existing words    |up to 10,000,000                                    |
|Daily, weekend and custom day goals|up to 100,000                                       |
|Writing days                       |up to 36,500 (100 years)                            |
|Spare days                         |from the start date to about one year after the plan|

|Rule                        |Effect                                                                                                  |
|----------------------------|--------------------------------------------------------------------------------------------------------|
|Past days are locked        |goals before today never change; spare days, custom goals and plan length can't be changed for past days|
|Logging replaces            |logging a day overwrites its entry                                                                      |
|No future logging           |words can't be logged for days after today                                                              |
|Running totals can't go down|a total below what's already logged is refused                                                          |
|Rest days aren't missed     |days with a goal of 0 are never missed and don't break streaks                                          |
|Today counts when it's over |the on-track status expects goals through yesterday and counts every word written                       |
|Previews first              |recalculations, adjustments and start-date moves are shown before they're applied                       |

---

## 17. Troubleshooting

**"Days before today are locked: their goals can't change."**
You tried to add a spare day, a custom goal or another change on a past date. Only
today and later can be changed. Words for past days can still be logged.

**"… is a spare day. Remove it in 'Manage spare days' first."**
A custom goal can't go on a spare day. Remove the spare day first, then set the
goal.

**"…s are rest days in this plan. Change the weekend settings first."**
Weekends are off in this plan, so weekend days can't have custom goals.

**A spare day is listed as "(outside the plan, ignored)".**
It's after the plan's end (or before its start). It has no effect, but it's kept
in case the plan grows to include it.

**The commands say "there is no current plan (★)".**
Open *Manage multiple plans → Set the current plan (★)* and choose one.

**My plans disappeared after changing the save directory.**
The planner only lists plans in the current folder. Your files are still in the
old folder: set it again, or move them (the planner offers to when you change the
folder).

**"Cannot recalculate: Plan end date has already passed."**
Extend the plan first (Modify plan → Writing days, or move the end date), then
recalculate.

**The daily goal I see isn't what every day shows.**
The daily goal is that of an ordinary weekday. Weekends, custom goals, spare days
and patterns give other days different goals. Check the monthly calendar for each
day's goal.

---

> 📖 **Running example — where the story stands**
>
> On November 10 *The Lighthouse Keeper* is at 15,350 words (25.6%), 1,157 words
> ahead of schedule. It has 843 words planned for each weekday, 1,231 for each
> weekend day, a light day on November 18 and Christmas off, and it ends on
> December 31. Happy writing!
