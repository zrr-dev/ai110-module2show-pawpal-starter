"""PawPal+ core logic: owners, pets, care tasks, and a daily scheduler."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from datetime import date, timedelta
from pathlib import Path

PRIORITY_RANK = {"High": 0, "Medium": 1, "Low": 2}
FREQUENCY_DAYS = {"Once": None, "Daily": 1, "Weekly": 7}
# Alternate spellings accepted for a frequency, mapped to their canonical name.
FREQUENCY_ALIASES = {"One-time": "Once", "One time": "Once", "Onetime": "Once"}

# normalizes the time string to "HH:MM" and validates it is a valid 24-hour time
def _normalize_time(value: str) -> str:
    """Validate a "H:MM" or "HH:MM" string and return it zero-padded as "HH:MM"."""
    if not isinstance(value, str):
        raise ValueError(f"Time must be a string like HH:MM, got {value!r}")
    try:
        hours_text, minutes_text = value.strip().split(":")
        hours, minutes = int(hours_text), int(minutes_text)
    except ValueError:
        raise ValueError(f"Time must look like HH:MM, got {value!r}") from None
    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        raise ValueError(f"Time out of range: {value!r}")
    return f"{hours:02d}:{minutes:02d}"


# eq=False so tasks compare by identity: two identical-looking tasks stay distinct.
@dataclass(eq=False)
class Task:
    """A single pet care activity scheduled at a time of day."""

    description: str
    time: str  # "HH:MM", 24-hour clock
    duration_minutes: int = 0
    priority: str = "Medium"  # "High" | "Medium" | "Low"
    frequency: str = "Daily"  # "Once" | "Daily" | "Weekly"
    due_date: date = field(default_factory=date.today)
    completed: bool = False
    pet_name: str = ""

    def __post_init__(self) -> None:
        """Normalize and validate fields so sorting and comparisons are reliable."""
        self.description = self.description.strip()
        if not self.description:
            raise ValueError("Task description cannot be empty")
        self.time = _normalize_time(self.time)
        self.priority = self.priority.strip().capitalize()
        self.frequency = self.frequency.strip().capitalize()
        self.frequency = FREQUENCY_ALIASES.get(self.frequency, self.frequency)
        if self.priority not in PRIORITY_RANK:
            raise ValueError(f"Priority must be one of {list(PRIORITY_RANK)}")
        if self.frequency not in FREQUENCY_DAYS:
            raise ValueError(f"Frequency must be one of {list(FREQUENCY_DAYS)}")
        if self.duration_minutes < 0:
            raise ValueError("Duration cannot be negative")

    @property
    def start_minutes(self) -> int:
        """Return the start time as minutes after midnight."""
        hours, minutes = self.time.split(":")
        return int(hours) * 60 + int(minutes)

    @property
    def end_minutes(self) -> int:
        """Return the end time as minutes after midnight."""
        return self.start_minutes + self.duration_minutes

    def mark_complete(self) -> Task | None:
        """Mark this task done; return the next occurrence for recurring tasks."""
        # Completing twice would queue a duplicate next occurrence.
        if self.completed:
            raise ValueError(f"{self.description!r} is already completed")
        self.completed = True
        interval = FREQUENCY_DAYS[self.frequency]
        if interval is None:
            return None
        return replace(
            self, due_date=self.due_date + timedelta(days=interval), completed=False
        )

    def overlaps(self, other: Task) -> bool:
        """Return True if this task's time window intersects the other's."""
        if self is other or self.due_date != other.due_date:
            return False
        # Two tasks starting at the same moment conflict even with zero duration.
        if self.start_minutes == other.start_minutes:
            return True
        return (
            self.start_minutes < other.end_minutes
            and other.start_minutes < self.end_minutes
        )

    def to_dict(self) -> dict:
        """Return a JSON-safe dict of this task (the date as an ISO string)."""
        data = asdict(self)
        data["due_date"] = self.due_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        """Rebuild a task from to_dict() output, re-running all validation."""
        return cls(**{**data, "due_date": date.fromisoformat(data["due_date"])})

#creates a Pet class that has a name, species, age, and a list of tasks. It has methods to add, get, remove, and complete tasks.
@dataclass
class Pet:
    """A pet and the care tasks that belong to it."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Reject blank names and negative ages."""
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("Pet name cannot be empty")
        if self.age < 0:
            raise ValueError("Pet age cannot be negative")

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        if task in self.tasks:
            raise ValueError(f"{task.description!r} is already assigned to {self.name}")
        task.pet_name = self.name
        self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return a copy of this pet's task list."""
        return list(self.tasks)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet."""
        self.tasks.remove(task)

    def complete_task(self, task: Task) -> Task | None:
        """Complete a task and queue its next occurrence if it recurs."""
        if task not in self.tasks:
            raise ValueError(f"{task.description!r} does not belong to {self.name}")
        next_task = task.mark_complete()
        if next_task is not None:
            self.add_task(next_task)
        return next_task

    def to_dict(self) -> dict:
        """Return a JSON-safe dict of this pet and its tasks."""
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Pet:
        """Rebuild a pet and its tasks from to_dict() output."""
        pet = cls(name=data["name"], species=data["species"], age=data["age"])
        for task_data in data["tasks"]:
            pet.add_task(Task.from_dict(task_data))
        return pet

#creates an Owner class that has a name, available minutes, and a list of pets. It has methods to add, get, and retrieve all tasks for the owner.
class Owner:
    """A pet owner who manages one or more pets."""

    def __init__(self, name: str, available_minutes: int = 120) -> None:
        if available_minutes < 0:
            raise ValueError("Available minutes cannot be negative")
        self.name = name
        self.available_minutes = available_minutes
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner, rejecting duplicate names."""
        if self.get_pet(pet.name) is not None:
            raise ValueError(f"{self.name} already has a pet named {pet.name}")
        self.pets.append(pet)

    def get_pet(self, name: str) -> Pet | None:
        """Look up a pet by name (case-insensitive)."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.get_tasks()]

    def to_dict(self) -> dict:
        """Return a JSON-safe dict of this owner, their pets, and all tasks."""
        return {
            "name": self.name,
            "available_minutes": self.available_minutes,
            "pets": [pet.to_dict() for pet in self.pets],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Owner:
        """Rebuild an owner and everything they own from to_dict() output."""
        owner = cls(name=data["name"], available_minutes=data["available_minutes"])
        for pet_data in data["pets"]:
            owner.add_pet(Pet.from_dict(pet_data))
        return owner

    def save_to_json(self, path: str | Path) -> None:
        """Write this owner, their pets, and all tasks to a JSON file."""
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load_from_json(cls, path: str | Path) -> Owner:
        """Load an owner saved by save_to_json(); raises FileNotFoundError if missing."""
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

#creates a Scheduler class that organizes an owner's tasks by sorting, filtering, detecting conflicts, and planning. It has methods to sort tasks by time, filter tasks based on pet name, completion status, and date, detect conflicts between tasks, complete a task via its pet, and build a daily plan of open tasks based on priority and available time.
class Scheduler:
    """Organizes an owner's tasks: sorting, filtering, conflict detection, planning."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def _tasks(self, tasks: list[Task] | None) -> list[Task]:
        """Return the given tasks, or all of the owner's tasks when none are given."""
        return self.owner.get_all_tasks() if tasks is None else list(tasks)

    def sort_by_time(
        self, tasks: list[Task] | None = None, by_priority: bool = False
    ) -> list[Task]:
        """Return tasks ordered by date, then start time (earliest first).

        With by_priority=True, tasks are grouped High -> Medium -> Low first,
        and each group is then ordered by date and start time.
        """
        if by_priority:
            key = lambda t: (PRIORITY_RANK[t.priority], t.due_date, t.start_minutes)
        else:
            key = lambda t: (t.due_date, t.start_minutes)
        return sorted(self._tasks(tasks), key=key)

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
        on_date: date | None = None,
    ) -> list[Task]:
        """Return tasks matching every filter that is provided."""
        return [
            task
            for task in self.owner.get_all_tasks()
            if (pet_name is None or task.pet_name.lower() == pet_name.lower())
            and (completed is None or task.completed == completed)
            and (on_date is None or task.due_date == on_date)
        ]

    def detect_conflicts(self, tasks: list[Task] | None = None) -> list[str]:
        """Return a warning message for each pair of overlapping active (incomplete) tasks."""
        active = [task for task in self._tasks(tasks) if not task.completed]
        ordered = self.sort_by_time(active)
        warnings = []
        for i, first in enumerate(ordered):
            for second in ordered[i + 1 :]:
                if first.overlaps(second):
                    warnings.append(
                        f"Conflict on {first.due_date}: "
                        f"{first.pet_name}'s '{first.description}' at {first.time} "
                        f"({first.duration_minutes} min) overlaps "
                        f"{second.pet_name}'s '{second.description}' at {second.time} "
                        f"({second.duration_minutes} min)"
                    )
        return warnings

    def find_next_available_slot(
        self,
        duration_minutes: int,
        tasks: list[Task] | None = None,
        on_date: date | None = None,
        earliest: str = "00:00",
    ) -> str | None:
        """Return the earliest "HH:MM" at or after `earliest` where a task of this
        length fits on the day without overlapping an open task, or None if the
        day has no gap that long before midnight."""
        if duration_minutes <= 0:
            raise ValueError("Duration must be positive to find a slot")
        day = on_date or date.today()
        busy = [
            task
            for task in self.sort_by_time(self._tasks(tasks))
            if task.due_date == day and not task.completed
        ]
        hours, minutes = _normalize_time(earliest).split(":")
        candidate = int(hours) * 60 + int(minutes)
        # Tasks are in start order, so each blocking task pushes the candidate
        # past its end; once a task starts after the gap closes, the gap is free.
        for task in busy:
            if task.start_minutes >= candidate + duration_minutes:
                break
            # Zero-length tasks still claim their start minute (see Task.overlaps).
            candidate = max(candidate, task.end_minutes, task.start_minutes + 1)
        if candidate + duration_minutes > 24 * 60:
            return None
        return f"{candidate // 60:02d}:{candidate % 60:02d}"

    def complete_task(self, task: Task) -> Task | None:
        """Complete a task via its pet so recurring tasks get their next occurrence."""
        pet = self.owner.get_pet(task.pet_name)
        if pet is None:
            raise ValueError(f"No pet named {task.pet_name!r} for this owner")
        return pet.complete_task(task)

    def build_daily_plan(self, on_date: date | None = None) -> list[Task]:
        """Pick the day's open tasks by priority within the owner's time, then order by time."""
        day = on_date or date.today()
        candidates = sorted(
            self.filter_tasks(completed=False, on_date=day),
            key=lambda t: (PRIORITY_RANK[t.priority], t.start_minutes),
        )
        plan: list[Task] = []
        minutes_left = self.owner.available_minutes
        for task in candidates:
            if task.duration_minutes > minutes_left:
                continue
            # A higher-priority task already holds this time slot.
            if any(task.overlaps(chosen) for chosen in plan):
                continue
            plan.append(task)
            minutes_left -= task.duration_minutes
        return self.sort_by_time(plan)
