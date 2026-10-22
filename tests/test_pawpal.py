"""Automated tests for PawPal+ core logic (pawpal_system.py).

Sections:
    1. Core behavior (tasks and pets)
    2. Sorting (time and priority)       -> Scheduler.sort_by_time
    3. Filtering                         -> Scheduler.filter_tasks
    4. Recurrence logic                  -> Task.mark_complete / Scheduler.complete_task
    5. Conflict detection                -> Scheduler.detect_conflicts
    6. Daily plan and free slots         -> Scheduler.build_daily_plan / find_next_available_slot
    7. Input guardrails / edge cases     -> ValueError on bad input
    8. Persistence                       -> Owner.save_to_json / Owner.load_from_json
"""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task

DAY = date(2026, 1, 1)


@pytest.fixture
def owner_with_pets():
    """An owner with a dog (Buddy) and a cat (Whiskers) and no tasks yet."""
    owner = Owner(name="Alex", available_minutes=120)
    dog = Pet(name="Buddy", species="Dog", age=3)
    cat = Pet(name="Whiskers", species="Cat", age=5)
    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner, dog, cat


# ---------------------------------------------------------------------------
# 1. Core behavior
# ---------------------------------------------------------------------------

def test_mark_complete():
    # Verify that calling mark_complete() changes task status to True
    task = Task(description="Grooming", time="10:00", frequency="Daily", pet_name="Buddy")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task():
    # Verify that adding a task increases the pet's task count
    pet = Pet(name="Buddy", species="Dog")
    assert len(pet.tasks) == 0

    task = Task(description="Morning Walk", time="08:00", frequency="Daily", pet_name="Buddy")
    pet.add_task(task)
    assert len(pet.tasks) == 1
    assert pet.tasks[0].description == "Morning Walk"


def test_add_task_tags_pet_name_and_owner_sees_all_tasks(owner_with_pets):
    # Adding a task stamps it with the pet's name, and the owner aggregates across pets
    owner, dog, cat = owner_with_pets
    walk = Task(description="Walk", time="08:00")
    feed = Task(description="Feed", time="09:00")
    dog.add_task(walk)
    cat.add_task(feed)
    assert walk.pet_name == "Buddy" and feed.pet_name == "Whiskers"
    assert owner.get_all_tasks() == [walk, feed]


# ---------------------------------------------------------------------------
# 2. Sorting and chronological order
# ---------------------------------------------------------------------------

def test_sort_by_time_orders_chronologically():
    owner = Owner(name="Alex")
    pet = Pet(name="Buddy", species="Dog")
    owner.add_pet(pet)
    for t in ["18:00", "7:30", "12:15"]:
        pet.add_task(Task(description=f"Task {t}", time=t, frequency="Once"))
    times = [task.time for task in Scheduler(owner).sort_by_time()]
    assert times == ["07:30", "12:15", "18:00"]


def test_sort_by_time_avoids_string_comparison_bug(owner_with_pets):
    # "9:00" < "10:00" numerically even though "9" > "1" as a string
    owner, dog, _ = owner_with_pets
    dog.add_task(Task(description="Late", time="10:00"))
    dog.add_task(Task(description="Early", time="9:00"))
    ordered = Scheduler(owner).sort_by_time()
    assert [t.description for t in ordered] == ["Early", "Late"]


def test_sort_by_time_orders_by_date_before_time(owner_with_pets):
    # A task tomorrow morning comes after a task today evening
    owner, dog, cat = owner_with_pets
    tomorrow_morning = Task(description="Walk", time="07:00", due_date=DAY + timedelta(days=1))
    today_evening = Task(description="Feed", time="19:00", due_date=DAY)
    dog.add_task(tomorrow_morning)
    cat.add_task(today_evening)
    assert Scheduler(owner).sort_by_time() == [today_evening, tomorrow_morning]


