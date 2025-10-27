#!/usr/bin/env python3
"""Textual TUI application for the word count planner."""

import calendar
from datetime import datetime, timedelta
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Header, Footer, Button, Static, Input, Label, RadioButton, RadioSet, DataTable
from textual.widget import Widget
from textual.binding import Binding
from rich.text import Text

import plan
import calendar_view
import plan_storage


class MonthlyCalendarWidget(Widget):
    """Widget to display monthly calendar view with word goals."""

    def __init__(self, plan_obj: plan.Plan, start_date: datetime, **kwargs):
        super().__init__(**kwargs)
        self.plan_obj = plan_obj
        self.start_date = start_date
        self.end_date = start_date + timedelta(days=int(plan_obj.time) - 1)

    def compose(self) -> ComposeResult:
        """Create monthly calendar tables."""
        # Display plan summary
        yield Static(
            f"[bold cyan]Total Words:[/bold cyan] {self.plan_obj.total:,.0f}  "
            f"[bold green]Daily Goal:[/bold green] {self.plan_obj.daily:,.0f} words/day  "
            f"[bold yellow]Duration:[/bold yellow] {self.plan_obj.time:.0f} days\n"
            f"[bold magenta]Start:[/bold magenta] {self.start_date.strftime('%B %d, %Y')}  "
            f"[bold magenta]End:[/bold magenta] {self.end_date.strftime('%B %d, %Y')}\n",
            classes="calendar-summary"
        )

        # Generate monthly calendars
        current_date = self.start_date
        days_remaining = int(self.plan_obj.time)
        max_months = 24
        months_shown = 0

        while days_remaining > 0 and months_shown < max_months:
            months_shown += 1
            first_of_month = datetime(current_date.year, current_date.month, 1)

            if first_of_month > self.end_date:
                break

            # Create table for this month
            month_name = current_date.strftime("%B %Y")
            table = DataTable(classes="month-table")
            table.add_column("Week", width=6)
            table.add_column("Mon", width=12)
            table.add_column("Tue", width=12)
            table.add_column("Wed", width=12)
            table.add_column("Thu", width=12)
            table.add_column("Fri", width=12)
            table.add_column("Sat", width=12)
            table.add_column("Sun", width=12)

            # Title for the month
            yield Static(f"[bold cyan]{month_name}[/bold cyan]", classes="month-title")

            # Get calendar for this month
            cal = calendar.monthcalendar(current_date.year, current_date.month)
            days_added_this_month = 0

            # Process each week
            week_num = 1
            for week in cal:
                row = [f"W{week_num}"]
                week_num += 1

                for day in week:
                    if day == 0:
                        row.append("")
                    else:
                        day_date = datetime(current_date.year, current_date.month, day)

                        if self.start_date <= day_date <= self.end_date:
                            days_elapsed = (day_date - self.start_date).days + 1
                            cell_text = Text()
                            cell_text.append(f"{day}\n", style="bold white")
                            cell_text.append(f"{self.plan_obj.daily:,.0f}w", style="green")
                            row.append(cell_text)

                            days_remaining -= 1
                            days_added_this_month += 1
                            if days_remaining == 0:
                                break
                        else:
                            row.append(str(day))

                table.add_row(*row, height=2)
                if days_remaining == 0:
                    break

            # Yield the table for this month before checking if we're done
            yield table

            # Safety check: if we didn't add any days this month, we've gone past the plan
            if days_added_this_month == 0:
                break

            # Exit if we've finished all days
            if days_remaining <= 0:
                break

            # Move to next month
            if current_date.month == 12:
                current_date = datetime(current_date.year + 1, 1, 1)
            else:
                current_date = datetime(current_date.year, current_date.month + 1, 1)


