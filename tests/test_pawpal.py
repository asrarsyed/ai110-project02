"""Core tests for PawPal system: basic functionality, sorting, recurrence, and conflict detection."""

from datetime import date, timedelta

from pawpal_system import (
    Owner,
    Pet,
    Recurrence,
    Scheduler,
    ScheduleItem,
    Task,
    TimeWindow,
)


def test_task_mark_complete_sets_is_complete_true() -> None:
    task = Task(name="Feed", duration_minutes=15, priority=3)

    task.mark_complete()

    assert task.is_complete is True


def test_adding_task_to_pet_increases_task_count() -> None:
    pet = Pet(name="Mochi", species="cat")
    task = Task(name="Play", duration_minutes=20, priority=2)

    before = len(pet.get_tasks())
    pet.add_task(task)
    after = len(pet.get_tasks())

    assert after == before + 1


# ============================================================================
# SORTING CORRECTNESS TESTS
# ============================================================================


def test_schedule_items_returned_in_chronological_order() -> None:
    """Verify that generate_schedule returns tasks in chronological order by start time."""
    owner = Owner(name="Alex", available_time_minutes=200)
    pet = Pet(name="Max", species="dog")

    # Create tasks with different fixed times (out of order)
    task1 = Task(
        name="Afternoon walk", duration_minutes=30, priority=3, fixed_time_minute=720
    )  # 12:00
    task2 = Task(
        name="Morning feed", duration_minutes=15, priority=3, fixed_time_minute=480
    )  # 8:00
    task3 = Task(
        name="Evening play", duration_minutes=20, priority=3, fixed_time_minute=1080
    )  # 18:00

    pet.add_task(task1)
    pet.add_task(task2)
    pet.add_task(task3)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, schedule_date=date.today())
    schedule = scheduler.generate_schedule()

    # Should be sorted by start_minute
    assert len(schedule) == 3
    assert schedule[0].task.name == "Morning feed"
    assert schedule[0].start_minute == 480
    assert schedule[1].task.name == "Afternoon walk"
    assert schedule[1].start_minute == 720
    assert schedule[2].task.name == "Evening play"
    assert schedule[2].start_minute == 1080


def test_sort_by_time_prioritizes_correctly() -> None:
    """Verify that sort_by_time orders by: fixed time > critical > priority > duration."""
    owner = Owner(name="Alex", available_time_minutes=200)
    scheduler = Scheduler(owner=owner)

    # Create tasks to test sorting hierarchy
    task_fixed_early = Task(
        name="Fixed 8am", duration_minutes=30, priority=3, fixed_time_minute=480
    )
    task_fixed_late = Task(
        name="Fixed 10am", duration_minutes=30, priority=5, fixed_time_minute=600
    )
    task_critical = Task(name="Critical", duration_minutes=40, priority=3, is_critical=True)
    task_high_priority = Task(name="High priority", duration_minutes=50, priority=5)
    task_low_priority_short = Task(name="Low priority short", duration_minutes=10, priority=2)
    task_low_priority_long = Task(name="Low priority long", duration_minutes=60, priority=2)

    tasks = [
        task_low_priority_long,
        task_high_priority,
        task_fixed_late,
        task_critical,
        task_low_priority_short,
        task_fixed_early,
    ]

    sorted_tasks = scheduler.sort_by_time(tasks)

    # Expected order:
    # 1. Fixed times first (sorted by time)
    # 2. Then critical
    # 3. Then by priority (descending)
    # 4. Then by duration (ascending)
    assert sorted_tasks[0].name == "Fixed 8am"
    assert sorted_tasks[1].name == "Fixed 10am"
    assert sorted_tasks[2].name == "Critical"
    assert sorted_tasks[3].name == "High priority"
    assert sorted_tasks[4].name == "Low priority short"  # Shorter comes first
    assert sorted_tasks[5].name == "Low priority long"


# ============================================================================
# RECURRENCE LOGIC TESTS
# ============================================================================