def test_sort_by_time_empty_and_does_not_mutate_input(owner_with_pets):
    owner, _, _ = owner_with_pets
    scheduler = Scheduler(owner)
    assert scheduler.sort_by_time() == []
    tasks = [Task(description="B", time="12:00"), Task(description="A", time="08:00")]
    original = list(tasks)
    scheduler.sort_by_time(tasks)
    assert tasks == original


def test_sort_by_priority_then_time(owner_with_pets):
    owner, dog, cat = owner_with_pets
    low_early = Task(description="Play", time="07:00", priority="Low", due_date=DAY)
    high_late = Task(description="Meds", time="20:00", priority="High", due_date=DAY)
    high_early = Task(description="Feed", time="9:00", priority="High", due_date=DAY)
    medium = Task(description="Walk", time="12:00", priority="Medium", due_date=DAY)
    dog.add_task(low_early)
    dog.add_task(high_late)
    cat.add_task(high_early)
    cat.add_task(medium)
    scheduler = Scheduler(owner)
    assert scheduler.sort_by_time(by_priority=True) == [high_early, high_late, medium, low_early]
    # The default stays purely chronological
    assert scheduler.sort_by_time() == [low_early, high_early, medium, high_late]


# ---------------------------------------------------------------------------
# 3. Filtering
# ---------------------------------------------------------------------------

def test_filter_by_pet_and_status():
    owner = Owner(name="Alex")
    dog, cat = Pet(name="Buddy", species="Dog"), Pet(name="Whiskers", species="Cat")
    owner.add_pet(dog)
    owner.add_pet(cat)
    walk = Task(description="Walk", time="08:00", frequency="Once")
    feed = Task(description="Feed", time="09:00", frequency="Once")
    dog.add_task(walk)
    cat.add_task(feed)
    walk.mark_complete()
    scheduler = Scheduler(owner)
    assert scheduler.filter_tasks(pet_name="buddy") == [walk]
    assert scheduler.filter_tasks(completed=False) == [feed]


def test_filter_by_date_and_unknown_pet(owner_with_pets):
    owner, dog, _ = owner_with_pets
    today = Task(description="Walk", time="08:00", due_date=DAY)
    later = Task(description="Bath", time="08:00", due_date=DAY + timedelta(days=7))
    dog.add_task(today)
    dog.add_task(later)
    scheduler = Scheduler(owner)
    assert scheduler.filter_tasks(on_date=DAY) == [today]
    assert scheduler.filter_tasks(pet_name="Nobody") == []


# ---------------------------------------------------------------------------
# 4. Recurrence logic
# ---------------------------------------------------------------------------

def test_completing_daily_task_schedules_next_day():
    # Completing a recurring task via the Scheduler adds the next occurrence to the pet
    owner = Owner(name="Alex")
    pet = Pet(name="Buddy", species="Dog")
    owner.add_pet(pet)
    task = Task(description="Morning Walk", time="08:00", frequency="Daily", due_date=DAY)
    pet.add_task(task)
    next_task = Scheduler(owner).complete_task(task)
    assert task.completed is True
    assert next_task.due_date == DAY + timedelta(days=1)
    assert next_task.completed is False
    assert next_task in pet.tasks


def test_weekly_task_recurs_in_seven_days():
    task = Task(description="Bath", time="10:00", frequency="Weekly", due_date=DAY)
    assert task.mark_complete().due_date == date(2026, 1, 8)


def test_next_occurrence_keeps_task_details(owner_with_pets):
    # The new occurrence is a distinct object that copies time, duration, priority, pet
    owner, dog, _ = owner_with_pets
    task = Task(description="Meds", time="21:00", duration_minutes=5, priority="High",
                frequency="Daily", due_date=DAY)
    dog.add_task(task)
    nxt = Scheduler(owner).complete_task(task)
    assert nxt is not task
    assert (nxt.description, nxt.time, nxt.duration_minutes, nxt.priority, nxt.pet_name) == \
        ("Meds", "21:00", 5, "High", "Buddy")


