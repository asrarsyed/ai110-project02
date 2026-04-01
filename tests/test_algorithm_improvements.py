"""Tests for algorithm improvements: sorting, filtering, recurring tasks, conflict detection."""

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


def test_sort_by_status_incomplete_first() -> None:
    """Test that incomplete tasks are sorted before complete tasks."""
    owner = Owner(name="Alex", available_time_minutes=120)
    scheduler = Scheduler(owner=owner)

    task1 = Task(name="Task1", duration_minutes=10, priority=3, is_complete=True)
    task2 = Task(name="Task2", duration_minutes=10, priority=3, is_complete=False)
    task3 = Task(name="Task3", duration_minutes=10, priority=3, is_complete=False)

    sorted_tasks = scheduler.sort_by_status([task1, task2, task3])

    assert sorted_tasks[0].is_complete is False
    assert sorted_tasks[1].is_complete is False
    assert sorted_tasks[2].is_complete is True


def test_sort_by_pet_and_time() -> None:
    """Test sorting schedule items by pet name then start time."""
    owner = Owner(name="Alex", available_time_minutes=120)
    scheduler = Scheduler(owner=owner)

    pet1 = Pet(name="Buddy", species="dog")
    pet2 = Pet(name="Alice", species="cat")

    task1 = Task(name="Walk", duration_minutes=30, priority=3)
    task2 = Task(name="Feed", duration_minutes=10, priority=3)

    item1 = ScheduleItem(pet=pet1, task=task1, start_minute=100, end_minute=130, reason="test")
    item2 = ScheduleItem(pet=pet2, task=task2, start_minute=50, end_minute=60, reason="test")
    item3 = ScheduleItem(pet=pet1, task=task2, start_minute=30, end_minute=40, reason="test")

    sorted_items = scheduler.sort_by_pet_and_time([item1, item2, item3])

    # Should be sorted: Alice (50), Buddy (30), Buddy (100)
    assert sorted_items[0].pet.name == "Alice"
    assert sorted_items[1].pet.name == "Buddy"
    assert sorted_items[1].start_minute == 30
    assert sorted_items[2].pet.name == "Buddy"
    assert sorted_items[2].start_minute == 100


def test_filter_tasks_by_recurrence() -> None:
    """Test filtering tasks by recurrence type."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    task1 = Task(name="Daily walk", duration_minutes=30, priority=5, recurrence=Recurrence.DAILY)
    task2 = Task(name="Weekly vet", duration_minutes=60, priority=4, recurrence=Recurrence.WEEKLY)
    task3 = Task(
        name="One-time bath", duration_minutes=20, priority=3, recurrence=Recurrence.ONE_TIME
    )

    pet.add_task(task1)
    pet.add_task(task2)
    pet.add_task(task3)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)

    daily_tasks = scheduler.filter_tasks(recurrence=Recurrence.DAILY)
    assert len(daily_tasks) == 1
    assert daily_tasks[0].name == "Daily walk"

    one_time_tasks = scheduler.filter_tasks(recurrence=Recurrence.ONE_TIME)
    assert len(one_time_tasks) == 1
    assert one_time_tasks[0].name == "One-time bath"


def test_filter_tasks_by_critical() -> None:
    """Test filtering tasks by critical flag."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    task1 = Task(name="Medicine", duration_minutes=5, priority=5, is_critical=True)
    task2 = Task(name="Play", duration_minutes=20, priority=3, is_critical=False)

    pet.add_task(task1)
    pet.add_task(task2)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)

    critical_tasks = scheduler.filter_tasks(critical=True)
    assert len(critical_tasks) == 1
    assert critical_tasks[0].name == "Medicine"

    non_critical_tasks = scheduler.filter_tasks(critical=False)
    assert len(non_critical_tasks) == 1
    assert non_critical_tasks[0].name == "Play"