def test_daily_task_reschedules_to_next_day_after_completion() -> None:
    """Confirm that marking a daily task complete and advancing creates a new task for the following day."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    today = date.today()
    daily_task = Task(
        name="Daily walk",
        duration_minutes=30,
        priority=5,
        recurrence=Recurrence.DAILY,
        next_due_date=today,
    )

    pet.add_task(daily_task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, schedule_date=today)

    # Mark task as complete
    daily_task.mark_complete()
    assert daily_task.is_complete is True

    # Advance the task
    scheduler.advance_recurring_tasks([daily_task])

    # Task should be reset and due tomorrow
    assert daily_task.is_complete is False
    assert daily_task.next_due_date == today + timedelta(days=1)


def test_weekly_task_reschedules_to_next_week() -> None:
    """Verify weekly recurring tasks advance by 7 days."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    today = date.today()
    weekly_task = Task(
        name="Weekly grooming",
        duration_minutes=60,
        priority=4,
        recurrence=Recurrence.WEEKLY,
        next_due_date=today,
        is_complete=True,
    )

    pet.add_task(weekly_task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, schedule_date=today)
    scheduler.advance_recurring_tasks([weekly_task])

    assert weekly_task.next_due_date == today + timedelta(days=7)
    assert weekly_task.is_complete is False


def test_one_time_task_does_not_reschedule() -> None:
    """Verify one-time tasks stay complete and are not rescheduled by advance_recurring_tasks."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    today = date.today()
    one_time_task = Task(
        name="Vet appointment",
        duration_minutes=45,
        priority=5,
        recurrence=Recurrence.ONE_TIME,
        next_due_date=today,
        is_complete=True,
    )

    pet.add_task(one_time_task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, schedule_date=today)

    # Store original due date
    original_due_date = one_time_task.next_due_date

    # advance_recurring_tasks should not modify ONE_TIME tasks
    scheduler.advance_recurring_tasks([one_time_task])

    # Should remain complete and due date unchanged (advance_recurring_tasks only affects recurring tasks)
    assert one_time_task.is_complete is True
    assert one_time_task.next_due_date == original_due_date


def test_recurring_task_with_future_due_date_not_scheduled_today() -> None:
    """Verify tasks with future due dates don't appear in today's schedule."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    today = date.today()
    tomorrow = today + timedelta(days=1)

    future_task = Task(
        name="Future task",
        duration_minutes=30,
        priority=5,
        recurrence=Recurrence.DAILY,
        next_due_date=tomorrow,
    )

    pet.add_task(future_task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, schedule_date=today)
    schedule = scheduler.generate_schedule()

    # Task shouldn't be scheduled today
    assert len(schedule) == 0


# ============================================================================
# CONFLICT DETECTION TESTS
# ============================================================================


def test_scheduler_detects_duplicate_fixed_times() -> None:
    """Verify that the scheduler flags tasks with duplicate fixed times (conflict)."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    # Two tasks with the same fixed time
    task1 = Task(name="Task A", duration_minutes=30, priority=5, fixed_time_minute=600)  # 10:00
    task2 = Task(
        name="Task B", duration_minutes=20, priority=4, fixed_time_minute=600
    )  # 10:00 (same!)

    pet.add_task(task1)
    pet.add_task(task2)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, schedule_date=date.today())
    schedule = scheduler.generate_schedule()

    # Only one should be scheduled (the first one processed)
    assert len(schedule) == 1

    # The unscheduled task should be identifiable
    unscheduled = scheduler.get_unscheduled_tasks(schedule)
    assert len(unscheduled) == 1


def test_detect_overlapping_tasks() -> None:
    """Verify conflict detection identifies overlapping tasks."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    task1 = Task(name="Task 1", duration_minutes=30, priority=5)
    task2 = Task(name="Task 2", duration_minutes=20, priority=4)

    # Manually create overlapping schedule items
    item1 = ScheduleItem(pet=pet, task=task1, start_minute=100, end_minute=130, reason="test")
    item2 = ScheduleItem(pet=pet, task=task2, start_minute=120, end_minute=140, reason="test")

    scheduler = Scheduler(owner=owner)
    conflicts = scheduler.detect_conflicts([item1, item2])

    assert len(conflicts) > 0
    assert any("overlap" in conflict.lower() for conflict in conflicts)