def test_recurrence_crosses_month_and_year_boundaries():
    daily = Task(description="Walk", time="08:00", frequency="Daily", due_date=date(2026, 12, 31))
    weekly = Task(description="Bath", time="10:00", frequency="Weekly", due_date=date(2026, 2, 25))
    assert daily.mark_complete().due_date == date(2027, 1, 1)
    assert weekly.mark_complete().due_date == date(2026, 3, 4)


def test_one_time_frequency_alias():
    # "One-time" is accepted and stored as the canonical "Once"; it does not recur
    task = Task(description="Vet Visit", time="09:00", frequency="One-time")
    assert task.frequency == "Once"
    assert task.mark_complete() is None


def test_completing_once_task_via_scheduler_adds_nothing(owner_with_pets):
    owner, dog, _ = owner_with_pets
    task = Task(description="Vet Visit", time="09:00", frequency="Once")
    dog.add_task(task)
    assert Scheduler(owner).complete_task(task) is None
    assert dog.tasks == [task]


# ---------------------------------------------------------------------------
# 5. Conflict detection
# ---------------------------------------------------------------------------

def test_same_time_slot_conflict_warning():
    owner = Owner(name="Alex")
    dog, cat = Pet(name="Buddy", species="Dog"), Pet(name="Whiskers", species="Cat")
    owner.add_pet(dog)
    owner.add_pet(cat)
    dog.add_task(Task(description="Walk", time="08:00", frequency="Once"))
    cat.add_task(Task(description="Feed", time="08:00", frequency="Once"))
    warnings = Scheduler(owner).detect_conflicts()
    assert len(warnings) == 1 and "08:00" in warnings[0]


def test_overlapping_duration_windows_conflict(owner_with_pets):
    # 08:00-08:30 walk overlaps a 08:15 feeding even though start times differ
    owner, dog, cat = owner_with_pets
    dog.add_task(Task(description="Walk", time="08:00", duration_minutes=30))
    cat.add_task(Task(description="Feed", time="08:15", duration_minutes=10))
    warnings = Scheduler(owner).detect_conflicts()
    assert len(warnings) == 1
    assert "Buddy's 'Walk'" in warnings[0] and "Whiskers's 'Feed'" in warnings[0]


def test_back_to_back_tasks_do_not_conflict(owner_with_pets):
    # End time is exclusive: 08:00-08:30 and 08:30-08:45 touch but don't overlap
    owner, dog, cat = owner_with_pets
    dog.add_task(Task(description="Walk", time="08:00", duration_minutes=30))
    cat.add_task(Task(description="Feed", time="08:30", duration_minutes=15))
    assert Scheduler(owner).detect_conflicts() == []


def test_same_time_on_different_days_does_not_conflict(owner_with_pets):
    owner, dog, cat = owner_with_pets
    dog.add_task(Task(description="Walk", time="08:00", due_date=DAY))
    cat.add_task(Task(description="Feed", time="08:00", due_date=DAY + timedelta(days=1)))
    assert Scheduler(owner).detect_conflicts() == []


def test_completed_tasks_do_not_conflict():
    # Only active (incomplete) tasks are checked for double-booking
    owner = Owner(name="Alex")
    pet = Pet(name="Buddy", species="Dog")
    owner.add_pet(pet)
    walk = Task(description="Walk", time="08:00", duration_minutes=30, frequency="Once")
    feed = Task(description="Feed", time="08:10", duration_minutes=5, frequency="Once")
    pet.add_task(walk)
    pet.add_task(feed)
    scheduler = Scheduler(owner)
    assert len(scheduler.detect_conflicts()) == 1
    walk.mark_complete()
    assert scheduler.detect_conflicts(owner.get_all_tasks()) == []


