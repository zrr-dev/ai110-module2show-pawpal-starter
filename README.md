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

### Run it

```bash
python main.py            # CLI demo of every Scheduler feature (output below)
streamlit run app.py      # Streamlit UI (walkthrough below)
python -m pytest          # 46 automated tests
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🏗️ System Design

All logic lives in `pawpal_system.py`; `app.py` (Streamlit) and `main.py` (CLI) only call into it. The final UML is in [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd).

| Class | Responsibility | Key members |
|-------|----------------|-------------|
| `Task` | One care activity (walk, feeding, meds) at a time of day. Validates and normalizes its own fields. | `description`, `time`, `duration_minutes`, `priority`, `frequency`, `due_date`, `completed`, `pet_name`; `mark_complete()`, `overlaps()` |
| `Pet` | A pet and the tasks that belong to it. | `name`, `species`, `age`, `tasks`; `add_task()`, `get_tasks()`, `remove_task()`, `complete_task()` |
| `Owner` | The person caring for one or more pets, with a daily time budget. | `name`, `available_minutes`, `pets`; `add_pet()`, `get_pet()`, `get_all_tasks()`, `save_to_json()`, `load_from_json()` |
| `Scheduler` | The "brain": works across **all** of an owner's pets to sort, filter, detect conflicts, complete recurring tasks, and build a daily plan. | `sort_by_time()`, `filter_tasks()`, `detect_conflicts()`, `find_next_available_slot()`, `complete_task()`, `build_daily_plan()` |

An `Owner` has many `Pet`s, each `Pet` has many `Task`s, and the `Scheduler` reaches every task through `Owner.get_all_tasks()`, so conflicts between different pets are caught too.

## ✨ Features

- **Multi-pet owner profile** — one owner manages any number of pets (dogs, cats, birds, rabbits, ...), each with its own task list.
- **Sorting by time** — `Scheduler.sort_by_time()` orders tasks by due date, then start time in minutes after midnight, so `9:00` correctly comes before `10:00`.
- **Priority sorting** — `Scheduler.sort_by_time(by_priority=True)` groups tasks High → Medium → Low, then orders each group chronologically.
- **Next available slot** — `Scheduler.find_next_available_slot()` scans the day's open tasks and returns the earliest `HH:MM` where a task of a given length fits without overlapping anything.
- **Filtering** — `Scheduler.filter_tasks()` narrows tasks by pet, completion status, and/or date.
- **Conflict warnings** — `Scheduler.detect_conflicts()` compares every pair of open tasks on the same day and warns when start times match or duration windows overlap (back-to-back tasks are allowed).
- **Daily recurrence** — completing a Daily or Weekly task through `Scheduler.complete_task()` automatically queues the next occurrence 1 or 7 days later using `timedelta`; One-time tasks don't repeat.
- **Priority-based daily plan** — `Scheduler.build_daily_plan()` picks High → Medium → Low tasks until the owner's free minutes run out, skips anything that overlaps a higher-priority choice, then shows the plan in time order.
- **JSON persistence** — `Owner.save_to_json()` / `Owner.load_from_json()` save and restore the owner, pets, and tasks so nothing is lost when the app restarts.
- **Input guardrails** — invalid times (`8am`, `25:00`), blank names, negative ages/durations, duplicate pets, and double-completing a task all raise `ValueError`, which the UI shows as a friendly error instead of crashing.

## 🖥️ Sample Output

Running `python main.py` creates an owner with two pets and four tasks (added out of order, with one overlap), then shows each Scheduler behavior:

```
--- Today's Schedule (sorted by time) ---
| Date   | Time   | Pet      | Task           |   Min | Priority   | Frequency   | Status   |
|--------|--------|----------|----------------|-------|------------|-------------|----------|
| Oct 22 | 07:30  | Whiskers | Feed Breakfast |    10 | High       | Daily       | open     |
| Oct 22 | 08:00  | Buddy    | Morning Walk   |    30 | High       | Daily       | open     |
| Oct 22 | 08:15  | Whiskers | Brush Fur      |    20 | Low        | Weekly      | open     |
| Oct 22 | 18:00  | Buddy    | Evening Walk   |    30 | Medium     | Daily       | open     |

--- Sorted by priority, then time ---
| Date   | Time   | Pet      | Task           |   Min | Priority   | Frequency   | Status   |
|--------|--------|----------|----------------|-------|------------|-------------|----------|
| Oct 22 | 07:30  | Whiskers | Feed Breakfast |    10 | High       | Daily       | open     |
| Oct 22 | 08:00  | Buddy    | Morning Walk   |    30 | High       | Daily       | open     |
| Oct 22 | 18:00  | Buddy    | Evening Walk   |    30 | Medium     | Daily       | open     |
| Oct 22 | 08:15  | Whiskers | Brush Fur      |    20 | Low        | Weekly      | open     |

