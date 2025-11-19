#!/usr/bin/env python3
"""Test pre-existing words feature."""

import datetime
from datetime import timedelta
import plan

print("=" * 70)
print("Testing Pre-Existing Words Feature")
print("=" * 70)

# Create a test plan
start_date = datetime.datetime(2025, 11, 20)

p = plan.Plan(
    name="Test Pre-existing Words",
    total=10000,
    daily=1000,
    time=10,
    start_date=start_date
)

print(f"\nInitial Plan:")
print(f"  Total: {p.total:,.0f} words")
print(f"  Daily: {p.daily:,.0f} words")
print(f"  Time: {p.time:.0f} days")
print(f"  Start: {p.start_date.strftime('%Y-%m-%d')}")

# Simulate recording pre-existing words (3000 words)
pre_existing = 3000
pre_start_date = start_date - timedelta(days=1)

print(f"\nSimulating pre-existing words...")
print(f"  Pre-existing: {pre_existing:,.0f} words")
print(f"  Recorded on: {pre_start_date.strftime('%Y-%m-%d')} (day before start)")

p.record_progress(pre_start_date, pre_existing)

# Check the results
print(f"\nResults:")
print(f"  Total written: {p.get_total_written():,.0f} words")
print(f"  Completion: {p.get_completion_percentage():.1f}%")
print(f"  Remaining: {p.get_remaining_words():,.0f} words")

# Verify progress was recorded
if pre_start_date.strftime('%Y-%m-%d') in p.progress:
    print(f"  ✓ Progress recorded on {pre_start_date.strftime('%Y-%m-%d')}")
else:
    print(f"  ✗ Progress NOT recorded!")

# Test with recalculation
print("\n" + "=" * 70)
print("Testing Recalculation with Pre-existing Words")
print("=" * 70)

# Now simulate starting the plan
# Record progress for day 1 and 2
day1 = start_date
day2 = start_date + timedelta(days=1)

p.record_progress(day1, 1000)
p.record_progress(day2, 900)

print(f"\nProgress recorded:")
print(f"  Pre-existing: {pre_existing:,.0f} words")
print(f"  Day 1: 1,000 words")
print(f"  Day 2: 900 words")
print(f"  Total: {p.get_total_written():,.0f} words")

# Recalculate from day 3
day3 = start_date + timedelta(days=2)
print(f"\nRecalculating from day 3 ({day3.strftime('%Y-%m-%d')})...")

result = p.recalculate_from_progress(as_of_date=day3)

if result and result['success']:
    print("✓ Recalculation successful!")
    print(f"\nResults:")
    print(f"  Words completed: {result['words_completed']:,.0f}")
    print(f"  Words remaining: {result['words_remaining']:,.0f}")
    print(f"  Remaining days: {result['remaining_writing_days']}")
    print(f"  Old daily target: {result['old_daily']:,.0f}")
    print(f"  New daily target: {result['new_daily']:,.0f}")

    # Verify the math
    expected_completed = pre_existing + 1000 + 900
    print(f"\nVerification:")
    print(f"  Expected completed: {expected_completed:,.0f}")
    print(f"  Actual completed: {result['words_completed']:,.0f}")
    print(f"  Match: {result['words_completed'] == expected_completed}")

    remaining = p.total - expected_completed
    print(f"  Expected remaining: {remaining:,.0f}")
    print(f"  Actual remaining: {result['words_remaining']:,.0f}")
    print(f"  Match: {result['words_remaining'] == remaining}")

else:
    print("✗ Recalculation failed!")
    if result:
        print(f"  Reason: {result.get('reason')}")

print("\n" + "=" * 70)
print("Test completed!")
print("=" * 70)