class WeeklySummaryWidget(Widget):
    """Widget to display weekly summary with cumulative totals."""

    def __init__(self, plan_obj: plan.Plan, start_date: datetime, **kwargs):
        super().__init__(**kwargs)
        self.plan_obj = plan_obj
        self.start_date = start_date

    def compose(self) -> ComposeResult:
        """Create weekly summary table."""
        yield Static("[bold cyan]Weekly Summary[/bold cyan]\n", classes="section-title")

        table = DataTable(classes="weekly-table")
        table.add_column("Week", width=8)
        table.add_column("Dates", width=30)
        table.add_column("Daily Goal", width=15)
        table.add_column("Weekly Total", width=15)
        table.add_column("Cumulative", width=15)

        current_date = self.start_date
        days_remaining = int(self.plan_obj.time)
        week_num = 1
        cumulative_words = 0

        while days_remaining > 0:
            days_in_week = min(7, days_remaining)
            week_end = current_date + timedelta(days=days_in_week - 1)

            weekly_words = int(self.plan_obj.daily * days_in_week)
            cumulative_words += weekly_words

            date_range = f"{current_date.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}"

            table.add_row(
                str(week_num),
                date_range,
                f"{self.plan_obj.daily:,.0f}",
                f"{weekly_words:,}",
                f"{cumulative_words:,}"
            )

            current_date = week_end + timedelta(days=1)
            days_remaining -= days_in_week
            week_num += 1

        yield table


class MilestonesWidget(Widget):
    """Widget to display progress milestones."""

    def __init__(self, plan_obj: plan.Plan, start_date: datetime, **kwargs):
        super().__init__(**kwargs)
        self.plan_obj = plan_obj
        self.start_date = start_date

    def compose(self) -> ComposeResult:
        """Create milestones table."""
        yield Static("[bold cyan]Milestones[/bold cyan]\n", classes="section-title")

        table = DataTable(classes="milestones-table")
        table.add_column("Progress", width=12)
        table.add_column("Date", width=20)
        table.add_column("Words Written", width=18)
        table.add_column("Days Elapsed", width=15)

        milestones = [0.25, 0.50, 0.75, 1.0]

        for milestone in milestones:
            days_to_milestone = int(self.plan_obj.time * milestone)
            words_at_milestone = int(self.plan_obj.total * milestone)
            date_at_milestone = self.start_date + timedelta(days=days_to_milestone - 1)

            table.add_row(
                f"{int(milestone * 100)}%",
                date_at_milestone.strftime("%b %d, %Y"),
                f"{words_at_milestone:,}",
                str(days_to_milestone)
            )

        yield table


