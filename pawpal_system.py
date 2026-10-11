"""PawPal+ logic layer: backend classes for pets, tasks, and scheduling.

All times are stored as minutes since midnight (e.g. 08:00 -> 480).
"""

from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from enum import Enum
from itertools import combinations
from typing import List, Optional, Tuple

COMMON_TASK_TYPES = ["feeding", "grooming", "medication", "play"]


def format_time(minutes: int) -> str:
    """Convert minutes since midnight to an HH:MM string."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def parse_time(text: str) -> int:
    """Convert an "HH:MM" string to minutes since midnight (inverse of format_time).

    Example: parse_time("08:30") -> 510. Raises ValueError on malformed input.
    """
    hours, minutes = text.split(":")
    return int(hours) * 60 + int(minutes)


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass(eq=False)  # identity equality: two identical-looking tasks stay distinct and hashable
class Task:
    """A single pet care activity."""

    title: str
    task_type: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    preferred_time: Optional[int] = None  # minutes since midnight; None = no preference
    frequency: str = "once"  # "once", "daily", or "weekly"
    is_completed: bool = False
    due_date: Optional[date] = None  # None = today; used to date recurring tasks

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task as done and build its next occurrence if it recurs.

        A "daily" task comes back due today + 1 day and a "weekly" task today + 7
        days (via timedelta, so month and year rollovers are handled). The copy is
        a fresh, not-completed Task with every other field unchanged. A "once"
        task returns None. This method does not add the copy to any pet; use
        Pet.complete_task or Scheduler.mark_task_complete for that.
        """
        self.is_completed = True
        step = {"daily": 1, "weekly": 7}.get(self.frequency)
        if step is None:
            return None
        return replace(
            self, is_completed=False, due_date=date.today() + timedelta(days=step)
        )