def test_detect_task_outside_time_window() -> None:
    """Verify conflict detection catches tasks scheduled outside their time windows."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    # Task with window 9:00-11:00 (540-660)
    task = Task(
        name="Morning task",
        duration_minutes=30,
        priority=5,
        time_window=TimeWindow(start_minute=540, end_minute=660),
    )

    # Schedule it in the afternoon (outside window)
    item = ScheduleItem(pet=pet, task=task, start_minute=800, end_minute=830, reason="test")

    scheduler = Scheduler(owner=owner)
    conflicts = scheduler.detect_conflicts([item])

    assert len(conflicts) > 0
    assert any("outside its allowed time window" in conflict for conflict in conflicts)


def test_detect_invalid_time_range() -> None:
    """Verify conflict detection catches invalid time ranges (negative, > 1440, start >= end)."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")
    task = Task(name="Invalid task", duration_minutes=30, priority=5)

    scheduler = Scheduler(owner=owner)

    # Test negative start time
    item_negative = ScheduleItem(pet=pet, task=task, start_minute=-10, end_minute=20, reason="test")
    conflicts_negative = scheduler.detect_conflicts([item_negative])
    assert len(conflicts_negative) > 0
    assert any("Invalid time range" in conflict for conflict in conflicts_negative)

    # Test beyond 24 hours
    item_beyond = ScheduleItem(
        pet=pet, task=task, start_minute=1400, end_minute=1450, reason="test"
    )
    conflicts_beyond = scheduler.detect_conflicts([item_beyond])
    assert len(conflicts_beyond) > 0
    assert any("Invalid time range" in conflict for conflict in conflicts_beyond)

    # Test start >= end
    item_reversed = ScheduleItem(
        pet=pet, task=task, start_minute=100, end_minute=100, reason="test"
    )
    conflicts_reversed = scheduler.detect_conflicts([item_reversed])
    assert len(conflicts_reversed) > 0
    assert any("Invalid time range" in conflict for conflict in conflicts_reversed)


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


def test_task_at_midnight_boundary() -> None:
    """Test task scheduled exactly at midnight (minute 0)."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    task = Task(name="Midnight task", duration_minutes=30, priority=5, fixed_time_minute=0)
    pet.add_task(task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, schedule_date=date.today())
    schedule = scheduler.generate_schedule()

    assert len(schedule) == 1
    assert schedule[0].start_minute == 0
    assert schedule[0].end_minute == 30


def test_task_at_end_of_day_boundary() -> None:
    """Test task near end of day (minute 1439 = 23:59)."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    # Task that starts at 23:50 (1430) and lasts 10 minutes (ends at 1440 = exactly 24:00)
    task = Task(name="Late night task", duration_minutes=10, priority=5, fixed_time_minute=1430)
    pet.add_task(task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, schedule_date=date.today())
    schedule = scheduler.generate_schedule()

    assert len(schedule) == 1
    assert schedule[0].start_minute == 1430
    assert schedule[0].end_minute == 1440


def test_task_exceeding_day_boundary_is_rejected() -> None:
    """Test that tasks extending beyond minute 1440 are not scheduled."""
    owner = Owner(name="Alex", available_time_minutes=200)
    pet = Pet(name="Max", species="dog")

    # Task that would extend past midnight
    task = Task(name="Too late", duration_minutes=30, priority=5, fixed_time_minute=1425)
    pet.add_task(task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, schedule_date=date.today())
    schedule = scheduler.generate_schedule()

    # Task should not be scheduled
    assert len(schedule) == 0


def test_critical_task_exceeds_available_time() -> None:
    """Verify critical tasks can be scheduled even when they exceed available time."""
    owner = Owner(name="Alex", available_time_minutes=30)
    pet = Pet(name="Max", species="dog")

    # Critical task that exceeds available time
    critical_task = Task(
        name="Critical medicine",
        duration_minutes=45,
        priority=5,
        is_critical=True,
        next_due_date=date.today(),
    )

    pet.add_task(critical_task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, schedule_date=date.today())
    schedule = scheduler.generate_schedule()

    # Critical task should still be scheduled
    assert len(schedule) == 1
    assert schedule[0].task.name == "Critical medicine"
    assert "critical" in schedule[0].reason.lower()


def test_non_critical_task_exceeds_available_time() -> None:
    """Verify non-critical tasks are skipped when they exceed available time."""
    owner = Owner(name="Alex", available_time_minutes=30)
    pet = Pet(name="Max", species="dog")

    # Non-critical task that exceeds available time
    task = Task(
        name="Long walk",
        duration_minutes=60,
        priority=5,
        is_critical=False,
        next_due_date=date.today(),
    )

    pet.add_task(task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, schedule_date=date.today())
    schedule = scheduler.generate_schedule()

    # Task should not be scheduled
    assert len(schedule) == 0


def test_time_window_exact_fit() -> None:
    """Test task that exactly fits its time window."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    # Task with duration exactly matching window size
    task = Task(
        name="Exact fit",
        duration_minutes=60,
        priority=5,
        time_window=TimeWindow(start_minute=600, end_minute=660),  # Exactly 60 minutes
    )

    pet.add_task(task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, schedule_date=date.today())
    schedule = scheduler.generate_schedule()

    assert len(schedule) == 1
    assert schedule[0].start_minute == 600
    assert schedule[0].end_minute == 660


def test_time_window_too_small_for_task() -> None:
    """Test that task cannot be scheduled if window is smaller than duration."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    # Window is 30 minutes but task needs 45 minutes
    task = Task(
        name="Won't fit",
        duration_minutes=45,
        priority=5,
        time_window=TimeWindow(start_minute=600, end_minute=630),
    )

    pet.add_task(task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, schedule_date=date.today())
    schedule = scheduler.generate_schedule()

    # Task cannot be scheduled
    assert len(schedule) == 0


