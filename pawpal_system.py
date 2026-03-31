from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Recurrence(Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    ONE_TIME = "ONE_TIME"


@dataclass
class TimeWindow:
    start: str
    end: str

    def contains(self, time: str) -> bool:
        pass


@dataclass
class Task:
    name: str
    duration_minutes: int
    priority: int
    fixed_time: str | None = None
    time_window: TimeWindow | None = None
    recurrence: Recurrence = Recurrence.ONE_TIME
    is_complete: bool = False
    is_critical: bool = False

    def mark_complete(self) -> None:
        pass

    def reschedule_next(self) -> None:
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
    task: Task
    start_time: str
    end_time: str
    reason: str


@dataclass
class Scheduler:
    owner: Owner
    tasks: list[Task] = field(default_factory=list)
    available_time_minutes: int = 0

    def generate_schedule(self) -> list[ScheduleItem]:
        pass

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        pass

    def filter_tasks(self, status: str, pet: Pet | None) -> list[Task]:
        pass

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        pass

    def handle_recurring_tasks(self, tasks: list[Task]) -> list[Task]:
        pass