def test_three_way_overlap_reports_each_pair(owner_with_pets):
    owner, dog, cat = owner_with_pets
    dog.add_task(Task(description="Walk", time="08:00", duration_minutes=60))
    dog.add_task(Task(description="Brush", time="08:20", duration_minutes=10))
    cat.add_task(Task(description="Feed", time="08:40", duration_minutes=10))
    # Walk overlaps Brush and Feed; Brush (08:20-08:30) and Feed (08:40) do not overlap
    assert len(Scheduler(owner).detect_conflicts()) == 2


# ---------------------------------------------------------------------------
# 6. Daily plan
# ---------------------------------------------------------------------------

def test_daily_plan_respects_priority_and_time_budget(owner_with_pets):
    owner, dog, cat = owner_with_pets
    owner.available_minutes = 60
    high = Task(description="Meds", time="09:00", duration_minutes=40, priority="High", due_date=DAY)
    low = Task(description="Play", time="07:00", duration_minutes=40, priority="Low", due_date=DAY)
    med = Task(description="Feed", time="18:00", duration_minutes=15, priority="Medium", due_date=DAY)
    dog.add_task(high)
    dog.add_task(low)
    cat.add_task(med)
    plan = Scheduler(owner).build_daily_plan(DAY)
    # Low-priority Play no longer fits after High + Medium; result is in time order
    assert plan == [high, med]


def test_daily_plan_skips_overlap_with_higher_priority(owner_with_pets):
    owner, dog, cat = owner_with_pets
    high = Task(description="Vet", time="10:00", duration_minutes=30, priority="High", due_date=DAY)
    low = Task(description="Groom", time="10:15", duration_minutes=15, priority="Low", due_date=DAY)
    dog.add_task(high)
    cat.add_task(low)
    assert Scheduler(owner).build_daily_plan(DAY) == [high]


def test_next_available_slot_finds_first_gap(owner_with_pets):
    owner, dog, cat = owner_with_pets
    dog.add_task(Task(description="Walk", time="08:00", duration_minutes=30, due_date=DAY))
    cat.add_task(Task(description="Feed", time="08:45", duration_minutes=15, due_date=DAY))
    dog.add_task(Task(description="Play", time="09:15", duration_minutes=60, due_date=DAY))
    scheduler = Scheduler(owner)
    # 08:30-08:45 fits 15 minutes exactly (back-to-back is allowed) but not 20
    assert scheduler.find_next_available_slot(15, on_date=DAY, earliest="08:00") == "08:30"
    assert scheduler.find_next_available_slot(20, on_date=DAY, earliest="08:00") == "10:15"
    # Before the first task, the earliest time itself is free
    assert scheduler.find_next_available_slot(30, on_date=DAY, earliest="07:00") == "07:00"


def test_next_available_slot_ignores_other_days_and_completed(owner_with_pets):
    owner, dog, _ = owner_with_pets
    dog.add_task(Task(description="Vet", time="09:00", duration_minutes=60, due_date=DAY + timedelta(days=1)))
    done = Task(description="Walk", time="09:00", duration_minutes=60, due_date=DAY, completed=True)
    dog.add_task(done)
    assert Scheduler(owner).find_next_available_slot(30, on_date=DAY, earliest="09:00") == "09:00"


def test_next_available_slot_none_when_day_is_full(owner_with_pets):
    owner, dog, _ = owner_with_pets
    dog.add_task(Task(description="Sleep", time="22:00", duration_minutes=120, due_date=DAY))
    scheduler = Scheduler(owner)
    assert scheduler.find_next_available_slot(30, on_date=DAY, earliest="22:00") is None
    # A zero-minute task still claims its start time
    dog.add_task(Task(description="Pill", time="07:00", due_date=DAY))
    assert scheduler.find_next_available_slot(10, on_date=DAY, earliest="07:00") == "07:01"
    with pytest.raises(ValueError):
        scheduler.find_next_available_slot(0, on_date=DAY)


# ---------------------------------------------------------------------------
# 7. Input guardrails / edge cases
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_time", ["8am", "25:00", "12:60", "8", "ab:cd", "", 800, None])
def test_invalid_time_formats_raise_value_error(bad_time):
    with pytest.raises(ValueError):
        Task(description="Walk", time=bad_time)