class MainMenuScreen(Screen):
    """Main menu screen for choosing calculation type."""

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
    ]

    def compose(self) -> ComposeResult:
        """Create the main menu UI."""
        yield Header()
        yield Container(
            Static("[bold cyan]Word Count Planner[/bold cyan]", id="title"),
            Static("\nWhat do you know about your writing project?\n", id="subtitle"),
            Vertical(
                Button("Calculate days needed", id="btn_calc_time", variant="primary"),
                Button("Calculate total words", id="btn_calc_words", variant="primary"),
                Button("Calculate daily words", id="btn_calc_daily", variant="primary"),
                Button("Load Saved Plan", id="btn_load_plan", variant="success"),
                Button("Exit", id="btn_exit", variant="error"),
                id="menu_buttons"
            ),
            id="main_container"
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn_calc_time":
            # Know total words and daily words → calculate time
            self.app.push_screen(InputScreen(
                mode="time",
                title="Calculate Days Needed",
                prompts=[
                    ("total", "Total word goal:"),
                    ("daily", "Words you can write daily:")
                ]
            ))
        elif button_id == "btn_calc_words":
            # Know daily words and time → calculate total words
            self.app.push_screen(InputScreen(
                mode="words",
                title="Calculate Total Words",
                prompts=[
                    ("daily", "Words you can write daily:"),
                    ("time", "Days you have available:")
                ]
            ))
        elif button_id == "btn_calc_daily":
            # Know total words and time → calculate daily words
            self.app.push_screen(InputScreen(
                mode="daily",
                title="Calculate Daily Words Needed",
                prompts=[
                    ("total", "Total word goal:"),
                    ("time", "Days you have available:")
                ]
            ))
        elif button_id == "btn_load_plan":
            # Load saved plan
            self.app.push_screen(LoadPlanScreen())
        elif button_id == "btn_exit":
            self.app.exit()


class InputScreen(Screen):
    """Screen for inputting calculation parameters."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    def __init__(self, mode: str, title: str, prompts: list, **kwargs):
        super().__init__(**kwargs)
        self.mode = mode
        self.screen_title = title
        self.prompts = prompts
        self.inputs = {}

    def compose(self) -> ComposeResult:
        """Create the input form UI."""
        yield Header()

        widgets = [
            Static(f"[bold cyan]{self.screen_title}[/bold cyan]", id="input_title"),
            Static(""),
        ]

        # Create input fields
        for field_id, label_text in self.prompts:
            widgets.append(Label(label_text))
            widgets.append(Input(placeholder="Enter a positive number", id=f"input_{field_id}"))
            widgets.append(Static(""))

        widgets.append(
            Horizontal(
                Button("Calculate", id="btn_calculate", variant="success"),
                Button("Cancel", id="btn_cancel", variant="error"),
                id="button_row"
            )
        )

        yield Container(*widgets, id="input_container")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn_calculate":
            # Collect and validate inputs
            values = {}
            valid = True

            for field_id, _ in self.prompts:
                input_widget = self.query_one(f"#input_{field_id}", Input)
                try:
                    value = float(input_widget.value)
                    if value <= 0:
                        self.notify("All values must be positive numbers!", severity="error")
                        valid = False
                        break
                    values[field_id] = value
                except ValueError:
                    self.notify(f"Invalid input for {field_id}. Please enter a number.", severity="error")
                    valid = False
                    break

            if valid:
                # Create plan and calculate
                newplan = plan.Plan(**values)

                if self.mode == "time":
                    newplan.calculate_time()
                elif self.mode == "words":
                    newplan.calculate_words()
                elif self.mode == "daily":
                    newplan.calculate_daily()

                # Show results
                self.app.push_screen(ResultsScreen(newplan))

        elif event.button.id == "btn_cancel":
            self.app.pop_screen()

    def action_cancel(self) -> None:
        """Cancel and return to main menu."""
        self.app.pop_screen()


class ResultsScreen(Screen):
    """Screen for displaying calculation results and calendar options."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("n", "new_plan", "New Plan", show=True),
    ]

    def __init__(self, plan_obj: plan.Plan, **kwargs):
        super().__init__(**kwargs)
        self.plan_obj = plan_obj

    def compose(self) -> ComposeResult:
        """Create the results display UI."""
        yield Header()

        yield Container(
            Static("[bold cyan]Your Writing Plan[/bold cyan]", id="results_title"),
            Static(""),
            Static(f"[bold]Total words:[/bold] {self.plan_obj.total:,.0f} words"),
            Static(f"[bold]Time needed:[/bold] {self.plan_obj.time:.1f} days"),
            Static(f"[bold]Daily goal:[/bold] {self.plan_obj.daily:,.1f} words per day"),
            Static(""),
            Static("[bold yellow]Would you like to see your plan as a calendar?[/bold yellow]"),
            Static(""),
            Vertical(
                Button("Monthly Calendar View", id="btn_monthly", variant="primary"),
                Button("Weekly Summary View", id="btn_weekly", variant="primary"),
                Button("Both Views", id="btn_both", variant="primary"),
                Button("Skip Calendar", id="btn_skip", variant="default"),
                Static(""),
                Button("Save This Plan", id="btn_save", variant="success"),
                id="calendar_buttons"
            ),
            id="results_container"
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id in ["btn_monthly", "btn_weekly", "btn_both"]:
            # Ask for start date
            self.app.push_screen(DateInputScreen(self.plan_obj, button_id))
        elif button_id == "btn_save":
            # Save the plan
            self.app.push_screen(SavePlanScreen(self.plan_obj))
        elif button_id == "btn_skip":
            self.app.pop_screen()

    def action_back(self) -> None:
        """Go back to main menu."""
        self.app.pop_screen()

    def action_new_plan(self) -> None:
        """Create a new plan."""
        self.app.pop_screen()


class DateInputScreen(Screen):
    """Screen for inputting the start date."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    def __init__(self, plan_obj: plan.Plan, view_type: str, **kwargs):
        super().__init__(**kwargs)
        self.plan_obj = plan_obj
        self.view_type = view_type

    def compose(self) -> ComposeResult:
        """Create the date input UI."""
        yield Header()

        yield Container(
            Static("[bold cyan]Start Date[/bold cyan]", id="date_title"),
            Static(""),
            Label("When would you like to start writing?"),
            Label("Enter date in format YYYY-MM-DD (e.g., 2025-11-01)"),
            Label("Or leave empty to start today"),
            Static(""),
            Input(placeholder="YYYY-MM-DD or press Enter for today", id="input_date"),
            Static(""),
            Horizontal(
                Button("Show Calendar", id="btn_show", variant="success"),
                Button("Cancel", id="btn_cancel", variant="error"),
                id="date_button_row"
            ),
            id="date_container"
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn_show":
            date_input = self.query_one("#input_date", Input)
            date_str = date_input.value.strip()

            if date_str == "":
                start_date = datetime.now()
            else:
                try:
                    start_date = datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    self.notify("Invalid date format. Using today's date.", severity="warning")
                    start_date = datetime.now()

            # Show calendar view(s)
            self.app.push_screen(CalendarScreen(self.plan_obj, start_date, self.view_type))

        elif event.button.id == "btn_cancel":
            self.app.pop_screen()

    def action_cancel(self) -> None:
        """Cancel and return."""
        self.app.pop_screen()


class CalendarScreen(Screen):
    """Screen for displaying calendar views."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("m", "quit_to_menu", "Main Menu", show=True, priority=True),
        Binding("up", "scroll_up", "Scroll Up", show=False),
        Binding("down", "scroll_down", "Scroll Down", show=False),
    ]

    def __init__(self, plan_obj: plan.Plan, start_date: datetime, view_type: str, **kwargs):
        super().__init__(**kwargs)
        self.plan_obj = plan_obj
        self.start_date = start_date
        self.view_type = view_type

    def compose(self) -> ComposeResult:
        """Create the calendar display."""
        yield Header()

        # Add scroll instructions
        yield Static(
            "[dim]Use ↑/↓ arrow keys, Page Up/Down, or mouse wheel to scroll through the calendar[/dim]",
            id="scroll_hint"
        )

        with VerticalScroll(id="calendar_scroll"):
            # Show appropriate views based on view_type
            if self.view_type == "btn_monthly":
                yield MonthlyCalendarWidget(self.plan_obj, self.start_date)
                yield Static("")  # Spacer
                yield MilestonesWidget(self.plan_obj, self.start_date)
            elif self.view_type == "btn_weekly":
                yield WeeklySummaryWidget(self.plan_obj, self.start_date)
                yield Static("")  # Spacer
                yield MilestonesWidget(self.plan_obj, self.start_date)
            elif self.view_type == "btn_both":
                yield MonthlyCalendarWidget(self.plan_obj, self.start_date)
                yield Static("")  # Spacer
                yield WeeklySummaryWidget(self.plan_obj, self.start_date)
                yield Static("")  # Spacer
                yield MilestonesWidget(self.plan_obj, self.start_date)

        yield Footer()

    def action_scroll_up(self) -> None:
        """Scroll up in the calendar."""
        scroll = self.query_one("#calendar_scroll", VerticalScroll)
        scroll.scroll_up()

    def action_scroll_down(self) -> None:
        """Scroll down in the calendar."""
        scroll = self.query_one("#calendar_scroll", VerticalScroll)
        scroll.scroll_down()

    def action_back(self) -> None:
        """Go back."""
        self.app.pop_screen()

    def action_quit_to_menu(self) -> None:
        """Return to main menu."""
        # Pop all screens to return to main menu
        # Schedule multiple pops - we need to pop CalendarScreen, DateInputScreen, ResultsScreen, and InputScreen
        def pop_multiple():
            try:
                # Pop DateInputScreen
                self.app.pop_screen()
                # Pop ResultsScreen
                self.app.pop_screen()
                # Pop InputScreen
                self.app.pop_screen()
            except Exception:
                pass

        # Pop CalendarScreen first, then schedule the rest
        self.app.call_after_refresh(pop_multiple)
        self.app.pop_screen()