def test_fixed_time_outside_time_window_validation() -> None:
    """Test that task with fixed time outside its time window fails validation."""
    # Fixed time at 500, but window is 600-700
    task = Task(
        name="Invalid",
        duration_minutes=30,
        priority=5,
        fixed_time_minute=500,
        time_window=TimeWindow(start_minute=600, end_minute=700),
    )

    # Should fail validation
    assert task.validate() is False


def test_owner_with_zero_available_time() -> None:
    """Test scheduler behavior with owner having zero available time."""
    owner = Owner(name="Alex", available_time_minutes=0)
    pet = Pet(name="Max", species="dog")

    task = Task(name="Any task", duration_minutes=30, priority=5, next_due_date=date.today())
    pet.add_task(task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, schedule_date=date.today())
    schedule = scheduler.generate_schedule()

    # No tasks should be scheduled (unless critical)
    assert len(schedule) == 0


def test_owner_with_negative_available_time() -> None:
    """Test that negative available time is handled as zero."""
    owner = Owner(name="Alex", available_time_minutes=-50)
    scheduler = Scheduler(owner=owner)

    # Should return 0, not negative
    assert scheduler.get_available_time_minutes() == 0


def test_empty_task_name_fails_validation() -> None:
    """Test that task with empty or whitespace-only name fails validation."""
    task_empty = Task(name="", duration_minutes=30, priority=3)
    task_whitespace = Task(name="   ", duration_minutes=30, priority=3)

    assert task_empty.validate() is False
    assert task_whitespace.validate() is False


def test_invalid_priority_fails_validation() -> None:
    """Test that priority outside 1-5 range fails validation."""
    task_zero = Task(name="Task", duration_minutes=30, priority=0)
    task_negative = Task(name="Task", duration_minutes=30, priority=-1)
    task_too_high = Task(name="Task", duration_minutes=30, priority=6)

    assert task_zero.validate() is False
    assert task_negative.validate() is False
    assert task_too_high.validate() is False


def test_zero_duration_fails_validation() -> None:
    """Test that zero or negative duration fails validation."""
    task_zero = Task(name="Task", duration_minutes=0, priority=3)
    task_negative = Task(name="Task", duration_minutes=-10, priority=3)

    assert task_zero.validate() is False
    assert task_negative.validate() is False


def test_multiple_pets_tasks_are_interleaved() -> None:
    """Test that tasks from multiple pets can be scheduled together."""
    owner = Owner(name="Alex", available_time_minutes=200)

    pet1 = Pet(name="Max", species="dog")
    pet2 = Pet(name="Bella", species="cat")

    task1 = Task(name="Walk Max", duration_minutes=30, priority=5, fixed_time_minute=480)
    task2 = Task(name="Feed Bella", duration_minutes=15, priority=5, fixed_time_minute=600)
    task3 = Task(name="Play with Max", duration_minutes=20, priority=4, fixed_time_minute=720)

    pet1.add_task(task1)
    pet1.add_task(task3)
    pet2.add_task(task2)

    owner.add_pet(pet1)
    owner.add_pet(pet2)

    scheduler = Scheduler(owner=owner, schedule_date=date.today())
    schedule = scheduler.generate_schedule()

    # All tasks should be scheduled
    assert len(schedule) == 3
    # Should be in chronological order, mixing pets
    assert schedule[0].pet.name == "Max"
    assert schedule[1].pet.name == "Bella"
    assert schedule[2].pet.name == "Max"


def test_back_to_back_tasks_no_gap() -> None:
    """Test that tasks can be scheduled back-to-back with no gap."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    task1 = Task(name="Task 1", duration_minutes=30, priority=5, fixed_time_minute=600)
    task2 = Task(
        name="Task 2", duration_minutes=20, priority=4, fixed_time_minute=630
    )  # Starts exactly when task1 ends

    pet.add_task(task1)
    pet.add_task(task2)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, schedule_date=date.today())
    schedule = scheduler.generate_schedule()

    # Both should be scheduled with no overlap
    assert len(schedule) == 2
    assert schedule[0].end_minute == schedule[1].start_minute

    # Should be no conflicts
    conflicts = scheduler.detect_conflicts(schedule)
    assert len(conflicts) == 0