def test_filter_tasks_by_min_priority() -> None:
    """Test filtering tasks by minimum priority level."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    task1 = Task(name="Critical", duration_minutes=10, priority=5)
    task2 = Task(name="Important", duration_minutes=15, priority=4)
    task3 = Task(name="Optional", duration_minutes=20, priority=2)

    pet.add_task(task1)
    pet.add_task(task2)
    pet.add_task(task3)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)

    high_priority_tasks = scheduler.filter_tasks(min_priority=4)
    assert len(high_priority_tasks) == 2
    assert all(task.priority >= 4 for task in high_priority_tasks)


def test_filter_tasks_combined_criteria() -> None:
    """Test filtering with multiple criteria at once."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    task1 = Task(
        name="Daily medicine",
        duration_minutes=5,
        priority=5,
        recurrence=Recurrence.DAILY,
        is_critical=True,
        is_complete=False,
    )
    task2 = Task(
        name="Daily walk",
        duration_minutes=30,
        priority=4,
        recurrence=Recurrence.DAILY,
        is_critical=False,
        is_complete=True,
    )
    task3 = Task(
        name="One-time play",
        duration_minutes=20,
        priority=3,
        recurrence=Recurrence.ONE_TIME,
        is_critical=False,
        is_complete=False,
    )

    pet.add_task(task1)
    pet.add_task(task2)
    pet.add_task(task3)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner)

    # Filter for daily, incomplete, critical tasks with priority >= 5
    filtered = scheduler.filter_tasks(
        completed=False, recurrence=Recurrence.DAILY, critical=True, min_priority=5
    )

    assert len(filtered) == 1
    assert filtered[0].name == "Daily medicine"


def test_filter_by_pets() -> None:
    """Test getting tasks for multiple specific pets."""
    owner = Owner(name="Alex", available_time_minutes=120)

    pet1 = Pet(name="Max", species="dog")
    pet2 = Pet(name="Bella", species="cat")
    pet3 = Pet(name="Charlie", species="dog")

    task1 = Task(name="Walk Max", duration_minutes=30, priority=4)
    task2 = Task(name="Feed Bella", duration_minutes=10, priority=5)
    task3 = Task(name="Walk Charlie", duration_minutes=25, priority=4)

    pet1.add_task(task1)
    pet2.add_task(task2)
    pet3.add_task(task3)

    owner.add_pet(pet1)
    owner.add_pet(pet2)
    owner.add_pet(pet3)

    scheduler = Scheduler(owner=owner)

    # Get tasks for Max and Charlie only
    tasks = scheduler.filter_by_pets([pet1, pet3])

    assert len(tasks) == 2
    assert task1 in tasks
    assert task3 in tasks
    assert task2 not in tasks


def test_advance_recurring_tasks() -> None:
    """Test auto-advancing completed recurring tasks."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    today = date.today()

    daily_task = Task(
        name="Daily walk",
        duration_minutes=30,
        priority=5,
        recurrence=Recurrence.DAILY,
        next_due_date=today,
        is_complete=True,
    )
    weekly_task = Task(
        name="Weekly grooming",
        duration_minutes=60,
        priority=3,
        recurrence=Recurrence.WEEKLY,
        next_due_date=today,
        is_complete=True,
    )
    one_time_task = Task(
        name="Vet visit",
        duration_minutes=45,
        priority=5,
        recurrence=Recurrence.ONE_TIME,
        is_complete=True,
    )

    pet.add_task(daily_task)
    pet.add_task(weekly_task)
    pet.add_task(one_time_task)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, schedule_date=today)
    scheduler.advance_recurring_tasks([daily_task, weekly_task, one_time_task])

    # Daily task should advance by 1 day
    assert daily_task.next_due_date == today + timedelta(days=1)
    assert daily_task.is_complete is False

    # Weekly task should advance by 7 days
    assert weekly_task.next_due_date == today + timedelta(days=7)
    assert weekly_task.is_complete is False

    # One-time task should have no next due date
    assert one_time_task.next_due_date is None
    assert one_time_task.is_complete is True


def test_detect_time_window_conflicts() -> None:
    """Test detection of tasks scheduled outside their time windows."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    # Task with time window 9:00-11:00 (540-660 minutes)
    task = Task(
        name="Morning walk",
        duration_minutes=30,
        priority=5,
        time_window=TimeWindow(start_minute=540, end_minute=660),
    )

    # Schedule it outside the window (7:00-7:30 = 420-450)
    item = ScheduleItem(pet=pet, task=task, start_minute=420, end_minute=450, reason="test")

    scheduler = Scheduler(owner=owner)
    conflicts = scheduler.detect_conflicts([item])

    assert len(conflicts) > 0
    assert any("outside its allowed time window" in conflict for conflict in conflicts)


