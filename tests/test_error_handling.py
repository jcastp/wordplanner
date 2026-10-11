#!/usr/bin/env python3
"""
Test script for error handling improvements in planeapalabras.

Tests:
1. Division by zero in plan calculations
2. Negative number validation in Plan.__init__
3. Corrupted JSON handling in Plan.from_json
4. Invalid data in Plan.from_dict
5. File I/O error simulation
"""

import datetime
import json
import tempfile
from pathlib import Path

# Import the modules to test
import plan
import plan_storage


def test_division_by_zero():
    """Test that division by zero is properly handled."""
    print("\n=== Testing Division by Zero ===")

    # Test calculate_daily with time=0
    print("\n1. Testing calculate_daily() with time=0:")
    p = plan.Plan(total=50000, time=0)
    try:
        p.calculate_daily()
        print("   ❌ FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"   ✓ PASSED: Raised ValueError: {e}")

    # Test calculate_time with daily=0
    print("\n2. Testing calculate_time() with daily=0:")
    p = plan.Plan(total=50000, daily=0)
    try:
        p.calculate_time()
        print("   ❌ FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"   ✓ PASSED: Raised ValueError: {e}")


def test_negative_numbers():
    """Test that negative numbers are properly rejected."""
    print("\n\n=== Testing Negative Number Validation ===")

    test_cases = [
        ("daily", {"daily": -1000}),
        ("total", {"total": -50000}),
        ("time", {"time": -30}),
        ("weekend_daily", {"weekend_daily": -500}),
    ]

    for field_name, kwargs in test_cases:
        print(f"\n{len([t for t in test_cases if test_cases.index(t) < test_cases.index((field_name, kwargs))])+1}. Testing negative {field_name}:")
        try:
            p = plan.Plan(**kwargs)
            print(f"   ❌ FAILED: Should have raised ValueError for {field_name}={kwargs[field_name]}")
        except ValueError as e:
            print(f"   ✓ PASSED: Rejected negative {field_name}: {e}")


def test_corrupted_json():
    """Test that corrupted JSON is properly handled."""
    print("\n\n=== Testing Corrupted JSON Handling ===")

    # Test malformed JSON
    print("\n1. Testing malformed JSON:")
    bad_json = '{"name": "test", "daily": 1000, invalid syntax here}'
    try:
        p = plan.Plan.from_json(bad_json)
        print("   ❌ FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"   ✓ PASSED: Caught corrupted JSON: {e}")

    # Test empty JSON
    print("\n2. Testing empty string:")
    try:
        p = plan.Plan.from_json("")
        print("   ❌ FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"   ✓ PASSED: Rejected empty JSON: {e}")

    # Test non-JSON string
    print("\n3. Testing non-JSON string:")
    try:
        p = plan.Plan.from_json("not json at all")
        print("   ❌ FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"   ✓ PASSED: Rejected non-JSON: {e}")


def test_invalid_plan_data():
    """Test that invalid plan data is properly handled."""
    print("\n\n=== Testing Invalid Plan Data ===")

    # Test invalid start_date format
    print("\n1. Testing invalid start_date format:")
    bad_data = {
        'name': 'Test Plan',
        'daily': 1000,
        'total': 50000,
        'time': 50,
        'start_date': 'not-a-valid-date'
    }
    try:
        p = plan.Plan.from_dict(bad_data)
        print("   ❌ FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"   ✓ PASSED: Caught invalid date format: {e}")

    # Test invalid numeric values
    print("\n2. Testing non-numeric values:")
    bad_data = {
        'name': 'Test Plan',
        'daily': 'not a number',
        'total': 50000,
        'time': 50,
    }
    try:
        p = plan.Plan.from_dict(bad_data)
        print("   ❌ FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"   ✓ PASSED: Caught invalid numeric value: {e}")

    # Test non-dict input to from_dict
    print("\n3. Testing non-dictionary input:")
    try:
        p = plan.Plan.from_dict("not a dictionary")
        print("   ❌ FAILED: Should have raised TypeError")
    except TypeError as e:
        print(f"   ✓ PASSED: Rejected non-dict input: {e}")


def test_file_operations():
    """Test file I/O error handling."""
    print("\n\n=== Testing File I/O Error Handling ===")

    # Test loading non-existent file
    print("\n1. Testing load_plan() with non-existent file:")
    fake_path = Path("/nonexistent/path/to/plan.json")
    try:
        p = plan_storage.load_plan(fake_path)
        print("   ❌ FAILED: Should have raised FileNotFoundError")
    except FileNotFoundError as e:
        print(f"   ✓ PASSED: Caught missing file: {e}")

    # Test loading empty file
    print("\n2. Testing load_plan() with empty file:")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        empty_file = Path(f.name)
        # Write nothing

    try:
        p = plan_storage.load_plan(empty_file)
        print("   ❌ FAILED: Should have raised ValueError for empty file")
    except ValueError as e:
        print(f"   ✓ PASSED: Rejected empty file: {e}")
    finally:
        empty_file.unlink()

    # Test loading corrupted JSON file
    print("\n3. Testing load_plan() with corrupted JSON file:")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        corrupted_file = Path(f.name)
        f.write('{"name": "test", invalid json')

    try:
        p = plan_storage.load_plan(corrupted_file)
        print("   ❌ FAILED: Should have raised ValueError for corrupted JSON")
    except ValueError as e:
        print(f"   ✓ PASSED: Caught corrupted JSON file: {e}")
    finally:
        corrupted_file.unlink()


def test_pattern_edge_cases():
    """Test pattern calculation edge cases."""
    print("\n\n=== Testing Pattern Calculation Edge Cases ===")

    # Test pattern with zero daily goal
    print("\n1. Testing pattern calculation with daily=0:")
    p = plan.Plan(daily=0, total=0, time=10, start_date=datetime.datetime.now())
    try:
        goals = p.calculate_pattern_goals()
        if all(g == 0 for g in goals):
            print(f"   ✓ PASSED: Returned flat goals with zero values")
        else:
            print(f"   ⚠ WARNING: Non-zero goals returned: {goals[:3]}...")
    except Exception as e:
        print(f"   ❌ FAILED: Unexpected error: {e}")


def test_calculation_method_errors():
    """Test that calculation methods validate inputs properly."""
    print("\n\n=== Testing Calculation Method Validation ===")

    # Note: Negative values are now caught at Plan.__init__, which is even better!
    # Test that we can't even create Plans with invalid values

    # Test creating Plan with negative total for calculate_daily
    print("\n1. Testing Plan creation rejects negative total (for calculate_daily):")
    try:
        p = plan.Plan(total=-1000, time=30)
        print("   ❌ FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"   ✓ PASSED: Rejected at creation time: {e}")

    # Test creating Plan with negative total for calculate_time
    print("\n2. Testing Plan creation rejects negative total (for calculate_time):")
    try:
        p = plan.Plan(total=-1000, daily=100)
        print("   ❌ FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"   ✓ PASSED: Rejected at creation time: {e}")

    # Test creating Plan with negative daily for calculate_words
    print("\n3. Testing Plan creation rejects negative daily (for calculate_words):")
    try:
        p = plan.Plan(daily=-100, time=30)
        print("   ❌ FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"   ✓ PASSED: Rejected at creation time: {e}")

    # Test creating Plan with negative time for calculate_words
    print("\n4. Testing Plan creation rejects negative time (for calculate_words):")
    try:
        p = plan.Plan(daily=100, time=-30)
        print("   ❌ FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"   ✓ PASSED: Rejected at creation time: {e}")


def main():
    """Run all error handling tests."""
    print("=" * 60)
    print("ERROR HANDLING TEST SUITE")
    print("=" * 60)

    try:
        test_division_by_zero()
        test_negative_numbers()
        test_corrupted_json()
        test_invalid_plan_data()
        test_file_operations()
        test_pattern_edge_cases()
        test_calculation_method_errors()

        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
        print("\nNote: Review any ❌ FAILED or ⚠ WARNING messages above.")

    except Exception as e:
        print(f"\n\n❌ TEST SUITE FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
