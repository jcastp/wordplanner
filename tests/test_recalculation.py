#!/usr/bin/env python3
"""Test script for the recalculation feature."""

import datetime
from datetime import timedelta
import plan

# Create a test plan
print("Creating test plan...")
p = plan.Plan(
    name="Test Recalculation",
    total=10000,
    daily=1000,
    time=10,
    start_date=datetime.datetime(2025, 11, 1)
)

print(f"Initial plan:")
print(f"  Total: {p.total:,.0f} words")
print(f"  Daily: {p.daily:,.0f} words")
print(f"  Time: {p.time:.0f} days")
print(f"  Start date: {p.start_date.strftime('%Y-%m-%d')}")

# Record some progress (simulate being ahead)
print("\nRecording progress for first 3 days (exceeding targets)...")
p.record_progress(datetime.datetime(2025, 11, 1), 1200)  # Day 1: +200
p.record_progress(datetime.datetime(2025, 11, 2), 1100)  # Day 2: +100
p.record_progress(datetime.datetime(2025, 11, 3), 1300)  # Day 3: +300

words_completed = p.get_total_written()
print(f"Words completed: {words_completed:,.0f} (expected: 3000, actual: 3600)")

# Recalculate from day 4 onwards
print("\nRecalculating plan from 2025-11-04...")
result = p.recalculate_from_progress(as_of_date=datetime.datetime(2025, 11, 4))

if result and result['success']:
    print("✓ Recalculation successful!")
    print(f"  Words remaining: {result['words_remaining']:,.0f} words")
    print(f"  Remaining days: {result['remaining_writing_days']}")
    print(f"  Old daily target: {result['old_daily']:,.0f} words")
    print(f"  New daily target: {result['new_daily']:,.0f} words")

    # Verify the math
    expected_remaining = p.total - words_completed
    expected_new_daily = expected_remaining / result['remaining_writing_days']

    print(f"\nVerification:")
    print(f"  Expected remaining: {expected_remaining:,.0f} words")
    print(f"  Expected new daily: {expected_new_daily:,.0f} words")
    print(f"  Match: {abs(result['new_daily'] - expected_new_daily) < 0.01}")
else:
    print("✗ Recalculation failed!")
    if result:
        print(f"  Reason: {result.get('reason')}")

# Test case 2: Behind schedule
print("\n" + "="*60)
print("Test Case 2: Behind schedule")
print("="*60)

p2 = plan.Plan(
    name="Test Behind",
    total=10000,
    daily=1000,
    time=10,
    start_date=datetime.datetime(2025, 11, 1)
)

# Record progress (falling behind)
print("Recording progress for first 3 days (behind targets)...")
p2.record_progress(datetime.datetime(2025, 11, 1), 800)   # Day 1: -200
p2.record_progress(datetime.datetime(2025, 11, 2), 900)   # Day 2: -100
p2.record_progress(datetime.datetime(2025, 11, 3), 700)   # Day 3: -300

words_completed2 = p2.get_total_written()
print(f"Words completed: {words_completed2:,.0f} (expected: 3000, actual: 2400)")

result2 = p2.recalculate_from_progress(as_of_date=datetime.datetime(2025, 11, 4))

if result2 and result2['success']:
    print("✓ Recalculation successful!")
    print(f"  Words remaining: {result2['words_remaining']:,.0f} words")
    print(f"  Remaining days: {result2['remaining_writing_days']}")
    print(f"  Old daily target: {result2['old_daily']:,.0f} words")
    print(f"  New daily target: {result2['new_daily']:,.0f} words")

    # Verify increase
    daily_increase = result2['new_daily'] - result2['old_daily']
    print(f"  Daily target increased by: {daily_increase:,.0f} words")

# Test case 3: With spare days
print("\n" + "="*60)
print("Test Case 3: With spare days")
print("="*60)

p3 = plan.Plan(
    name="Test Spare Days",
    total=10000,
    daily=1000,
    time=10,
    start_date=datetime.datetime(2025, 11, 1)
)

# Add a spare day
p3.spare_days_dates.append(datetime.datetime(2025, 11, 6))

print(f"Total days: {p3.time:.0f} writing days + {p3.spare_days} spare days")

# Record progress for first 2 days
p3.record_progress(datetime.datetime(2025, 11, 1), 1000)
p3.record_progress(datetime.datetime(2025, 11, 2), 1000)

result3 = p3.recalculate_from_progress(as_of_date=datetime.datetime(2025, 11, 3))

if result3 and result3['success']:
    print("✓ Recalculation successful!")
    print(f"  Words remaining: {result3['words_remaining']:,.0f} words")
    print(f"  Remaining days: {result3['remaining_writing_days']}")
    print(f"  Note: Spare days are excluded from remaining writing days")

print("\n" + "="*60)
print("All tests completed!")
print("="*60)