@dataclass
class Pet:
    """Base pet profile. Subclasses define species and allowed task types."""

    name: str
    age: int = 0
    tasks: List[Task] = field(default_factory=list)

    def species(self) -> str:
        """Return the species name."""
        return "pet"

    def allowed_task_types(self) -> List[str]:
        """Return the task types that make sense for this pet."""
        return list(COMMON_TASK_TYPES)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet. Raises ValueError if the type isn't allowed."""
        if task.task_type not in self.allowed_task_types():
            raise ValueError(
                f"{self.name} ({self.species()}) cannot have a '{task.task_type}' task"
            )
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet."""
        self.tasks.remove(task)

    def complete_task(self, task: Task) -> Optional[Task]:
        """Complete a task and, if it recurs, add its next occurrence to this pet.

        The finished task stays in the list, so a recurring task leaves one done
        copy and one pending copy. Returns the new Task, or None for a "once" task.
        """
        following = task.mark_complete()
        if following is not None:
            self.tasks.append(following)
        return following


@dataclass
class Dog(Pet):
    """A dog, which can also have walks and training."""

    def species(self) -> str:
        """Return "dog"."""
        return "dog"

    def allowed_task_types(self) -> List[str]:
        """Return the common task types plus walk and training."""
        return COMMON_TASK_TYPES + ["walk", "training"]


@dataclass
class Cat(Pet):
    """A cat, which can also have litter box care."""

    def species(self) -> str:
        """Return "cat"."""
        return "cat"

    def allowed_task_types(self) -> List[str]:
        """Return the common task types plus litter box."""
        return COMMON_TASK_TYPES + ["litter box"]


@dataclass
class OtherPet(Pet):
    """Any other kind of pet, with an optional custom species name."""

    custom_species: str = ""

    def species(self) -> str:
        """Return the custom species name, or "other" if none was given."""
        return self.custom_species or "other"

    def allowed_task_types(self) -> List[str]:
        """Return only the common task types."""
        return list(COMMON_TASK_TYPES)


@dataclass
class Owner:
    """The pet owner and their daily constraints."""

    name: str
    available_minutes: int = 120
    day_start: int = 480  # 08:00
    day_end: int = 1200  # 20:00
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner."""
        self.pets.remove(pet)

    def get_all_tasks(self) -> List[Tuple[Pet, Task]]:
        """Return every (pet, task) pair across all of the owner's pets."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


def sort_by_time(pairs: List[Tuple[Pet, Task]]) -> List[Tuple[Pet, Task]]:
    """Order (pet, task) pairs by preferred time, earliest first.

    The key is (no preference?, minutes), so tasks with no preferred time sort
    after every timed task. Sorting is stable: ties keep their original order.
    Returns a new list; the input is not modified. O(n log n).
    """
    return sorted(
        pairs,
        key=lambda pt: (pt[1].preferred_time is None, pt[1].preferred_time or 0),
    )


def filter_tasks(
    owner: Owner, pet_name: Optional[str] = None, completed: Optional[bool] = None
) -> List[Tuple[Pet, Task]]:
    """Return the owner's (pet, task) pairs, optionally limited by pet name and status.

    Args:
        pet_name: keep only this pet's tasks; None keeps every pet.
        completed: True keeps finished tasks, False keeps pending ones,
            None keeps both.

    Filters combine (both must match). Single O(n) pass.
    """
    return [
        (pet, task)
        for pet, task in owner.get_all_tasks()
        if (pet_name is None or pet.name == pet_name)
        and (completed is None or task.is_completed == completed)
    ]


def find_conflicts(pairs: List[Tuple[Pet, Task]]) -> List[str]:
    """Return a warning string for each pair of pending tasks whose windows overlap.

    A task's window is [preferred_time, preferred_time + duration). Two windows
    conflict when each starts before the other ends, so identical start times
    conflict, partial overlaps conflict, and back-to-back tasks do not. Each
    warning says whether the pair belongs to the same pet or different pets.

    Completed tasks and tasks with no preferred time are ignored. This reports
    what the owner asked for, not where the scheduler places tasks. It never
    raises and never changes the tasks. Pairwise check, O(n^2).
    """
    timed = [
        (pet, task)
        for pet, task in pairs
        if task.preferred_time is not None and not task.is_completed
    ]
    warnings = []
    for (pet_a, a), (pet_b, b) in combinations(timed, 2):
        end_a = a.preferred_time + a.duration_minutes
        end_b = b.preferred_time + b.duration_minutes
        if a.preferred_time < end_b and b.preferred_time < end_a:
            who = "same pet" if pet_a is pet_b else "different pets"
            warnings.append(
                f"Conflict ({who}): {a.title} ({pet_a.name}) "
                f"{format_time(a.preferred_time)}-{format_time(end_a)} overlaps "
                f"{b.title} ({pet_b.name}) "
                f"{format_time(b.preferred_time)}-{format_time(end_b)}"
            )
    return warnings


@dataclass
class ScheduledTask:
    """A task placed at a specific time for a specific pet."""

    task: Task
    pet: Pet
    start_time: int  # minutes since midnight
    end_time: int
    reason: str = ""


@dataclass
class SkippedTask:
    """A task that did not make it into the plan, and why."""

    task: Task
    pet: Pet
    reason: str


@dataclass
class DailyPlan:
    """The scheduler's output: what was scheduled, what was skipped, and why."""

    scheduled: List[ScheduledTask] = field(default_factory=list)
    skipped: List[SkippedTask] = field(default_factory=list)
    total_minutes: int = 0

    def explain(self, available_minutes: Optional[int] = None) -> str:
        """Return the plan as a readable table, with reasons and skipped tasks."""
        rule = "-" * 50
        lines = [
            f" {'TIME':<13} {'TASK':<18} {'PET':<8} {'PRIORITY':<9} MIN",
            " " + rule,
        ]
        for s in sorted(self.scheduled, key=lambda s: s.start_time):
            span = f"{format_time(s.start_time)}-{format_time(s.end_time)}"
            lines.append(
                f" {span:<13} {s.task.title:<18} {s.pet.name:<8} "
                f"{s.task.priority.name:<9} {s.task.duration_minutes:>3}"
            )
        lines.append(" " + rule)

        used = f"{self.total_minutes}"
        if available_minutes is not None:
            used += f" of {available_minutes}"
        lines.append(f" Scheduled: {len(self.scheduled)} tasks, {used} min used")

        if self.scheduled:
            lines.append("")
            lines.append(" Why:")
            for s in sorted(self.scheduled, key=lambda s: s.start_time):
                lines.append(f"   - {s.task.title} ({s.pet.name}): {s.reason}")

        if self.skipped:
            lines.append("")
            lines.append(f" Skipped ({len(self.skipped)}):")
            for k in self.skipped:
                lines.append(f"   - {k.task.title} ({k.pet.name}): {k.reason}")

        return "\n".join(lines)