def test_detect_over_scheduling() -> None:
    """Test detection of total scheduled time exceeding available time."""
    owner = Owner(name="Alex", available_time_minutes=60)  # Only 60 minutes available
    pet = Pet(name="Max", species="dog")

    task1 = Task(name="Task1", duration_minutes=40, priority=5)
    task2 = Task(name="Task2", duration_minutes=30, priority=4)

    item1 = ScheduleItem(pet=pet, task=task1, start_minute=0, end_minute=40, reason="test")
    item2 = ScheduleItem(pet=pet, task=task2, start_minute=40, end_minute=70, reason="test")

    scheduler = Scheduler(owner=owner)
    conflicts = scheduler.detect_conflicts([item1, item2])

    # Should detect over-scheduling (70 minutes scheduled, only 60 available)
    assert any("Over-scheduled" in conflict for conflict in conflicts)


def test_detect_overlap_with_details() -> None:
    """Test that overlap detection includes overlap duration."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    task1 = Task(name="Task1", duration_minutes=30, priority=5)
    task2 = Task(name="Task2", duration_minutes=20, priority=4)

    # Task1: 0-30, Task2: 20-40 (10 minute overlap)
    item1 = ScheduleItem(pet=pet, task=task1, start_minute=0, end_minute=30, reason="test")
    item2 = ScheduleItem(pet=pet, task=task2, start_minute=20, end_minute=40, reason="test")

    scheduler = Scheduler(owner=owner)
    conflicts = scheduler.detect_conflicts([item1, item2])

    assert len(conflicts) > 0
    assert any("10 minutes" in conflict for conflict in conflicts)


def test_get_unscheduled_tasks() -> None:
    """Test identifying tasks that couldn't be scheduled."""
    owner = Owner(name="Alex", available_time_minutes=30)  # Very limited time

    pet = Pet(name="Max", species="dog")

    task1 = Task(
        name="Short task",
        duration_minutes=10,
        priority=5,
        next_due_date=date.today(),
    )
    task2 = Task(
        name="Long task",
        duration_minutes=60,
        priority=3,
        next_due_date=date.today(),
    )

    pet.add_task(task1)
    pet.add_task(task2)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, schedule_date=date.today())
    schedule = scheduler.generate_schedule()

    # Only task1 should fit
    assert len(schedule) == 1
    assert schedule[0].task.name == "Short task"

    # task2 should be unscheduled
    unscheduled = scheduler.get_unscheduled_tasks(schedule)
    assert len(unscheduled) == 1
    assert unscheduled[0][0].name == "Long task"
    assert unscheduled[0][1].name == "Max"


def test_handle_recurring_tasks_respects_due_dates() -> None:
    """Test that recurring tasks only appear when they're due."""
    owner = Owner(name="Alex", available_time_minutes=120)
    pet = Pet(name="Max", species="dog")

    today = date.today()
    tomorrow = today + timedelta(days=1)

    # Task due today
    task_today = Task(
        name="Due today",
        duration_minutes=20,
        priority=5,
        recurrence=Recurrence.DAILY,
        next_due_date=today,
    )

    # Task due tomorrow (not yet due)
    task_future = Task(
        name="Due tomorrow",
        duration_minutes=20,
        priority=5,
        recurrence=Recurrence.DAILY,
        next_due_date=tomorrow,
    )

    pet.add_task(task_today)
    pet.add_task(task_future)
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, schedule_date=today)
    due_tasks = scheduler.handle_recurring_tasks([task_today, task_future])

    # Only task_today should be in the list
    assert len(due_tasks) == 1
    assert due_tasks[0].name == "Due today"
