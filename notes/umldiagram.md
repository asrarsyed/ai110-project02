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
        +fixed_time: str?
        +time_window: TimeWindow?
        +recurrence: Recurrence
        +is_complete: bool
        +is_critical: bool
        +mark_complete()
        +reschedule_next()
        +validate() bool
    }

    class Scheduler {
        +owner: Owner
        +tasks: list~Task~
        +available_time_minutes: int
        +generate_schedule() list~ScheduleItem~
        +sort_by_time(tasks: list~Task~) list~Task~
        +filter_tasks(status: str, pet: Pet?) list~Task~
        +detect_conflicts(tasks: list~Task~) list~str~
        +handle_recurring_tasks(tasks: list~Task~) list~Task~
    }

    class TimeWindow {
        +start: str
        +end: str
        +contains(time: str) bool
    }

    class ScheduleItem {
        +task: Task
        +start_time: str
        +end_time: str
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
    Scheduler "1" --> "0..*" Task : selects_and_orders
    Scheduler "1" --> "0..*" ScheduleItem : outputs
```

## Design Notes

- Core entities remain Owner, Pet, Task, and Scheduler.
- TimeWindow, Recurrence, and ScheduleItem are support types that make constraints and output explicit.
- `priority` uses an integer scale (recommended 1-5), with higher values meaning higher priority.
- Optional fields are marked with `?`.
- Composition (`*--`) is used for Owner->Pet and Pet->Task because those objects are managed as part of their parent context.