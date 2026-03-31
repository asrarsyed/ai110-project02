# PawPal+ UML Class Diagram

```mermaid
classDiagram
    direction LR

    class Owner {
        +name: str
        +available_time_minutes: int
        +preferences: dict?
        +pets: list~Pet~
        +add_pet(pet: Pet)
        +remove_pet(pet: Pet)
        +get_all_tasks() list~Task~
    }

    class Pet {
        +name: str
        +species: str
        +age: int?
        +medical_needs: str?
        +tasks: list~Task~
        +add_task(task: Task)
        +remove_task(task: Task)
        +get_tasks() list~Task~
    }

    class Task {
        +name: str
        +duration_minutes: int
        +priority: int
        +fixed_time_minute: int?
        +time_window: TimeWindow?
        +recurrence: Recurrence
        +next_due_date: date?
        +is_complete: bool
        +is_critical: bool
        +mark_complete()
        +reschedule_next(reference_date: date)
        +validate() bool
    }

    class Scheduler {
        +owner: Owner
        +schedule_date: date?
        +generate_schedule() list~ScheduleItem~
        +get_candidate_tasks() list~Task~
        +get_available_time_minutes() int
        +sort_by_time(tasks: list~Task~) list~Task~
        +filter_tasks(completed: bool?, pet: Pet?) list~Task~
        +detect_conflicts(schedule_items: list~ScheduleItem~) list~str~
        +handle_recurring_tasks(tasks: list~Task~) list~Task~
    }

    class TimeWindow {
        +start_minute: int
        +end_minute: int
        +contains(minute: int) bool
        +validate() bool
    }

    class ScheduleItem {
        +pet: Pet
        +task: Task
        +start_minute: int
        +end_minute: int
        +reason: str
    }

    class Recurrence {
        <<enumeration>>
        DAILY
        WEEKLY
        ONE_TIME
    }

    Owner "1" *-- "0..*" Pet : owns
    Pet "1" *-- "0..*" Task : manages
    Task "0..1" --> "1" TimeWindow : constrained_by
    Task --> Recurrence : repeats_as
    Scheduler "1" --> "1" Owner : reads_constraints_from
    Scheduler ..> Task : orders_indirectly_via_owner
    Scheduler "1" --> "0..*" ScheduleItem : outputs
```

## Design Notes

- Core entities remain Owner, Pet, Task, and Scheduler.
- TimeWindow, Recurrence, and ScheduleItem are support types that make constraints and output explicit.
- Time fields use integer minutes to avoid fragile string parsing during comparisons.
- Scheduler reads tasks and time budget from Owner as the source of truth.
- `priority` uses an integer scale (recommended 1-5), with higher values meaning higher priority.
- Optional fields are marked with `?`.
- Composition (`*--`) is used for Owner->Pet and Pet->Task because those objects are managed as part of their parent context.