class SavePlanScreen(Screen):
    """Screen for naming and saving a plan."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    def __init__(self, plan_obj: plan.Plan, **kwargs):
        super().__init__(**kwargs)
        self.plan_obj = plan_obj

    def compose(self) -> ComposeResult:
        """Create the save plan UI."""
        yield Header()

        yield Container(
            Static("[bold cyan]Save Your Plan[/bold cyan]", id="save_title"),
            Static(""),
            Label("Give your plan a name:"),
            Input(placeholder="e.g., My Novel, Short Story Project", id="input_plan_name"),
            Static(""),
            Horizontal(
                Button("Save", id="btn_save", variant="success"),
                Button("Cancel", id="btn_cancel", variant="error"),
                id="save_button_row"
            ),
            id="save_container"
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn_save":
            name_input = self.query_one("#input_plan_name", Input)
            plan_name = name_input.value.strip()

            if not plan_name:
                self.notify("Please enter a name for your plan!", severity="error")
                return

            try:
                # Set the plan name
                self.plan_obj.name = plan_name

                # Save the plan
                filepath = plan_storage.save_plan(self.plan_obj)

                self.notify(f"Plan saved successfully to {filepath.name}!", severity="information")
                self.app.pop_screen()
            except Exception as e:
                self.notify(f"Error saving plan: {e}", severity="error")

        elif event.button.id == "btn_cancel":
            self.app.pop_screen()

    def action_cancel(self) -> None:
        """Cancel and return."""
        self.app.pop_screen()


class LoadPlanScreen(Screen):
    """Screen for loading a saved plan."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
    ]

    def compose(self) -> ComposeResult:
        """Create the load plan UI."""
        yield Header()

        with VerticalScroll(id="load_scroll"):
            yield Static("[bold cyan]Load a Saved Plan[/bold cyan]", id="load_title")
            yield Static("")

            # Get list of saved plans
            saved_plans = plan_storage.list_saved_plans()

            if not saved_plans:
                yield Static("[yellow]No saved plans found.[/yellow]")
                yield Static("")
                yield Button("Back to Main Menu", id="btn_back", variant="default")
            else:
                yield Static(f"[dim]Found {len(saved_plans)} saved plan(s)[/dim]")
                yield Static("")

                # Create a button for each saved plan
                for idx, plan_info in enumerate(saved_plans):
                    plan_name = plan_info['name']
                    total = plan_info['total']
                    daily = plan_info['daily']
                    time = plan_info['time']
                    created = plan_info['created_date']
                    created_str = created.strftime("%Y-%m-%d %H:%M") if created else "Unknown"

                    yield Button(
                        f"{plan_name}\n{total:,.0f} words | {daily:,.0f}/day | {time:.0f} days | Created: {created_str}",
                        id=f"btn_load_{idx}",
                        variant="primary"
                    )
                    yield Static("")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn_back":
            self.app.pop_screen()
        elif button_id.startswith("btn_load_"):
            # Extract index
            idx = int(button_id.split("_")[-1])

            # Get saved plans list
            saved_plans = plan_storage.list_saved_plans()

            if idx < len(saved_plans):
                plan_info = saved_plans[idx]
                filepath = plan_info['path']

                try:
                    # Load the plan
                    loaded_plan = plan_storage.load_plan(filepath)

                    self.notify(f"Loaded plan: {loaded_plan.name}", severity="information")

                    # Show results screen with loaded plan
                    self.app.pop_screen()  # Close load screen
                    self.app.push_screen(ResultsScreen(loaded_plan))

                except Exception as e:
                    self.notify(f"Error loading plan: {e}", severity="error")

    def action_back(self) -> None:
        """Go back."""
        self.app.pop_screen()


