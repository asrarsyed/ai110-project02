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

    def filter_tasks(self, completed: bool | None, pet: Pet | None) -> list[Task]:
        source = pet.tasks if pet is not None else self.owner.get_all_tasks()
        if completed is None:
            return list(source)
        return [task for task in source if task.is_complete is completed]

    def detect_conflicts(self, schedule_items: list[ScheduleItem]) -> list[str]:
        conflicts: list[str] = []
        items = sorted(schedule_items, key=lambda item: item.start_minute)

        for idx, item in enumerate(items):
            if (
                item.start_minute < 0
                or item.end_minute > 1440
                or item.start_minute >= item.end_minute
            ):
                conflicts.append(f"Invalid time range for task '{item.task.name}'.")

            if idx == 0:
                continue

            prev = items[idx - 1]
            if item.start_minute < prev.end_minute:
                conflicts.append(
                    f"Overlap detected between '{prev.task.name}' and '{item.task.name}'."
                )

        return conflicts

    def handle_recurring_tasks(self, tasks: list[Task]) -> list[Task]:
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
