from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Any


class Recurrence(Enum):
    """Defines how often a task should repeat."""

    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    ONE_TIME = "ONE_TIME"


@dataclass
class TimeWindow:
    """Represents an allowed minute range within a day for a task."""

    start_minute: int
    end_minute: int

    def contains(self, minute: int) -> bool:
        if not self.validate():
            return False
        return self.start_minute <= minute <= self.end_minute

    def validate(self) -> bool:
        if self.start_minute < 0 or self.end_minute > 1439:
            return False
        return self.start_minute <= self.end_minute


@dataclass
class Task:
    """Represents one care activity with timing, priority, and recurrence rules."""

    name: str
    duration_minutes: int
    priority: int
    fixed_time_minute: int | None = None
    time_window: TimeWindow | None = None
    recurrence: Recurrence = Recurrence.ONE_TIME
    next_due_date: date | None = None
    is_complete: bool = False
    is_critical: bool = False

    def mark_complete(self) -> None:
        self.is_complete = True

    def reschedule_next(self, reference_date: date) -> None:
        if self.recurrence == Recurrence.DAILY:
            self.next_due_date = reference_date + timedelta(days=1)
            self.is_complete = False
            return
        if self.recurrence == Recurrence.WEEKLY:
            self.next_due_date = reference_date + timedelta(days=7)
            self.is_complete = False
            return
        self.next_due_date = None

    def validate(self) -> bool:
        if not self.name.strip():
            return False
        if self.duration_minutes <= 0:
            return False
        if not 1 <= self.priority <= 5:
            return False
        if self.fixed_time_minute is not None and not 0 <= self.fixed_time_minute <= 1439:
            return False
        if self.time_window is not None and not self.time_window.validate():
            return False
        return not (
            self.fixed_time_minute is not None
            and self.time_window is not None
            and not self.time_window.contains(self.fixed_time_minute)
        )


@dataclass
class Pet:
    """Stores pet profile information and that pet's care tasks."""

    name: str
    species: str
    age: int | None = None
    medical_needs: str | None = None
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        if not task.validate():
            raise ValueError("Task is invalid and cannot be added.")
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        self.tasks.remove(task)

    def get_tasks(self) -> list[Task]:
        return list(self.tasks)


@dataclass
class Owner:
    """Manages pets and exposes all tasks as one owner-level collection."""

    name: str
    available_time_minutes: int
    preferences: dict[str, Any] | None = None
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        self.pets.remove(pet)

    def get_all_tasks(self) -> list[Task]:
        tasks: list[Task] = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks


@dataclass
class ScheduleItem:
    """Represents one scheduled task block with rationale."""

    pet: Pet
    task: Task
    start_minute: int
    end_minute: int
    reason: str


