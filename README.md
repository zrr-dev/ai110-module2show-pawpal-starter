# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Running `python main.py` prints the owner's tasks across all pets:

```
--- Today's Schedule ---
- [Buddy] Morning Walk at 08:00 (Completed: False)
- [Buddy] Evening Walk at 18:00 (Completed: False)
- [Whiskers] Feed Breakfast at 07:30 (Completed: False)
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest

# Run with coverage:
python -m pytest --cov
```

All **10/10 tests pass**:

```
tests/test_pawpal.py::test_mark_complete PASSED                          [ 10%]
tests/test_pawpal.py::test_add_task PASSED                               [ 20%]
tests/test_pawpal.py::test_one_time_frequency_alias PASSED               [ 30%]
tests/test_pawpal.py::test_completing_daily_task_schedules_next_day PASSED [ 40%]
tests/test_pawpal.py::test_completed_tasks_do_not_conflict PASSED        [ 50%]
tests/test_pawpal.py::test_sort_by_time_orders_chronologically PASSED    [ 60%]
tests/test_pawpal.py::test_filter_by_pet_and_status PASSED               [ 70%]
tests/test_pawpal.py::test_weekly_task_recurs_in_seven_days PASSED       [ 80%]
tests/test_pawpal.py::test_same_time_slot_conflict_warning PASSED        [ 90%]
tests/test_pawpal.py::test_invalid_inputs_raise_value_error PASSED       [100%]
============================= 10 passed in 0.10s ==============================
```

What the tests cover:

- **Core behavior:** marking tasks complete and adding tasks to a pet.
- **Sorting and filtering:** chronological ordering (including un-padded times like `7:30`), and filtering by pet name (case-insensitive) and completion status.
- **Recurrence:** Daily tasks recur 1 day later, Weekly tasks 7 days later, and `"One-time"` normalizes to `"Once"` and does not recur.
- **Conflicts:** two tasks at the same time produce a warning, and completed tasks are ignored.
- **Edge cases:** invalid time formats (`"8am"`, `"25:00"`, `"12:60"`, non-string `800`), blank descriptions, duplicate pet names (case-insensitive), and completing a task twice all raise `ValueError`.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | Sorts chronologically by due date, then start time. Times are normalized to zero-padded `HH:MM` and compared as minutes after midnight, so `7:30` sorts before `12:15`. |
| Filtering | `Scheduler.filter_tasks()` | Filters by any combination of pet name (case-insensitive), completion status, and date. Omitted criteria are ignored. |
| Conflict handling | `Scheduler.detect_conflicts()` | Checks only active (incomplete) tasks. Flags exact time-slot collisions and overlapping duration windows on the same day, returning a readable warning per conflicting pair instead of raising. |
| Recurring tasks | `Task.mark_complete()`, `Scheduler.complete_task()` | Completing a Daily or Weekly task uses `timedelta` to create the next occurrence 1 or 7 days later, and `Scheduler.complete_task()` adds it to the pet. Frequencies like `"One-time"` normalize to `"Once"`, which does not recur. Completing an already-completed task raises `ValueError` so no duplicate occurrence is created. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