def test_time_is_normalized_to_hh_mm():
    assert Task(description="Walk", time=" 7:05 ").time == "07:05"


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_description_raises_value_error(blank):
    with pytest.raises(ValueError):
        Task(description=blank, time="08:00")


def test_negative_pet_age_raises_value_error():
    with pytest.raises(ValueError):
        Pet(name="Buddy", species="Dog", age=-1)


def test_blank_pet_name_raises_value_error():
    with pytest.raises(ValueError):
        Pet(name="  ", species="Dog")


def test_duplicate_pet_name_raises_value_error():
    owner = Owner(name="Alex")
    owner.add_pet(Pet(name="Buddy", species="Dog"))
    with pytest.raises(ValueError):
        owner.add_pet(Pet(name="buddy", species="Cat"))
    assert len(owner.pets) == 1


def test_double_completion_raises_value_error(owner_with_pets):
    # A second completion must not queue a duplicate next occurrence
    owner, dog, _ = owner_with_pets
    task = Task(description="Walk", time="08:00", frequency="Daily")
    dog.add_task(task)
    scheduler = Scheduler(owner)
    scheduler.complete_task(task)
    with pytest.raises(ValueError):
        scheduler.complete_task(task)
    assert len(dog.tasks) == 2


def test_other_invalid_inputs_raise_value_error(owner_with_pets):
    owner, dog, cat = owner_with_pets
    with pytest.raises(ValueError):
        Task(description="Walk", time="08:00", duration_minutes=-5)
    with pytest.raises(ValueError):
        Task(description="Walk", time="08:00", priority="Urgent")
    with pytest.raises(ValueError):
        Task(description="Walk", time="08:00", frequency="Monthly")
    with pytest.raises(ValueError):
        Owner(name="Alex", available_minutes=-1)
    task = Task(description="Walk", time="08:00")
    dog.add_task(task)
    with pytest.raises(ValueError):
        dog.add_task(task)  # same task twice
    with pytest.raises(ValueError):
        cat.complete_task(task)  # task belongs to Buddy, not Whiskers


# ---------------------------------------------------------------------------
# 8. Persistence
# ---------------------------------------------------------------------------


def test_save_and_load_round_trip(owner_with_pets, tmp_path):
    owner, dog, cat = owner_with_pets
    walk = Task(description="Walk", time="8:00", duration_minutes=30, priority="High", due_date=DAY)
    dog.add_task(walk)
    cat.add_task(Task(description="Brush", time="09:00", frequency="Weekly", due_date=DAY))
    Scheduler(owner).complete_task(walk)  # leaves a done task plus tomorrow's occurrence
    path = tmp_path / "data.json"

    owner.save_to_json(path)
    loaded = Owner.load_from_json(path)

    assert loaded.name == "Alex" and loaded.available_minutes == 120
    assert [(p.name, p.species, p.age) for p in loaded.pets] == [("Buddy", "Dog", 3), ("Whiskers", "Cat", 5)]
    assert [t.to_dict() for t in loaded.get_all_tasks()] == [t.to_dict() for t in owner.get_all_tasks()]
    assert loaded.get_pet("Buddy").tasks[1].due_date == DAY + timedelta(days=1)


def test_load_rejects_missing_or_invalid_data(tmp_path):
    with pytest.raises(FileNotFoundError):
        Owner.load_from_json(tmp_path / "missing.json")
    bad = tmp_path / "bad.json"
    bad.write_text(
        '{"name": "Alex", "available_minutes": 60, "pets": [{"name": "Buddy", "species": "Dog", "age": 3, '
        '"tasks": [{"description": "Walk", "time": "8am", "duration_minutes": 0, "priority": "High", '
        '"frequency": "Daily", "due_date": "2026-01-01", "completed": false, "pet_name": "Buddy"}]}]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        Owner.load_from_json(bad)  # loading re-runs the same guardrails as the UI
