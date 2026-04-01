"""PawPal+ Scheduling Demo - Demonstrates all algorithm improvements"""

from datetime import date

from pawpal_system import Owner, Pet, Recurrence, Scheduler, Task, TimeWindow


def minute_to_hhmm(minute: int) -> str:
    """Convert minute of day to HH:MM format."""
    hours = minute // 60
    mins = minute % 60
    return f"{hours:02d}:{mins:02d}"


def main_demo() -> None:
    """Comprehensive demo of PawPal+ scheduling system."""
    print("\n" + "=" * 60)
    print("PawPal+ Pet Scheduling System Demo")
    print("=" * 60)

    owner = Owner(name="Jordan", available_time_minutes=180)
    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")

    today = date.today()

    # Add tasks OUT OF ORDER to demonstrate sorting
    # (Assignment requirement: add tasks out of order)
    luna.add_task(
        Task(
            name="Litter box cleaning",
            duration_minutes=15,
            priority=4,
            recurrence=Recurrence.DAILY,
            next_due_date=today,
        )
    )

    mochi.add_task(
        Task(
            name="Play session",
            duration_minutes=20,
            priority=3,
            time_window=TimeWindow(start_minute=9 * 60, end_minute=11 * 60),
            recurrence=Recurrence.ONE_TIME,
        )
    )

    luna.add_task(
        Task(
            name="Feed breakfast",
            duration_minutes=10,
            priority=5,
            fixed_time_minute=7 * 60 + 30,  # 7:30 AM
            recurrence=Recurrence.DAILY,
            next_due_date=today,
            is_critical=True,
        )
    )

    mochi.add_task(
        Task(
            name="Morning walk",
            duration_minutes=30,
            priority=5,
            fixed_time_minute=8 * 60,  # 8:00 AM
            recurrence=Recurrence.DAILY,
            next_due_date=today,
            is_critical=True,
        )
    )

    mochi.add_task(
        Task(
            name="Weekly vet checkup",
            duration_minutes=45,
            priority=4,
            recurrence=Recurrence.WEEKLY,
            next_due_date=today,
        )
    )

    owner.add_pet(mochi)
    owner.add_pet(luna)

    scheduler = Scheduler(owner=owner, schedule_date=today)

    # STEP 2 DEMO: Sorting and Filtering
    print("\n📋 Step 2: Sorting and Filtering")
    print("-" * 60)

    all_tasks = owner.get_all_tasks()
    print(f"\n1. Original task order (added out of order):")
    for i, task in enumerate(all_tasks, 1):
        print(f"   {i}. {task.name} (priority {task.priority})")

    sorted_tasks = scheduler.sort_by_time(all_tasks)
    print(f"\n2. Sorted by time (fixed → critical → priority → duration):")
    for i, task in enumerate(sorted_tasks, 1):
        fixed = f" @ {minute_to_hhmm(task.fixed_time_minute)}" if task.fixed_time_minute else ""
        critical = " [CRITICAL]" if task.is_critical else ""
        print(f"   {i}. {task.name}{critical}{fixed}")

    print(f"\n3. Filter Mochi's tasks:")
    mochi_tasks = scheduler.filter_tasks(pet=mochi)
    for task in mochi_tasks:
        print(f"   - {task.name} ({task.duration_minutes} min)")

    print(f"\n4. Filter by high priority (>= 4):")
    high_priority = scheduler.filter_tasks(min_priority=4)
    for task in high_priority:
        print(f"   - {task.name} (priority {task.priority})")

    # STEP 3 DEMO: Recurring Task Automation
    print("\n\n🔄 Step 3: Recurring Task Automation")
    print("-" * 60)

    # Find a daily task to demonstrate
    daily_walk = next(t for t in mochi.tasks if t.name == "Morning walk")
    print(f"\n1. Task: {daily_walk.name}")
    print(f"   Current due date: {daily_walk.next_due_date}")
    print(f"   Recurrence: {daily_walk.recurrence.value}")
    print(f"   Complete: {daily_walk.is_complete}")

    # Mark complete and advance
    daily_walk.mark_complete()
    print(f"\n2. After marking complete: {daily_walk.is_complete}")

    scheduler.advance_recurring_tasks([daily_walk])
    print(f"\n3. After auto-advance:")
    print(f"   New due date: {daily_walk.next_due_date} (tomorrow)")
    print(f"   Reset to incomplete: {not daily_walk.is_complete}")
    print(f"   ✓ Used timedelta to advance by 1 day")

    # STEP 4 DEMO: Conflict Detection
    print("\n\n⚠️  Step 4: Conflict Detection")
    print("-" * 60)

    # Generate schedule
    schedule = scheduler.generate_schedule()

    print(f"\n1. Generated Schedule:")
    for item in schedule:
        start = minute_to_hhmm(item.start_minute)
        end = minute_to_hhmm(item.end_minute)
        print(f"   {start}-{end} | {item.pet.name:5} | {item.task.name}")

    # Check for conflicts
    conflicts = scheduler.detect_conflicts(schedule)
    print(f"\n2. Conflict Check:")
    if conflicts:
        for conflict in conflicts:
            print(f"   ⚠️ {conflict}")
    else:
        print(f"   ✅ No conflicts detected!")

    # Show unscheduled tasks
    unscheduled = scheduler.get_unscheduled_tasks(schedule)
    if unscheduled:
        print(f"\n3. Unscheduled Tasks ({len(unscheduled)}):")
        for task, pet in unscheduled:
            print(f"   - {task.name} ({pet.name})")
    else:
        print(f"\n3. ✅ All tasks scheduled successfully!")

    # Summary
    total_time = sum(item.task.duration_minutes for item in schedule)
    print(f"\n" + "=" * 60)
    print(f"Summary:")
    print(f"  Total scheduled: {total_time} minutes")
    print(f"  Available time: {owner.available_time_minutes} minutes")
    print(f"  Tasks scheduled: {len(schedule)}")
    print(f"  Pets managed: {len(owner.pets)}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main_demo()
