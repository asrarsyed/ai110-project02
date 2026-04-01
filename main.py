from datetime import date

from pawpal_system import Owner, Pet, Recurrence, Scheduler, Task, TimeWindow


def minute_to_hhmm(minute: int) -> str:
    hours = minute // 60
    mins = minute % 60
    return f"{hours:02d}:{mins:02d}"


def build_sample_data() -> Owner:
    owner = Owner(name="Jordan", available_time_minutes=180)

    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")

    mochi.add_task(
        Task(
            name="Morning walk",
            duration_minutes=30,
            priority=5,
            fixed_time_minute=8 * 60,
            recurrence=Recurrence.DAILY,
            next_due_date=date.today(),
            is_critical=True,
        )
    )

    luna.add_task(
        Task(
            name="Feed breakfast",
            duration_minutes=10,
            priority=5,
            fixed_time_minute=7 * 60 + 30,
            recurrence=Recurrence.DAILY,
            next_due_date=date.today(),
            is_critical=True,
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

    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner


def print_schedule() -> None:
    owner = build_sample_data()
    scheduler = Scheduler(owner=owner, schedule_date=date.today())
    schedule = scheduler.generate_schedule()

    print("Today's Schedule")
    print("=" * 20)

    if not schedule:
        print("No tasks were scheduled.")
        return

    for item in schedule:
        start = minute_to_hhmm(item.start_minute)
        end = minute_to_hhmm(item.end_minute)
        print(f"{start}-{end} | {item.pet.name} | {item.task.name} | {item.reason}")


if __name__ == "__main__":
    print_schedule()