class WordPlannerApp(App):
    """Main Textual application for word planning."""

    CSS = """
    #main_container {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    #title {
        text-align: center;
        width: 100%;
        padding: 1;
        text-style: bold;
    }

    #subtitle {
        text-align: center;
        width: 100%;
        padding: 1;
    }

    #menu_buttons {
        width: 60;
        height: auto;
        align: center middle;
    }

    #menu_buttons Button {
        width: 100%;
        margin: 1 0;
    }

    #input_container {
        width: 80;
        height: auto;
        align: center middle;
        padding: 2;
    }

    #input_title {
        text-align: center;
        width: 100%;
        padding: 1;
        text-style: bold;
    }

    Input {
        width: 100%;
        margin: 0 0 1 0;
    }

    Label {
        width: 100%;
        padding: 1 0 0 0;
    }

    #button_row {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1 0;
    }

    #button_row Button {
        margin: 0 1;
    }

    #results_container {
        width: 80;
        height: auto;
        align: center middle;
        padding: 2;
    }

    #results_title {
        text-align: center;
        width: 100%;
        padding: 1;
        text-style: bold;
    }

    #calendar_buttons {
        width: 50;
        height: auto;
        align: center middle;
    }

    #calendar_buttons Button {
        width: 100%;
        margin: 1 0;
    }

    #date_container {
        width: 80;
        height: auto;
        align: center middle;
        padding: 2;
    }

    #date_title {
        text-align: center;
        width: 100%;
        padding: 1;
        text-style: bold;
    }

    #date_button_row {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1 0;
    }

    #date_button_row Button {
        margin: 0 1;
    }

    #save_container {
        width: 80;
        height: auto;
        align: center middle;
        padding: 2;
    }

    #save_title {
        text-align: center;
        width: 100%;
        padding: 1;
        text-style: bold;
    }

    #save_button_row {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1 0;
    }

    #save_button_row Button {
        margin: 0 1;
    }

    #load_scroll {
        width: 100%;
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
    }

    #load_title {
        text-align: center;
        width: 100%;
        padding: 1;
        text-style: bold;
    }

    #load_scroll Button {
        width: 90%;
        margin: 0 5;
        height: auto;
        min-height: 5;
    }

    #calendar_container {
        width: 100%;
        height: 100%;
        padding: 2;
    }

    #calendar_content {
        width: 100%;
        height: 100%;
        padding: 2;
    }

    #scroll_hint {
        width: 100%;
        text-align: center;
        padding: 0 0 1 0;
        background: $panel;
    }

    #calendar_scroll {
        width: 100%;
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
    }

    .calendar-summary {
        width: 100%;
        padding: 1 0;
        text-align: center;
    }

    .month-title {
        width: 100%;
        padding: 2 0 1 0;
        text-align: center;
        text-style: bold;
    }

    .section-title {
        width: 100%;
        padding: 2 0 1 0;
        text-align: center;
        text-style: bold;
    }

    MonthlyCalendarWidget {
        width: 100%;
        height: auto;
    }

    WeeklySummaryWidget {
        width: 100%;
        height: auto;
    }

    MilestonesWidget {
        width: 100%;
        height: auto;
    }

    .month-table {
        width: 100%;
        height: auto;
        margin: 0 0 2 0;
    }

    .weekly-table {
        width: 100%;
        height: auto;
        margin: 0 0 2 0;
    }

    .milestones-table {
        width: 100%;
        height: auto;
        margin: 0 0 2 0;
    }

    DataTable {
        height: auto;
    }
    """

    BINDINGS = [
        Binding("q", "quit_app", "Quit", show=False),
    ]

    def on_mount(self) -> None:
        """Show the main menu when app starts."""
        self.push_screen(MainMenuScreen())

    def action_quit_app(self) -> None:
        """Quit the application."""
        self.exit()


def main():
    """Run the Textual app."""
    app = WordPlannerApp()
    app.run()


if __name__ == "__main__":
    main()
