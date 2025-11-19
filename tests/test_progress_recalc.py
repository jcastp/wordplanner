#!/usr/bin/env python3
"""Test that recalculation works correctly from progress workflow."""

import datetime
from datetime import timedelta
import plan

print("=" * 70)
print("Testing Progress-Based Recalculation")
print("=" * 70)

# Create a test plan starting today
today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
start_date = today - timedelta(days=5)  # Started 5 days ago

p = plan.Plan(
    name="Test Progress Recalc",
    total=10000,
    daily=1000,
    time=10,
    start_date=start_date
)

print(f"\nInitial Plan:")
print(f"  Start: {p.start_date.strftime('%Y-%m-%d')}")
print(f"  Total: {p.total:,.0f} words")
print(f"  Daily: {p.daily:,.0f} words")
print(f"  Time: {p.time:.0f} days")

# Simulate progress for days 1-5 (behind schedule)
print(f"\nSimulating progress for first 5 days (behind schedule)...")
for i in range(5):
    date = start_date + timedelta(days=i)
    words = 800  # 200 words behind each day
    p.record_progress(date, words)
    print(f"  Day {i+1} ({date.strftime('%Y-%m-%d')}): {words} words")

words_completed = p.get_total_written()
expected_by_now = 1000 * 5
behind_by = expected_by_now - words_completed

print(f"\nProgress Summary:")
print(f"  Expected by now: {expected_by_now:,.0f} words")
print(f"  Actually written: {words_completed:,.0f} words")
print(f"  Behind by: {behind_by:,.0f} words")

# Test recalculation from tomorrow
tomorrow = today + timedelta(days=1)
print(f"\nRecalculating from tomorrow ({tomorrow.strftime('%Y-%m-%d')})...")

result = p.recalculate_from_progress(as_of_date=tomorrow)

if result and result['success']:
    print("✓ Recalculation successful!")
    print(f"\nResults:")
    print(f"  Words completed: {result['words_completed']:,.0f}")
    print(f"  Words remaining: {result['words_remaining']:,.0f}")
    print(f"  Remaining days: {result['remaining_writing_days']}")
    print(f"  Old daily target: {result['old_daily']:,.0f}")
    print(f"  New daily target: {result['new_daily']:,.0f}")

    daily_increase = result['new_daily'] - result['old_daily']
    print(f"  Daily increase: {daily_increase:,.0f} words ({daily_increase/result['old_daily']*100:.1f}%)")

    # Verify the math
    print(f"\nVerification:")
    print(f"  Remaining words / remaining days = {result['words_remaining']} / {result['remaining_writing_days']}")
    print(f"  = {result['words_remaining'] / result['remaining_writing_days']:.2f}")
    print(f"  Match: {abs(result['new_daily'] - result['words_remaining']/result['remaining_writing_days']) < 0.01}")

    # Test that past days are not affected
    print(f"\nPast days check:")
    for i in range(5):
        date = start_date + timedelta(days=i)
        daily_goal = p.get_daily_goal(date=date)
        print(f"  Day {i+1} ({date.strftime('%Y-%m-%d')}): goal = {daily_goal:,.0f} words (should be 1000)")

    # Check future days use new target
    print(f"\nFuture days check:")
    for i in range(5, 8):
        date = start_date + timedelta(days=i)
        daily_goal = p.get_daily_goal(date=date)
        print(f"  Day {i+1} ({date.strftime('%Y-%m-%d')}): goal = {daily_goal:,.0f} words (should be {result['new_daily']:.0f})")

else:
    print("✗ Recalculation failed!")
    if result:
        print(f"  Reason: {result.get('reason')}")

print("\n" + "=" * 70)
print("Test completed!")
print("=" * 70)
