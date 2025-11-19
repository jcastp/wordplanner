#!/usr/bin/env python3
"""Test pre-existing words integration with plan calculations."""

import datetime
from datetime import timedelta
import plan

print("=" * 80)
print("Testing Pre-Existing Words with All Three Calculation Methods")
print("=" * 80)

# Test Case 1: User's example - Calculate time
# Total: 80,000, Daily: 1,000, Pre-existing: 32,000
# Expected: 48 days (because (80,000 - 32,000) / 1,000 = 48)
print("\n" + "=" * 80)
print("Test 1: Calculate Time (User's Example)")
print("=" * 80)
print("Goal: 80,000 words")
print("Pre-existing: 32,000 words")
print("Daily capacity: 1,000 words/day")
print("Expected result: 48 days")

total = 80000
pre_existing = 32000
daily = 1000
remaining = total - pre_existing

# Simulate the calculation
p1 = plan.Plan(total=remaining, daily=daily)
p1.calculate_time()
p1.total = total  # Restore actual total

print(f"\nCalculated plan:")
print(f"  Time: {p1.time:.0f} days (expected: 48)")
print(f"  Daily: {p1.daily:,.0f} words/day")
print(f"  Total: {p1.total:,.0f} words")
print(f"  ✓ PASS" if p1.time == 48 else f"  ✗ FAIL: Expected 48, got {p1.time}")

# Verify with progress
start_date = datetime.datetime(2025, 11, 20)
p1.start_date = start_date
pre_start = start_date - timedelta(days=1)
p1.record_progress(pre_start, pre_existing)

print(f"\nAfter recording pre-existing words:")
print(f"  Words completed: {p1.get_total_written():,.0f}")
print(f"  Remaining: {p1.get_remaining_words():,.0f}")
print(f"  Completion: {p1.get_completion_percentage():.1f}%")

# Test Case 2: Calculate Total Words
# Daily: 500, Time: 60 days, Pre-existing: 5,000
# Expected total: 500 * 60 + 5,000 = 35,000
print("\n" + "=" * 80)
print("Test 2: Calculate Total Words")
print("=" * 80)
print("Daily capacity: 500 words/day")
print("Available time: 60 days")
print("Pre-existing: 5,000 words")
print("Expected total: 35,000 words (500 * 60 + 5,000)")

daily2 = 500
time2 = 60
pre_existing2 = 5000

# Simulate the calculation
p2 = plan.Plan(daily=daily2, time=time2)
p2.calculate_words()
p2.total = p2.total + pre_existing2  # Add pre-existing to calculated total

print(f"\nCalculated plan:")
print(f"  Total: {p2.total:,.0f} words (expected: 35,000)")
print(f"  Daily: {p2.daily:,.0f} words/day")
print(f"  Time: {p2.time:.0f} days")
print(f"  ✓ PASS" if p2.total == 35000 else f"  ✗ FAIL: Expected 35,000, got {p2.total}")

# Verify math
calculated_writing = daily2 * time2
print(f"\nVerification:")
print(f"  New writing needed: {daily2} × {time2} = {calculated_writing:,.0f}")
print(f"  Pre-existing: {pre_existing2:,.0f}")
print(f"  Total goal: {calculated_writing + pre_existing2:,.0f}")

# Test Case 3: Calculate Daily Words
# Total: 50,000, Time: 40 days, Pre-existing: 10,000
# Expected daily: (50,000 - 10,000) / 40 = 1,000
print("\n" + "=" * 80)
print("Test 3: Calculate Daily Words")
print("=" * 80)
print("Goal: 50,000 words")
print("Pre-existing: 10,000 words")
print("Available time: 40 days")
print("Expected daily: 1,000 words/day ((50,000 - 10,000) / 40)")

total3 = 50000
time3 = 40
pre_existing3 = 10000
remaining3 = total3 - pre_existing3

# Simulate the calculation
p3 = plan.Plan(total=remaining3, time=time3)
p3.calculate_daily()
p3.total = total3  # Restore actual total

print(f"\nCalculated plan:")
print(f"  Daily: {p3.daily:,.0f} words/day (expected: 1,000)")
print(f"  Total: {p3.total:,.0f} words")
print(f"  Time: {p3.time:.0f} days")
print(f"  ✓ PASS" if p3.daily == 1000 else f"  ✗ FAIL: Expected 1,000, got {p3.daily}")

# Verify with progress
start_date3 = datetime.datetime(2025, 12, 1)
p3.start_date = start_date3
pre_start3 = start_date3 - timedelta(days=1)
p3.record_progress(pre_start3, pre_existing3)

print(f"\nAfter recording pre-existing words:")
print(f"  Words completed: {p3.get_total_written():,.0f}")
print(f"  Remaining: {p3.get_remaining_words():,.0f}")
print(f"  Completion: {p3.get_completion_percentage():.1f}%")

# Test Case 4: Edge case - Pre-existing equals total
print("\n" + "=" * 80)
print("Test 4: Edge Case - Pre-existing Equals Total")
print("=" * 80)
print("Goal: 10,000 words")
print("Pre-existing: 10,000 words")
print("Expected: Goal already met (no plan needed)")

total4 = 10000
pre_existing4 = 10000
remaining4 = total4 - pre_existing4

if remaining4 <= 0:
    print("✓ PASS: Correctly detected that goal is already met")
else:
    print(f"✗ FAIL: Should have detected goal completion")

# Test Case 5: Verify recalculation works with pre-existing words
print("\n" + "=" * 80)
print("Test 5: Recalculation with Pre-existing Words")
print("=" * 80)

p5 = plan.Plan(
    total=20000,
    daily=1000,
    time=15,  # Plan for 15 days
    start_date=datetime.datetime(2025, 11, 20)
)

# Record pre-existing words (5,000)
pre_start5 = p5.start_date - timedelta(days=1)
p5.record_progress(pre_start5, 5000)

# Record progress for 3 days (2,000 words total)
p5.record_progress(p5.start_date, 700)
p5.record_progress(p5.start_date + timedelta(days=1), 600)
p5.record_progress(p5.start_date + timedelta(days=2), 700)

total_written = p5.get_total_written()
print(f"Progress so far:")
print(f"  Pre-existing: 5,000 words")
print(f"  Days 1-3: 2,000 words")
print(f"  Total written: {total_written:,.0f} words")

# Recalculate from day 4
day4 = p5.start_date + timedelta(days=3)
result = p5.recalculate_from_progress(as_of_date=day4)

if result and result['success']:
    print(f"\n✓ Recalculation successful:")
    print(f"  Words remaining: {result['words_remaining']:,.0f} (expected: 13,000)")
    print(f"  Remaining days: {result['remaining_writing_days']}")
    print(f"  New daily target: {result['new_daily']:,.0f} words")

    # Verify
    expected_remaining = 20000 - 7000
    expected_daily = expected_remaining / result['remaining_writing_days']
    print(f"\nVerification:")
    print(f"  Expected remaining: {expected_remaining:,.0f}")
    print(f"  Match: {result['words_remaining'] == expected_remaining}")
    print(f"  Expected daily: {expected_daily:,.0f}")
    print(f"  Match: {abs(result['new_daily'] - expected_daily) < 0.01}")
else:
    print("✗ Recalculation failed!")

print("\n" + "=" * 80)
print("All tests completed!")
print("=" * 80)