--- Whiskers' tasks only ---
| Date   | Time   | Pet      | Task           |   Min | Priority   | Frequency   | Status   |
|--------|--------|----------|----------------|-------|------------|-------------|----------|
| Oct 22 | 07:30  | Whiskers | Feed Breakfast |    10 | High       | Daily       | open     |
| Oct 22 | 08:15  | Whiskers | Brush Fur      |    20 | Low        | Weekly      | open     |

--- Conflict Warnings ---
WARNING: Conflict on 2026-10-22: Buddy's 'Morning Walk' at 08:00 (30 min) overlaps Whiskers's 'Brush Fur' at 08:15 (20 min)

--- Daily Plan (60 min available) ---
| Date   | Time   | Pet      | Task           |   Min | Priority   | Frequency   | Status   |
|--------|--------|----------|----------------|-------|------------|-------------|----------|
| Oct 22 | 07:30  | Whiskers | Feed Breakfast |    10 | High       | Daily       | open     |
| Oct 22 | 08:00  | Buddy    | Morning Walk   |    30 | High       | Daily       | open     |

Next free 30-minute slot after 07:30: 08:35

Completed 'Morning Walk'; next occurrence due Oct 23.

--- Buddy's tasks after completing Morning Walk ---
| Date   | Time   | Pet   | Task         |   Min | Priority   | Frequency   | Status   |
|--------|--------|-------|--------------|-------|------------|-------------|----------|
| Oct 22 | 08:00  | Buddy | Morning Walk |    30 | High       | Daily       | done     |
| Oct 22 | 18:00  | Buddy | Evening Walk |    30 | Medium     | Daily       | open     |
| Oct 23 | 08:00  | Buddy | Morning Walk |    30 | High       | Daily       | open     |
```

## 🧪 Testing PawPal+

The automated suite lives in `tests/test_pawpal.py` and tests the core logic in `pawpal_system.py` directly, without the Streamlit UI. From the project root, with the virtual environment activated, run:

```bash
python -m pytest
```

Add `-v` to see each test by name. A successful run looks like this:

```
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Zia Files\CodePath\ai110-module2show-pawpal-starter
plugins: anyio-4.15.1
collected 46 items

tests\test_pawpal.py ..............................................      [100%]

