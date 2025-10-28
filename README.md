# planeapalabras - Word Count Planner

A writing planning tool inspired by [pacemaker.press](https://pacemaker.press) that helps writers calculate and visualize their writing goals. Available as both a modern terminal UI and a traditional console interface.

## Overview

Writing requires managing three key variables:
- **Total words** - Your word count goal
- **Daily words** - How many words you can write per day
- **Time (days)** - How long you have to write

Given any two variables, **planeapalabras** calculates the third and provides beautiful calendar visualizations to help you stay on track.

## Features

### ✅ Implemented

- **Two User Interfaces**
  - Modern Textual TUI with buttons, forms, and keyboard shortcuts
  - Traditional console interface with text menus

- **Three Calculation Methods**
  1. Calculate days needed (given total words + daily capacity)
  2. Calculate total words (given daily capacity + available time)
  3. Calculate daily words needed (given total words + available time)

- **Calendar Visualization**
  - Monthly calendar view with day-by-day word goals
  - Weekly summary with cumulative progress tracking
  - Milestone tracking (25%, 50%, 75%, 100%)
  - Weekend highlighting
  - Start date selection

- **Save & Load Plans**
  - Save plans with custom names
  - Load previously saved plans
  - Plans stored as JSON in `~/.planeapalabras/plans/`
  - View creation dates and plan details

- **Beautiful Terminal UI**
  - Built with Rich and Textual libraries
  - Color-coded displays
  - Scrollable calendar views
  - Form validation

## Installation

### Requirements

- Python 3.13+ (see `.python-version`)
- uv package manager (recommended) or pip

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd planeapalabras

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install rich textual
# or
uv pip install -e .
```

## Usage

### Textual TUI (Recommended)

Modern, interactive terminal interface:

```bash
python app.py
```

**Features:**
- Button-based navigation
- Form-based input with validation
- Screen-based workflow
- Keyboard shortcuts:
  - `ESC` - Go back
  - `M` - Return to main menu (from calendar)
  - `Q` - Quit application
  - Arrow keys, Page Up/Down, mouse wheel - Scroll

### Console Interface

Traditional text-based menu system:

```bash
python planea.py
```

**Features:**
- Text-based interactive menus
- Full Rich calendar visualization support
- Number-based navigation

## Workflow Example

1. **Create a Plan**
   - Choose a calculation type
   - Enter your known values (e.g., 50,000 words, 1,000 words/day)
   - Get your calculated result (e.g., 50 days needed)

2. **Save Your Plan**
   - Give it a descriptive name (e.g., "My Novel Draft 1")
   - Plan is saved automatically to `~/.planeapalabras/plans/`

3. **Visualize with Calendar**
   - Choose monthly, weekly, or both views
   - Select a start date
   - See your daily word goals laid out across weeks and months
   - View progress milestones

4. **Load Later**
   - Return to the app anytime
   - Select "Load Saved Plan" from the main menu
   - Pick your plan and continue planning

## File Structure

```
planeapalabras/
├── app.py              # Textual TUI application
├── planea.py           # Console interface
├── plan.py             # Core Plan class
├── calendar_view.py    # Calendar visualization
├── plan_storage.py     # Save/load functionality
├── README.md           # This file
├── CLAUDE.md           # Developer documentation
└── pyproject.toml      # Project dependencies
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

## TODO / Planned Features

- [ ] Different planning patterns (valley, mountain, rising, declining, random)
- [ ] Spare days functionality
- [ ] Weekend-specific planning (different word goals for weekends)
- [ ] Plan tracking with actual progress
- [ ] Recalculation based on progress
- [ ] Progress graphs (expected vs actual words written)
- [ ] Export plans to different formats (CSV, PDF, etc.)

## Contributing

This is a personal project, but suggestions and feedback are welcome!

## License

[Your license here]

## Acknowledgments

Inspired by [pacemaker.press](https://pacemaker.press) - a web-based writing planning tool.
