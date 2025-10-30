#!/usr/bin/env python3
"""
Test script for multiple plans management functionality.

Tests:
1. Plan creation with new fields
2. Plan serialization/deserialization
3. Filtering by status, category, tags
4. Sorting plans
5. Active plan management
6. Archiving/unarchiving
7. Tag management
8. Category management
9. Plan comparison
10. Plan search
11. Plan statistics
"""

import datetime
import tempfile
from pathlib import Path

import plan
import plan_manager
import plan_storage
import config


def test_plan_fields():
    """Test Plan class with new multiple plans fields."""
    print("\n=== Testing Plan Fields ===")

    # Test with all new fields
    print("\n1. Creating plan with new fields:")
    p = plan.Plan(
        name="Test Novel",
        total=50000,
        daily=1000,
        time=50,
        status="active",
        tags=["fiction", "urgent"],
        category="novel",
        is_active=True
    )
    print(f"   ✓ Status: {p.status}")
    print(f"   ✓ Tags: {p.tags}")
    print(f"   ✓ Category: {p.category}")
    print(f"   ✓ Is active: {p.is_active}")

    # Test serialization
    print("\n2. Testing serialization:")
    plan_dict = p.to_dict()
    assert 'status' in plan_dict
    assert 'tags' in plan_dict
    assert 'category' in plan_dict
    assert 'is_active' in plan_dict
    assert 'last_modified' in plan_dict
    print("   ✓ All new fields present in dictionary")

    # Test deserialization
    print("\n3. Testing deserialization:")
    p2 = plan.Plan.from_dict(plan_dict)
    assert p2.status == p.status
    assert p2.tags == p.tags
    assert p2.category == p.category
    assert p2.is_active == p.is_active
    print("   ✓ All fields correctly restored")

    # Test backward compatibility (old plans without new fields)
    print("\n4. Testing backward compatibility:")
    old_plan_dict = {
        'name': 'Old Plan',
        'daily': 500,
        'total': 10000,
        'time': 20,
        'start_date': datetime.datetime.now().isoformat()
    }
    p3 = plan.Plan.from_dict(old_plan_dict)
    assert p3.status == "active"  # Default value
    assert p3.tags == []  # Default value
    assert p3.category is None  # Default value
    assert p3.is_active == False  # Default value
    print("   ✓ Old plan format loads with defaults")


def test_filtering():
    """Test plan filtering functionality."""
    print("\n\n=== Testing Plan Filtering ===")

    # Create test plans
    plans = [
        plan.Plan(name="Novel 1", total=50000, status="active", category="novel", tags=["fiction"]),
        plan.Plan(name="Blog 1", total=2000, status="active", category="blog", tags=["tech"]),
        plan.Plan(name="Novel 2", total=80000, status="archived", category="novel", tags=["fiction", "scifi"]),
        plan.Plan(name="Article", total=5000, status="completed", category="article", tags=["tech"]),
    ]

    # Test filter by status
    print("\n1. Filter by status:")
    active = plan_manager.filter_plans_by_status(plans, "active")
    print(f"   ✓ Active plans: {len(active)} (expected 2)")
    assert len(active) == 2

    archived = plan_manager.filter_plans_by_status(plans, "archived")
    print(f"   ✓ Archived plans: {len(archived)} (expected 1)")
    assert len(archived) == 1

    # Test filter by category
    print("\n2. Filter by category:")
    novels = plan_manager.filter_plans_by_category(plans, "novel")
    print(f"   ✓ Novel plans: {len(novels)} (expected 2)")
    assert len(novels) == 2

    # Test filter by tag
    print("\n3. Filter by tag:")
    fiction = plan_manager.filter_plans_by_tag(plans, "fiction")
    print(f"   ✓ Fiction tagged plans: {len(fiction)} (expected 2)")
    assert len(fiction) == 2

    tech = plan_manager.filter_plans_by_tag(plans, "tech")
    print(f"   ✓ Tech tagged plans: {len(tech)} (expected 2)")
    assert len(tech) == 2


def test_sorting():
    """Test plan sorting functionality."""
    print("\n\n=== Testing Plan Sorting ===")

    # Create test plans with different dates
    base_date = datetime.datetime(2025, 1, 1)
    plans = [
        plan.Plan(name="Charlie", total=50000, created_date=base_date + datetime.timedelta(days=2)),
        plan.Plan(name="Alice", total=30000, created_date=base_date),
        plan.Plan(name="Bob", total=40000, created_date=base_date + datetime.timedelta(days=1)),
    ]

    # Test sort by name
    print("\n1. Sort by name:")
    sorted_plans = plan_manager.sort_plans(plans, sort_by="name", reverse=False)
    names = [p.name for p in sorted_plans]
    print(f"   ✓ Order: {names}")
    assert names == ["Alice", "Bob", "Charlie"]

    # Test sort by created date
    print("\n2. Sort by creation date (newest first):")
    sorted_plans = plan_manager.sort_plans(plans, sort_by="created", reverse=True)
    names = [p.name for p in sorted_plans]
    print(f"   ✓ Order: {names}")
    assert names == ["Charlie", "Bob", "Alice"]


