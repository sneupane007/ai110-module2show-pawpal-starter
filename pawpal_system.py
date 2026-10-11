"""PawPal+ logic layer: backend classes for pets, tasks, and scheduling."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Task:
    """A single pet care activity."""

    title: str
    task_type: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    preferred_time: str = ""
    is_completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass


@dataclass
class Pet:
    """Base pet profile. Subclasses define species and allowed task types."""

    name: str
    age: int = 0
    tasks: List[Task] = field(default_factory=list)

    def species(self) -> str:
        """Return the species name."""
        pass

    def allowed_task_types(self) -> List[str]:
        """Return the task types that make sense for this pet."""
        pass

    def add_task(self, task: Task) -> None:
        """Add a task to this pet."""
        pass

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet."""
        pass


@dataclass
class Dog(Pet):
    def species(self) -> str:
        pass

    def allowed_task_types(self) -> List[str]:
        pass


@dataclass
class Cat(Pet):
    def species(self) -> str:
        pass

    def allowed_task_types(self) -> List[str]:
        pass


@dataclass
class OtherPet(Pet):
    custom_species: str = ""

    def species(self) -> str:
        pass

    def allowed_task_types(self) -> List[str]:
        pass


@dataclass
class Owner:
    """The pet owner and their daily constraints."""

    name: str
    available_minutes: int = 120
    day_start: str = "08:00"
    day_end: str = "20:00"
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner."""
        pass

    def get_all_tasks(self) -> List[Task]:
        """Return every task across all of the owner's pets."""
        pass


@dataclass
class ScheduledTask:
    """A task placed at a specific time for a specific pet."""

    task: Task
    pet: Pet
    start_time: str
    end_time: str
    reason: str = ""


@dataclass
class DailyPlan:
    """The scheduler's output: what was scheduled, what was skipped, and why."""

    scheduled: List[ScheduledTask] = field(default_factory=list)
    skipped: List[Task] = field(default_factory=list)
    total_minutes: int = 0

    def explain(self) -> str:
        """Return a human-readable explanation of the plan."""
        pass


class Scheduler:
    """Builds a DailyPlan for an owner's pets based on time and priority."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def generate_plan(self) -> DailyPlan:
        """Create a daily plan from the owner's tasks and constraints."""
        pass

    def _sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """Order tasks by priority, then preferred time."""
        pass

    def _fits_in_time(self, task: Task, minutes_left: int) -> bool:
        """Return True if the task fits in the remaining time."""
        pass

    def _detect_conflicts(self, plan: DailyPlan) -> List[Task]:
        """Return tasks whose scheduled times overlap."""
        pass