@dataclass
class Scheduler:
    """Coordinates and prioritizes tasks across pets to build a daily plan."""

    owner: Owner
    schedule_date: date | None = None

    def generate_schedule(self) -> list[ScheduleItem]:
        scheduled_items: list[ScheduleItem] = []
        used_minutes = 0

        pairs = self._get_task_pet_pairs()
        candidate_tasks = self.handle_recurring_tasks([task for task, _ in pairs])
        tasks_by_id = {id(task): pet for task, pet in pairs}

        for task in self.sort_by_time(candidate_tasks):
            pet = tasks_by_id[id(task)]

            if (
                used_minutes + task.duration_minutes > self.get_available_time_minutes()
                and not task.is_critical
            ):
                continue

            start_minute = self._find_start_minute(task, scheduled_items)
            if start_minute is None:
                continue

            end_minute = start_minute + task.duration_minutes

            if task.time_window is not None and end_minute > task.time_window.end_minute:
                continue

            reason = "Scheduled by priority and constraints"
            if task.fixed_time_minute is not None:
                reason = "Scheduled at fixed time"
            elif task.time_window is not None:
                reason = "Scheduled within allowed time window"

            if (
                used_minutes + task.duration_minutes > self.get_available_time_minutes()
                and task.is_critical
            ):
                reason = "Scheduled despite time limit because task is critical"

            scheduled_items.append(
                ScheduleItem(
                    pet=pet,
                    task=task,
                    start_minute=start_minute,
                    end_minute=end_minute,
                    reason=reason,
                )
            )
            used_minutes += task.duration_minutes

        scheduled_items.sort(key=lambda item: item.start_minute)
        return scheduled_items

    def get_candidate_tasks(self) -> list[Task]:
        return self.handle_recurring_tasks(self.owner.get_all_tasks())

    def get_available_time_minutes(self) -> int:
        return max(0, self.owner.available_time_minutes)

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by fixed time, criticality, priority, and duration.

        Optimized sorting order:
        1. Fixed-time tasks come first (sorted by their fixed time)
        2. Critical tasks come before non-critical
        3. Higher priority tasks come first
        4. Shorter tasks come first (easier to fit in schedule)
        """
        return sorted(
            tasks,
            key=lambda task: (
                0 if task.fixed_time_minute is not None else 1,
                task.fixed_time_minute if task.fixed_time_minute is not None else 10_000,
                0 if task.is_critical else 1,
                -task.priority,
                task.duration_minutes,
            ),
        )

    def sort_by_status(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by completion status (incomplete first)."""
        return sorted(tasks, key=lambda task: task.is_complete)

    def sort_by_pet_and_time(self, schedule_items: list[ScheduleItem]) -> list[ScheduleItem]:
        """Sort schedule items by pet name, then by start time."""
        return sorted(schedule_items, key=lambda item: (item.pet.name, item.start_minute))

    def filter_tasks(
        self,
        completed: bool | None = None,
        pet: Pet | None = None,
        recurrence: Recurrence | None = None,
        critical: bool | None = None,
        min_priority: int | None = None,
    ) -> list[Task]:
        """Advanced filtering with multiple criteria.

        Args:
            completed: Filter by completion status (None = all)
            pet: Filter to specific pet's tasks (None = all pets)
            recurrence: Filter by recurrence type (None = all types)
            critical: Filter by critical flag (None = all)
            min_priority: Filter tasks with priority >= this value (None = all)
        """
        source = pet.tasks if pet is not None else self.owner.get_all_tasks()

        result = list(source)

        if completed is not None:
            result = [task for task in result if task.is_complete is completed]

        if recurrence is not None:
            result = [task for task in result if task.recurrence == recurrence]

        if critical is not None:
            result = [task for task in result if task.is_critical is critical]

        if min_priority is not None:
            result = [task for task in result if task.priority >= min_priority]

        return result

    def filter_by_pets(self, pets: list[Pet]) -> list[Task]:
        """Get all tasks for multiple specific pets."""
        tasks: list[Task] = []
        for pet in pets:
            tasks.extend(pet.tasks)
        return tasks

    def detect_conflicts(self, schedule_items: list[ScheduleItem]) -> list[str]:
        """Detect various scheduling conflicts and issues.

        Checks for:
        - Invalid time ranges (negative, beyond 24h, start >= end)
        - Overlapping tasks
        - Tasks exceeding time windows
        - Over-scheduling (total time > available time)
        """
        conflicts: list[str] = []
        items = sorted(schedule_items, key=lambda item: item.start_minute)

        total_scheduled_minutes = 0

        for idx, item in enumerate(items):
            total_scheduled_minutes += item.task.duration_minutes

            # Check for invalid time ranges
            if (
                item.start_minute < 0
                or item.end_minute > 1440
                or item.start_minute >= item.end_minute
            ):
                conflicts.append(f"Invalid time range for task '{item.task.name}'.")

            # Check if task exceeds its time window
            if item.task.time_window is not None and (
                item.start_minute < item.task.time_window.start_minute
                or item.end_minute > item.task.time_window.end_minute
            ):
                conflicts.append(
                    f"Task '{item.task.name}' scheduled outside its allowed time window "
                    f"({item.task.time_window.start_minute}-{item.task.time_window.end_minute})."
                )

            if idx == 0:
                continue

            # Check for overlapping tasks
            prev = items[idx - 1]
            if item.start_minute < prev.end_minute:
                overlap_minutes = prev.end_minute - item.start_minute
                conflicts.append(
                    f"Overlap detected: '{prev.task.name}' and '{item.task.name}' "
                    f"conflict by {overlap_minutes} minutes."
                )

        # Check for over-scheduling
        available = self.get_available_time_minutes()
        if total_scheduled_minutes > available:
            conflicts.append(
                f"Over-scheduled: {total_scheduled_minutes} minutes scheduled, "
                f"but only {available} minutes available."
            )

        return conflicts

    def get_unscheduled_tasks(self, schedule_items: list[ScheduleItem]) -> list[tuple[Task, Pet]]:
        """Find tasks that couldn't be scheduled.

        Returns list of (task, pet) tuples for tasks that were candidates but not scheduled.
        """
        scheduled_task_ids = {id(item.task) for item in schedule_items}
        candidate_pairs = self._get_task_pet_pairs()
        candidate_tasks = self.handle_recurring_tasks([task for task, _ in candidate_pairs])
        tasks_by_id = {id(task): pet for task, pet in candidate_pairs}

        unscheduled = []
        for task in candidate_tasks:
            if id(task) not in scheduled_task_ids:
                pet = tasks_by_id.get(id(task))
                if pet:
                    unscheduled.append((task, pet))

        return unscheduled

    def handle_recurring_tasks(self, tasks: list[Task]) -> list[Task]:
        """Filter tasks to only those due on the target date.

        Logic:
        - ONE_TIME tasks: include if not complete and due date is today or earlier
        - DAILY/WEEKLY tasks: include if next_due_date is None or <= target_date
        """
        target_date = self.schedule_date or date.today()
        due_tasks: list[Task] = []

        for task in tasks:
            if not task.validate():
                continue

            if task.recurrence == Recurrence.ONE_TIME:
                if task.is_complete:
                    continue
                if task.next_due_date is not None and task.next_due_date > target_date:
                    continue
                due_tasks.append(task)
                continue

            if task.next_due_date is None or task.next_due_date <= target_date:
                due_tasks.append(task)

        return due_tasks

    def advance_recurring_tasks(self, tasks: list[Task]) -> None:
        """Auto-advance completed recurring tasks to their next due date.

        Should be called after completing tasks to prepare for the next cycle.
        """
        reference_date = self.schedule_date or date.today()
        for task in tasks:
            if task.is_complete and task.recurrence != Recurrence.ONE_TIME:
                task.reschedule_next(reference_date)

    def _get_task_pet_pairs(self) -> list[tuple[Task, Pet]]:
        pairs: list[tuple[Task, Pet]] = []
        for pet in self.owner.pets:
            for task in pet.tasks:
                pairs.append((task, pet))
        return pairs

    def _find_start_minute(self, task: Task, schedule_items: list[ScheduleItem]) -> int | None:
        if task.fixed_time_minute is not None:
            start = task.fixed_time_minute
            end = start + task.duration_minutes
            if end > 1440:
                return None
            if task.time_window is not None and (
                start < task.time_window.start_minute or end > task.time_window.end_minute
            ):
                return None
            for item in schedule_items:
                if self._overlaps(start, end, item.start_minute, item.end_minute):
                    return None
            return start

        start = 0
        if task.time_window is not None:
            start = task.time_window.start_minute

        items = sorted(schedule_items, key=lambda item: item.start_minute)
        while True:
            end = start + task.duration_minutes
            if end > 1440:
                return None
            if task.time_window is not None and end > task.time_window.end_minute:
                return None

            conflict = next(
                (
                    item
                    for item in items
                    if self._overlaps(start, end, item.start_minute, item.end_minute)
                ),
                None,
            )
            if conflict is None:
                return start
            start = conflict.end_minute

    @staticmethod
    def _overlaps(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
        return start_a < end_b and start_b < end_a