class Scheduler:
    """Builds a DailyPlan for an owner's pets based on time and priority."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler for the given owner."""
        self.owner = owner

    def generate_plan(self) -> DailyPlan:
        """Create a daily plan from the owner's tasks and constraints.

        Tasks are taken highest priority first, then by preferred time. Each is
        placed in the earliest free slot at or after its preferred time. A task
        that does not fit is skipped, and smaller later tasks can still fit.
        """
        plan = DailyPlan()
        pending: List[Tuple[Pet, Task]] = []

        for pet, task in self.owner.get_all_tasks():
            if task.is_completed:
                plan.skipped.append(SkippedTask(task, pet, "already completed"))
            elif task.task_type not in pet.allowed_task_types():
                plan.skipped.append(
                    SkippedTask(task, pet, f"'{task.task_type}' not valid for a {pet.species()}")
                )
            else:
                pending.append((pet, task))

        for pet, task in self._sort_tasks(pending):
            slot = self._place_task(task, plan)
            if slot is None:
                plan.skipped.append(
                    SkippedTask(task, pet, "not enough time left in the day")
                )
                continue

            start, end = slot
            reason = f"{task.priority.name.lower()} priority"
            if task.preferred_time is None:
                reason += ", earliest open slot"
            elif start == task.preferred_time:
                reason += f", at preferred time {format_time(start)}"
            else:
                reason += f", moved from preferred {format_time(task.preferred_time)}"

            plan.scheduled.append(ScheduledTask(task, pet, start, end, reason))
            plan.total_minutes += task.duration_minutes

        plan.scheduled.sort(key=lambda s: s.start_time)
        return plan

    def sort_by_time(
        self, pairs: Optional[List[Tuple[Pet, Task]]] = None
    ) -> List[Tuple[Pet, Task]]:
        """Return (pet, task) pairs ordered by preferred time, earliest first.

        Sorts the given pairs, or all of the owner's tasks when none are passed.
        Tasks with no preferred time go last. See the module-level sort_by_time.
        """
        return sort_by_time(self.owner.get_all_tasks() if pairs is None else pairs)

    def find_conflicts(self) -> List[str]:
        """Return a warning for each pair of the owner's pending tasks that overlap.

        Lightweight by design: it returns messages instead of raising, so the
        caller can print them and still call generate_plan. Overlap rules are
        described in the module-level find_conflicts.
        """
        return find_conflicts(self.owner.get_all_tasks())

    def mark_task_complete(self, pet: Pet, task: Task) -> Optional[Task]:
        """Complete a task and return its next occurrence, or None if it doesn't recur.

        A daily task is re-created due tomorrow and a weekly task due in 7 days;
        the new task is added to the given pet. See Task.mark_complete.
        """
        return pet.complete_task(task)

    def filter_tasks(
        self, pet_name: Optional[str] = None, completed: Optional[bool] = None
    ) -> List[Tuple[Pet, Task]]:
        """Return the owner's (pet, task) pairs filtered by pet name and/or status.

        pet_name=None keeps all pets; completed=None keeps done and pending
        tasks. The result can be passed to sort_by_time. See filter_tasks.
        """
        return filter_tasks(self.owner, pet_name, completed)

    def _sort_tasks(
        self, pairs: List[Tuple[Pet, Task]]
    ) -> List[Tuple[Pet, Task]]:
        """Order (pet, task) pairs by priority (highest first), then preferred time."""
        no_preference = 24 * 60
        return sorted(
            pairs,
            key=lambda pt: (
                -pt[1].priority.value,
                pt[1].preferred_time if pt[1].preferred_time is not None else no_preference,
            ),
        )

    def _place_task(self, task: Task, plan: DailyPlan) -> Optional[Tuple[int, int]]:
        """Return (start, end) in the earliest free slot at or after the task's
        preferred time, or None if it exceeds the time budget or the day window."""
        if plan.total_minutes + task.duration_minutes > self.owner.available_minutes:
            return None

        start = self.owner.day_start
        if task.preferred_time is not None:
            start = max(start, task.preferred_time)

        for s in sorted(plan.scheduled, key=lambda s: s.start_time):
            if start + task.duration_minutes <= s.start_time:
                break
            start = max(start, s.end_time)

        end = start + task.duration_minutes
        if end > self.owner.day_end:
            return None
        return start, end