============================= 46 passed in 0.15s ==============================
```

All **46 tests pass**. They're grouped into sections, and each one tests either a normal case or an edge case:

| Area | Method(s) under test | Normal cases | Edge cases |
|------|---------------------|--------------|------------|
| Core behavior | `Task`, `Pet.add_task`, `Owner.get_all_tasks` | Marking a task complete, adding a task to a pet, collecting tasks across pets | The task is tagged with its pet's name |
| Sorting | `Scheduler.sort_by_time` | Sorts tasks earliest to latest; `by_priority=True` sorts High → Medium → Low, then by time | Unpadded times (`9:00` sorts before `10:00`), sorting by date before time, an empty list, the input list is not changed |
| Filtering | `Scheduler.filter_tasks` | Filters by pet, completion status, or date | Pet names match regardless of case, an unknown pet returns an empty list |
| Recurrence | `Task.mark_complete`, `Scheduler.complete_task` | A Daily task comes back 1 day later and a Weekly task 7 days later (using `timedelta`) | The next occurrence keeps the task's details, dates roll over month and year ends, `"One-time"`/`"Once"` tasks don't repeat |
| Conflicts | `Scheduler.detect_conflicts` | Two tasks at the same start time, partly overlapping time windows | Back-to-back tasks are allowed, the same time on different days is allowed, completed tasks are ignored, a three-way overlap gives one warning per pair |
| Daily plan | `Scheduler.build_daily_plan` | Picks tasks by priority within the owner's available minutes | Skips a lower-priority task whose time overlaps a chosen higher-priority task |
| Free slots | `Scheduler.find_next_available_slot` | Returns the first gap long enough for the new task | A gap that fits exactly (back-to-back) is used, other days and completed tasks are ignored, a full day returns `None`, a zero-minute task still blocks its start minute, a zero duration raises `ValueError` |
| Persistence | `Owner.save_to_json`, `Owner.load_from_json` | Save then load restores the owner, pets, tasks, completion status, and due dates exactly | A missing file raises `FileNotFoundError`; a saved task with a bad time (`8am`) raises `ValueError` on load |
| Input checks | Constructors and `mark_complete` | — | Each of these raises `ValueError`: bad times (`8am`, `25:00`, `12:60`, `8`, `""`, `800`, `None`), blank descriptions or pet names, negative ages, durations, or available minutes, unknown priority or frequency, duplicate pet names (any case), adding the same task twice, completing a task twice, completing a task through the wrong pet |

**Confidence Level: ⭐⭐⭐⭐⭐ 5/5.** Every public scheduling method has tests for both normal and edge cases, and all 46 pass. Every input check is tested to raise `ValueError`, so bad data is rejected at creation and can't break sorting or recurrence later. Conflicts are reported as warnings, not errors, so the app keeps running when it finds one. One gap remains: the tests cover the logic layer, not the Streamlit UI in `app.py`, which I checked by hand.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | Sorts chronologically by due date, then start time. Times are normalized to zero-padded `HH:MM` and compared as minutes after midnight, so `7:30` sorts before `12:15`. |
| Priority sorting *(Challenge 3)* | `Scheduler.sort_by_time(by_priority=True)` | Multi-level sort key `(priority rank, due date, start minutes)`: all High tasks first, then Medium, then Low, each group in time order. The default (`by_priority=False`) stays purely chronological, because the timeline, conflict check, and daily plan output depend on time order. The **Care Timeline** has a **Sort by** dropdown to switch. |
| Filtering | `Scheduler.filter_tasks()` | Filters by any combination of pet name (case-insensitive), completion status, and date. Omitted criteria are ignored. |
| Conflict handling | `Scheduler.detect_conflicts()` | Checks only active (incomplete) tasks. Flags exact time-slot collisions and overlapping duration windows on the same day, returning a readable warning per conflicting pair instead of raising. |
| Recurring tasks | `Task.mark_complete()`, `Scheduler.complete_task()` | Completing a Daily or Weekly task uses `timedelta` to create the next occurrence 1 or 7 days later, and `Scheduler.complete_task()` adds it to the pet. Frequencies like `"One-time"` normalize to `"Once"`, which does not recur. Completing an already-completed task raises `ValueError` so no duplicate occurrence is created. |
| Priority-based daily plan *(advanced)* | `Scheduler.build_daily_plan()` | Sorts the day's open tasks by priority (High → Medium → Low, ties by start time), adds each one only if it fits in the owner's remaining `available_minutes` and doesn't overlap a task already chosen (time-blocking), then returns the plan in time order. In the **🖥️ Sample Output** above, the 60-minute plan keeps both High tasks, drops Brush Fur because it overlaps the higher-priority Morning Walk, and drops Evening Walk because only 20 minutes are left. |
| Next available slot *(Challenge 1)* | `Scheduler.find_next_available_slot()` | Walks the day's open tasks in start order with one candidate time (starting at `earliest`, default `00:00`). Each task that would overlap the candidate window pushes the candidate to that task's end; the first task that starts after the window ends means the gap is free. Runs in O(n log n) for the sort plus one pass. Returns `None` if the task wouldn't finish before midnight. In the sample output, a 30-minute task after 07:30 lands at **08:35**: Feed Breakfast, Morning Walk, and Brush Fur fill 07:30–08:35 back to back or overlapping. |

## 💾 Data Persistence

The Streamlit app saves everything to `data.json` in the project folder, so pets and tasks survive closing and reopening the app.

- **Load:** on the first run of each session, `app.py` calls `Owner.load_from_json("data.json")`. If the file doesn't exist yet, the app starts with the sample owner. If it's corrupted or has invalid data, the app shows an error and falls back to the sample data instead of crashing.
- **Save:** after every change (adding a pet, adding a task, completing a task, changing free minutes), `app.py` calls `owner.save_to_json("data.json")`.
- **Format:** `Task.to_dict()`, `Pet.to_dict()`, and `Owner.to_dict()` turn each object into plain JSON (dates as ISO strings like `"2026-10-22"`). The matching `from_dict()` methods rebuild the objects through their normal constructors and `add_pet()` / `add_task()`, so loaded data passes the same validation as data typed into the UI.
- **Files modified:** `pawpal_system.py` (the `to_dict` / `from_dict` / save / load methods), `app.py` (load at startup, `save()` after each change), `tests/test_pawpal.py` (section 8, two tests), and `.gitignore` (`data.json` is personal data, so it isn't committed). Delete `data.json` to reset the app.

## 🎨 UI and Output Formatting

- **Custom CSS** (`st.markdown(..., unsafe_allow_html=True)` in `app.py`): a coral title, soft pink pet cards with an accent border, and rounded buttons.
- **Emoji indicators:** 🔴 / 🟡 / 🟢 priority badges (`PRIORITY_BADGE`), ✅ / ⏳ task status, and species icons 🐶 🐱 🦜 🐰 on pet cards (`SPECIES_EMOJI`).
- **Streamlit layout components:** `st.tabs` (Care Timeline / Smart Daily Plan), `st.columns` for filters and task rows, `st.metric` for dashboard and plan counts, and `st.table` for the daily plan, built by the `task_row()` helper.
- **Status messages:** `st.warning` for conflicts and tasks that didn't fit, `st.success` for confirmations, `st.error` for rejected input, and `st.info` for empty states.
- **CLI tables** (`main.py`): the `print_tasks()` helper uses the [`tabulate`](https://pypi.org/project/tabulate/) library (`tablefmt="github"`) to print each section as an aligned table with date, time, pet, task, minutes, priority, frequency, and status. The output is plain ASCII, so it works in any Windows console or when redirected to a file, and it can be pasted into Markdown as-is (that's how the **🖥️ Sample Output** above was made).

## 📸 Demo Walkthrough

Run the app with `streamlit run app.py`. The sidebar has four pages plus a **free minutes today** setting that the daily plan uses. On first launch the app starts with a sample owner (Alex) and dog (Buddy) with a daily Morning Walk at 08:00.

**Main UI features**

| Page | What you can do |
|------|-----------------|
| 📋 View Schedule | See a conflict banner (or a green "no conflicts" message), then two tabs. **Care Timeline** lists every task sorted by date and time (or by priority, then time), filterable by pet and status, with a **Done! 🎉** button per open task. **Smart Daily Plan** shows the priority-based plan in a table, metrics for tasks planned and minutes used, and a list of tasks that didn't fit. |
| 🐶 Add Pet | Add a pet with name, species, and age. Blank or duplicate names show an error. |
| ⏰ Schedule Task | A **🔎 Find a free slot** helper at the top suggests the next free time today for a task of the length you enter (it updates as you type). Then add a task with description, time (`HH:MM`), duration, priority, and frequency (Daily, Weekly, One-time). Invalid times show an error, and a new task that overlaps an existing one shows a warning right away. |
| 📊 Pet Dashboard | Metrics for pets, total tasks, and completed tasks, plus a card for each pet showing its open and total tasks. |

**Example workflow**

1. Open **🐶 Add Pet**, enter `Whiskers`, choose **Cat 🐱**, age `5`, and click **Add Pet ✨**. A success message confirms it.
2. Open **⏰ Schedule Task**, pick Whiskers, enter `Brush Fur` at `08:15` for 20 minutes, Low priority, Weekly. It's saved, and a **Heads up** warning appears because it overlaps Buddy's 08:00–08:30 Morning Walk.
3. Add `Feed Breakfast` for Whiskers at `7:30` (10 min, High, Daily). The time is normalized to `07:30`. Try `8am` instead and you get *"Couldn't add task: Time must look like HH:MM"*.
4. Open **📋 View Schedule**. The yellow banner lists the Morning Walk / Brush Fur conflict and suggests moving or shortening one task. The **Care Timeline** shows Feed Breakfast (07:30), Morning Walk (08:00), Brush Fur (08:15) in order. Filter by **Whiskers** to see only the cat's tasks.
5. Open the **Smart Daily Plan** tab. Both High tasks are planned; Brush Fur is listed under **Didn't fit today** because it overlaps the higher-priority walk. Lower the free minutes in the sidebar to watch lower-priority tasks drop out.
6. Back on **Care Timeline**, click **Done! 🎉** on Morning Walk. A message says the next one is scheduled for tomorrow, the walk shows ✅, a new open Morning Walk appears for the next day, and the conflict banner clears because completed tasks are no longer checked.
7. Open **📊 Pet Dashboard** to see the updated counts and a card for each pet.
8. Stop the app (`Ctrl+C`) and run `streamlit run app.py` again. Whiskers and all the tasks are still there, loaded from `data.json`.

**Key Scheduler behaviors shown**

- **Sorting:** the timeline and plan always use `sort_by_time()`, regardless of the order tasks were added; the **Sort by** dropdown switches the timeline to `by_priority=True`.
- **Next free slot:** the helper on the Schedule Task page calls `find_next_available_slot()`.
- **Filtering:** the pet and status dropdowns call `filter_tasks()`.
- **Conflict warnings:** `detect_conflicts()` drives the banner on the schedule page and the instant warning on the task form.
- **Recurrence:** **Done! 🎉** calls `complete_task()`, which queues the next Daily/Weekly occurrence.
- **Daily plan:** the Smart Daily Plan tab calls `build_daily_plan()` with the owner's free minutes.
- **Guardrails:** every `ValueError` from the backend is shown with `st.error` instead of crashing the app.

The CLI output from `python main.py` is shown in **🖥️ Sample Output** above.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
