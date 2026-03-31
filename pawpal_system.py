from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any


class Recurrence(Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    ONE_TIME = "ONE_TIME"


@dataclass
class TimeWindow:
    start_minute: int
    end_minute: int

    def contains(self, minute: int) -> bool:
        pass

    def validate(self) -> bool:
        pass


@dataclass
class Task:
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
        pass

    def reschedule_next(self, reference_date: date) -> None:
        pass

    def validate(self) -> bool:
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int | None = None
    medical_needs: str | None = None
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task: Task) -> None:
        pass

    def get_tasks(self) -> list[Task]:
        pass


@dataclass
class Owner:
    name: str
    available_time_minutes: int
    preferences: dict[str, Any] | None = None
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def remove_pet(self, pet: Pet) -> None:
        pass

    def get_all_tasks(self) -> list[Task]:
        pass


@dataclass
class ScheduleItem:
    pet: Pet
    task: Task
    start_minute: int
    end_minute: int
    reason: str


@dataclass
class Scheduler:
    owner: Owner
    schedule_date: date | None = None

    def generate_schedule(self) -> list[ScheduleItem]:
        pass

    def get_candidate_tasks(self) -> list[Task]:
        pass

    def get_available_time_minutes(self) -> int:
        pass

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        pass

    def filter_tasks(self, completed: bool | None, pet: Pet | None) -> list[Task]:
        pass

    def detect_conflicts(self, schedule_items: list[ScheduleItem]) -> list[str]:
        pass

    def handle_recurring_tasks(self, tasks: list[Task]) -> list[Task]:
        pass
