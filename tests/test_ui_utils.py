"""Tests for UI utility functions."""

import pytest
from io import StringIO
import sys
import ui_utils


class TestDisplayFunctions:
    """Test display helper functions."""

    def test_display_header(self, capsys):
        """Test display_header outputs correct format."""
        ui_utils.display_header("TEST HEADER")
        captured = capsys.readouterr()
        assert "=" * 50 in captured.out
        assert "TEST HEADER" in captured.out

    def test_display_header_custom_width(self, capsys):
        """Test display_header with custom width."""
        ui_utils.display_header("TEST", width=20)
        captured = capsys.readouterr()
        assert "=" * 20 in captured.out

    def test_display_section(self, capsys):
        """Test display_section outputs correct format."""
        ui_utils.display_section("TEST SECTION")
        captured = capsys.readouterr()
        assert "-" * 50 in captured.out
        assert "TEST SECTION" in captured.out

    def test_display_success(self, capsys):
        """Test display_success shows success message."""
        ui_utils.display_success("Operation completed")
        captured = capsys.readouterr()
        assert "✓" in captured.out
        assert "Operation completed" in captured.out

    def test_display_error(self, capsys):
        """Test display_error shows error message."""
        ui_utils.display_error("Something went wrong")
        captured = capsys.readouterr()
        assert "✗" in captured.out
        assert "Something went wrong" in captured.out

    def test_display_warning(self, capsys):
        """Test display_warning shows warning message."""
        ui_utils.display_warning("Be careful")
        captured = capsys.readouterr()
        assert "⚠" in captured.out
        assert "Be careful" in captured.out


class TestInputValidation:
    """Test input validation functions."""

    def test_get_menu_choice_valid(self, monkeypatch):
        """Test get_menu_choice with valid input."""
        monkeypatch.setattr('builtins.input', lambda _: "2")
        result = ui_utils.get_menu_choice("Choose: ", 1, 3)
        assert result == 2

    def test_get_menu_choice_boundary_min(self, monkeypatch):
        """Test get_menu_choice at minimum boundary."""
        monkeypatch.setattr('builtins.input', lambda _: "1")
        result = ui_utils.get_menu_choice("Choose: ", 1, 3)
        assert result == 1

    def test_get_menu_choice_boundary_max(self, monkeypatch):
        """Test get_menu_choice at maximum boundary."""
        monkeypatch.setattr('builtins.input', lambda _: "3")
        result = ui_utils.get_menu_choice("Choose: ", 1, 3)
        assert result == 3

    def test_get_integer_input_valid(self, monkeypatch):
        """Test get_integer_input with valid integer."""
        monkeypatch.setattr('builtins.input', lambda _: "42")
        result = ui_utils.get_integer_input("Enter number: ")
        assert result == 42

    def test_get_integer_input_with_min(self, monkeypatch):
        """Test get_integer_input with minimum value."""
        inputs = iter(["5", "10"])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        result = ui_utils.get_integer_input("Enter number: ", min_value=10)
        assert result == 10

    def test_get_integer_input_with_max(self, monkeypatch):
        """Test get_integer_input with maximum value."""
        inputs = iter(["100", "50"])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        result = ui_utils.get_integer_input("Enter number: ", max_value=50)
        assert result == 50

    def test_get_string_input_nonempty(self, monkeypatch):
        """Test get_string_input with non-empty string."""
        monkeypatch.setattr('builtins.input', lambda _: "test string")
        result = ui_utils.get_string_input("Enter text: ")
        assert result == "test string"

    def test_get_string_input_allows_empty(self, monkeypatch):
        """Test get_string_input allows empty when specified."""
        monkeypatch.setattr('builtins.input', lambda _: "")
        result = ui_utils.get_string_input("Enter text: ", allow_empty=True)
        assert result == ""


class TestYesNoPrompts:
    """Test yes/no prompt functions."""

    def test_get_yes_no_yes(self, monkeypatch):
        """Test get_yes_no returns True for 'yes'."""
        monkeypatch.setattr('builtins.input', lambda _: "yes")
        result = ui_utils.get_yes_no("Continue?")
        assert result is True

    def test_get_yes_no_y(self, monkeypatch):
        """Test get_yes_no returns True for 'y'."""
        monkeypatch.setattr('builtins.input', lambda _: "y")
        result = ui_utils.get_yes_no("Continue?")
        assert result is True

    def test_get_yes_no_no(self, monkeypatch):
        """Test get_yes_no returns False for 'no'."""
        monkeypatch.setattr('builtins.input', lambda _: "no")
        result = ui_utils.get_yes_no("Continue?")
        assert result is False

    def test_get_yes_no_n(self, monkeypatch):
        """Test get_yes_no returns False for 'n'."""
        monkeypatch.setattr('builtins.input', lambda _: "n")
        result = ui_utils.get_yes_no("Continue?")
        assert result is False

    def test_get_yes_no_default_yes(self, monkeypatch):
        """Test get_yes_no uses default 'y'."""
        monkeypatch.setattr('builtins.input', lambda _: "")
        result = ui_utils.get_yes_no("Continue?", default='y')
        assert result is True

    def test_get_yes_no_default_no(self, monkeypatch):
        """Test get_yes_no uses default 'n'."""
        monkeypatch.setattr('builtins.input', lambda _: "")
        result = ui_utils.get_yes_no("Continue?", default='n')
        assert result is False

    def test_confirm_action_yes(self, monkeypatch):
        """Test confirm_action returns True for yes."""
        monkeypatch.setattr('builtins.input', lambda _: "y")
        result = ui_utils.confirm_action("delete all files")
        assert result is True  # User confirmed with 'y'


class TestPositiveNumber:
    """Test get_positive_number function."""

    def test_get_positive_number_valid(self, monkeypatch):
        """Test get_positive_number with valid positive number."""
        monkeypatch.setattr('builtins.input', lambda _: "100")
        result = ui_utils.get_positive_number("Enter amount: ")
        assert result == 100.0

    def test_get_positive_number_float(self, monkeypatch):
        """Test get_positive_number with float."""
        monkeypatch.setattr('builtins.input', lambda _: "123.45")
        result = ui_utils.get_positive_number("Enter amount: ")
        assert abs(result - 123.45) < 0.01
