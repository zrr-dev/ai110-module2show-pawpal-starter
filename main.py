from tabulate import tabulate

from pawpal_system import Owner, Pet, Task, Scheduler


def print_tasks(title: str, tasks: list[Task]) -> None:
    """Print a heading followed by a table with one row per task."""
    print(f"\n--- {title} ---")
    if not tasks:
        print("(none)")
        return
    rows = [
        [
            f"{task.due_date:%b %d}",
            task.time,
            task.pet_name,
            task.description,
            task.duration_minutes,
            task.priority,
            task.frequency,
            "done" if task.completed else "open",
        ]
        for task in tasks
    ]
    headers = ["Date", "Time", "Pet", "Task", "Min", "Priority", "Frequency", "Status"]
    print(tabulate(rows, headers=headers, tablefmt="github"))


# 1. Create an Owner and Pets
owner = Owner(name="Alex", available_minutes=60)
dog = Pet(name="Buddy", species="Dog", age=3)
cat = Pet(name="Whiskers", species="Cat", age=5)
owner.add_pet(dog)
owner.add_pet(cat)

# 2. Add Tasks (deliberately out of order, with one overlap)
dog.add_task(Task("Evening Walk", "18:00", duration_minutes=30, priority="Medium", frequency="Daily"))
dog.add_task(Task("Morning Walk", "8:00", duration_minutes=30, priority="High", frequency="Daily"))
cat.add_task(Task("Feed Breakfast", "07:30", duration_minutes=10, priority="High", frequency="Daily"))
cat.add_task(Task("Brush Fur", "08:15", duration_minutes=20, priority="Low", frequency="Weekly"))

scheduler = Scheduler(owner)

# 3. Sorting and filtering
print_tasks("Today's Schedule (sorted by time)", scheduler.sort_by_time())
print_tasks("Sorted by priority, then time", scheduler.sort_by_time(by_priority=True))
print_tasks("Whiskers' tasks only", scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Whiskers")))

# 4. Conflict warnings
print("\n--- Conflict Warnings ---")
for warning in scheduler.detect_conflicts() or ["No conflicts found."]:
    print(f"WARNING: {warning}")

# 5. Daily plan within the owner's available time
print_tasks(f"Daily Plan ({owner.available_minutes} min available)", scheduler.build_daily_plan())

# 6. Next available slot for a new 30-minute task, starting the search at 07:30
slot = scheduler.find_next_available_slot(30, earliest="07:30")
print(f"\nNext free 30-minute slot after 07:30: {slot or 'none today'}")

# 7. Recurring tasks: completing a Daily task queues tomorrow's occurrence
morning_walk = next(t for t in dog.tasks if t.description == "Morning Walk")
next_walk = scheduler.complete_task(morning_walk)
print(f"\nCompleted '{morning_walk.description}'; next occurrence due {next_walk.due_date:%b %d}.")
print_tasks("Buddy's tasks after completing Morning Walk", scheduler.sort_by_time(dog.tasks))