def test_active_plan_management():
    """Test active plan setting and clearing."""
    print("\n\n=== Testing Active Plan Management ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Override save directory
        original_dir = config.SAVE_DIRECTORY
        config.SAVE_DIRECTORY = tmpdir

        try:
            # Create and save test plans
            print("\n1. Creating test plans:")
            p1 = plan.Plan(name="Plan 1", total=10000, daily=500, time=20, start_date=datetime.datetime.now())
            p2 = plan.Plan(name="Plan 2", total=20000, daily=1000, time=20, start_date=datetime.datetime.now())

            path1 = plan_storage.save_plan(p1)
            path2 = plan_storage.save_plan(p2)
            print(f"   ✓ Created 2 plans")

            # Set active plan
            print("\n2. Setting active plan:")
            result = plan_manager.set_active_plan(path1)
            assert result == True
            print(f"   ✓ Set Plan 1 as active")

            # Verify active plan
            active = plan_manager.get_active_plan()
            assert active is not None
            assert active.name == "Plan 1"
            print(f"   ✓ Retrieved active plan: {active.name}")

            # Switch active plan
            print("\n3. Switching active plan:")
            result = plan_manager.set_active_plan(path2)
            assert result == True
            active = plan_manager.get_active_plan()
            assert active.name == "Plan 2"
            print(f"   ✓ Switched to Plan 2")

            # Clear active plan
            print("\n4. Clearing active plan:")
            result = plan_manager.clear_active_plan()
            assert result == True
            active = plan_manager.get_active_plan()
            assert active is None
            print(f"   ✓ Active plan cleared")

        finally:
            config.SAVE_DIRECTORY = original_dir


def test_archive_operations():
    """Test archiving, unarchiving, and completion."""
    print("\n\n=== Testing Archive Operations ===")

    # Test archive
    print("\n1. Archiving plan:")
    p = plan.Plan(name="Test Plan", total=10000, status="active", is_active=True)
    result = plan_manager.archive_plan(p)
    assert p.status == "archived"
    assert p.is_active == False  # Should clear active flag
    print(f"   ✓ Plan archived, status: {p.status}")

    # Test unarchive
    print("\n2. Unarchiving plan:")
    result = plan_manager.unarchive_plan(p)
    assert p.status == "active"
    print(f"   ✓ Plan unarchived, status: {p.status}")

    # Test mark completed
    print("\n3. Marking plan as completed:")
    p.is_active = True
    result = plan_manager.mark_plan_completed(p)
    assert p.status == "completed"
    assert p.is_active == False  # Should clear active flag
    print(f"   ✓ Plan marked as completed")


def test_tag_management():
    """Test tag adding and removing."""
    print("\n\n=== Testing Tag Management ===")

    p = plan.Plan(name="Test Plan", total=10000, tags=["existing"])

    # Test add tag
    print("\n1. Adding tags:")
    result = plan_manager.add_tag_to_plan(p, "new-tag")
    assert "new-tag" in p.tags
    print(f"   ✓ Added tag: {p.tags}")

    # Test duplicate tag
    result = plan_manager.add_tag_to_plan(p, "new-tag")
    assert p.tags.count("new-tag") == 1  # Should not add duplicate
    print(f"   ✓ Duplicate tag not added")

    # Test remove tag
    print("\n2. Removing tag:")
    result = plan_manager.remove_tag_from_plan(p, "new-tag")
    assert "new-tag" not in p.tags
    print(f"   ✓ Tag removed: {p.tags}")


def test_category_management():
    """Test category setting."""
    print("\n\n=== Testing Category Management ===")

    p = plan.Plan(name="Test Plan", total=10000)

    # Test set category
    print("\n1. Setting category:")
    result = plan_manager.set_plan_category(p, "novel")
    assert p.category == "novel"
    print(f"   ✓ Category set: {p.category}")

    # Test invalid category
    print("\n2. Testing invalid category:")
    result = plan_manager.set_plan_category(p, "invalid-category")
    assert result == False
    assert p.category == "novel"  # Should remain unchanged
    print(f"   ✓ Invalid category rejected")

    # Test remove category
    print("\n3. Removing category:")
    result = plan_manager.set_plan_category(p, None)
    assert p.category is None
    print(f"   ✓ Category removed")


def test_plan_comparison():
    """Test plan comparison functionality."""
    print("\n\n=== Testing Plan Comparison ===")

    # Create test plans with some progress
    p1 = plan.Plan(name="Plan 1", total=10000, daily=500, time=20, start_date=datetime.datetime.now())
    p1.record_progress(datetime.datetime.now(), 1000)

    p2 = plan.Plan(name="Plan 2", total=20000, daily=1000, time=20, start_date=datetime.datetime.now())
    p2.record_progress(datetime.datetime.now(), 500)

    # Test comparison
    print("\n1. Comparing plans:")
    comparison = plan_manager.compare_plans([p1, p2])

    assert comparison['summary']['total_plans'] == 2
    assert comparison['summary']['total_words'] == 30000
    print(f"   ✓ Total plans: {comparison['summary']['total_plans']}")
    print(f"   ✓ Total words: {comparison['summary']['total_words']:,.0f}")
    print(f"   ✓ Average daily: {comparison['summary']['avg_daily']:,.0f}")

    # Verify individual plan data
    assert len(comparison['plans']) == 2
    assert comparison['plans'][0]['name'] == "Plan 1"
    assert comparison['plans'][0]['written'] == 1000
    print(f"   ✓ Individual plan data included")


def test_plan_search():
    """Test plan search functionality."""
    print("\n\n=== Testing Plan Search ===")

    # Create test plans
    plans_data = [
        plan.Plan(name="My Novel Project", total=50000, category="novel", tags=["fiction"]),
        plan.Plan(name="Blog Series", total=10000, category="blog", tags=["tech", "tutorial"]),
        plan.Plan(name="Another Novel", total=60000, category="novel", tags=["scifi"]),
    ]

    # Mock get_all_plans
    original_get_all = plan_manager.get_all_plans
    plan_manager.get_all_plans = lambda: plans_data

    try:
        # Test search by name
        print("\n1. Search by name:")
        results = plan_manager.search_plans("novel")
        print(f"   ✓ Found {len(results)} plans with 'novel' in name (expected 2)")
        assert len(results) == 2

        # Test search by category
        print("\n2. Search by category:")
        results = plan_manager.search_plans("blog")
        print(f"   ✓ Found {len(results)} plans with 'blog' category (expected 1)")
        assert len(results) == 1

        # Test search by tag
        print("\n3. Search by tag:")
        results = plan_manager.search_plans("tech")
        print(f"   ✓ Found {len(results)} plans with 'tech' tag (expected 1)")
        assert len(results) == 1

    finally:
        plan_manager.get_all_plans = original_get_all


def test_plan_statistics():
    """Test plan statistics functionality."""
    print("\n\n=== Testing Plan Statistics ===")

    # Create test plans
    plans_data = [
        plan.Plan(name="Plan 1", total=10000, status="active", category="novel"),
        plan.Plan(name="Plan 2", total=20000, status="active", category="blog"),
        plan.Plan(name="Plan 3", total=30000, status="archived", category="novel"),
        plan.Plan(name="Plan 4", total=40000, status="completed", category="article"),
    ]

    # Add some progress to plans
    plans_data[0].record_progress(datetime.datetime.now(), 5000)
    plans_data[1].record_progress(datetime.datetime.now(), 10000)

    # Mock both get_all_plans and get_plans_by_status
    original_get_all = plan_manager.get_all_plans
    original_get_by_status = plan_manager.get_plans_by_status

    plan_manager.get_all_plans = lambda: plans_data

    def mock_get_plans_by_status():
        return {
            'active': [p for p in plans_data if p.status == 'active'],
            'archived': [p for p in plans_data if p.status == 'archived'],
            'completed': [p for p in plans_data if p.status == 'completed']
        }

    plan_manager.get_plans_by_status = mock_get_plans_by_status

    try:
        print("\n1. Getting overall statistics:")
        stats = plan_manager.get_plan_statistics()

        assert stats['total_plans'] == 4
        assert stats['active_plans'] == 2
        assert stats['archived_plans'] == 1
        assert stats['completed_plans'] == 1
        assert stats['total_word_goal'] == 100000
        assert stats['total_words_written'] == 15000

        print(f"   ✓ Total plans: {stats['total_plans']}")
        print(f"   ✓ Active plans: {stats['active_plans']}")
        print(f"   ✓ Total word goal: {stats['total_word_goal']:,.0f}")
        print(f"   ✓ Total written: {stats['total_words_written']:,.0f}")

    finally:
        plan_manager.get_all_plans = original_get_all
        plan_manager.get_plans_by_status = original_get_by_status


def main():
    """Run all tests."""
    print("=" * 70)
    print("MULTIPLE PLANS MANAGEMENT TEST SUITE")
    print("=" * 70)

    try:
        test_plan_fields()
        test_filtering()
        test_sorting()
        test_active_plan_management()
        test_archive_operations()
        test_tag_management()
        test_category_management()
        test_plan_comparison()
        test_plan_search()
        test_plan_statistics()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)

    except AssertionError as e:
        print(f"\n\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
