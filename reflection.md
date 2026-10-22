# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial UML design consists of four core classes: Owner, Pet, Task, and Scheduler. The Owner class manages owner details and holds a list of owned pets. The Pet class represents an individual pet and stores its specific attributes alongside a list of assigned care tasks. The Task class represents individual activities (e.g., feedings, walks) with properties for description, scheduled time, frequency, and completion status using Python dataclasses. Finally, the Scheduler class acts as the system's scheduling manager, retrieving tasks across all pets via the Owner object to aggregate, sort, and detect time conflicts.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes, during implementation, the Scheduler class was updated to interact directly with the Owner class instead of working with the individual Pet instances. This change was made to ensure the scheduler could aggregate all tasks across multiple pets into a single daily timeline and accurately check for scheduling conflicts between different pets owned by the same person. Additionally, helper properties were added to safely parse string timestamps ("HH:MM") into comparable tuples for precise sorting.


---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

My scheduler considers five constraints:

- **Time of day.** Each task has a start time in `HH:MM` format, and the final plan is always sorted earliest first.
- **Duration.** A task's start time plus its duration gives the time window it takes up. That window is used for conflict checks and counts against the owner's time.
- **Owner's available minutes.** `Owner.available_minutes` is a daily limit. `build_daily_plan()` skips any task that won't fit in the minutes left.
- **Priority.** Tasks are High, Medium, or Low. When there isn't time for everything, higher-priority tasks are picked first. Ties go to the earlier start time.
- **Date and recurrence.** Only open tasks due on the chosen day are considered. Daily and Weekly tasks create their next occurrence when completed.

I chose the order by asking what would hurt a pet most if it were skipped. Medication or a vet visit (High) matters more than playtime (Low), so priority decides what goes into the plan. Time decides the order, because an owner follows the plan from morning to evening, not from most to least important. The time limit comes from the scenario of a busy owner: a plan that asks for more time than the owner has isn't useful. Owner preferences, like preferring morning walks, were the least important, so I represented them only through the times and priorities the owner picks.


**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The main tradeoff is in conflict detection: exact timestamp matching versus duration overlap checking. Exact matching (flagging only tasks that start at the same `HH:MM`) is simple and easy to explain, but it misses real problems. For example, a 30-minute walk at 08:00 and a feeding at 08:10 never share a start time, yet the owner can't do both. Overlap checking compares each task's full window (start time plus duration), so it catches those cases. The cost is that it depends on accurate durations, and it compares every pair of tasks, which is O(n²). My scheduler does both: two tasks with the same start time always conflict, even with zero duration, and tasks with durations are also checked for overlapping windows.

The scheduler also checks only active (incomplete) tasks. A completed task is history, and the owner can't act on a warning about a walk that already happened. Skipping completed tasks keeps the warning list short and actionable. It also keeps the pairwise check fast, because finished tasks and earlier occurrences of recurring tasks pile up over time and would otherwise grow the list being compared. This is reasonable for a single owner's daily plan, where the number of open tasks is small and the goal is to catch double-booking before it happens.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI as a pair programmer for the Phase 4 scheduling logic:

- **Sorting lambdas:** AI helped me write the sort key `lambda t: (t.due_date, t.start_minutes)`, which sorts by date first and then by time converted to minutes after midnight. This avoids string-comparison bugs like `"9:00"` sorting after `"10:00"`. It also suggested `(PRIORITY_RANK[t.priority], t.start_minutes)` for picking tasks by priority in the daily plan.
- **Recurrence math:** AI helped me use `timedelta(days=interval)` with a `FREQUENCY_DAYS` lookup (Daily = 1, Weekly = 7, Once = no repeat), and `dataclasses.replace()` to copy a completed task into its next occurrence with a new due date and `completed=False`.
- **Input guardrails:** AI helped me identify invalid inputs to reject with `ValueError`: badly formatted or out-of-range times, non-string times, blank descriptions and pet names, negative ages and durations, duplicate pet names (case-insensitive), and completing the same task twice.

The most helpful prompts were specific and named the exact method and behavior I wanted (for example, "update `Scheduler.detect_conflicts` to return warning messages for active tasks that share a time slot") rather than general requests like "improve the scheduler."

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

I did not accept the first version of conflict detection as-is. It compared every task in the owner's list, including completed ones. That meant a walk finished this morning would still be flagged against a new task at the same time, and old recurring occurrences would keep producing warnings about history the owner can't change. I changed it so `detect_conflicts()` filters to tasks where `completed` is `False` before comparing. Now warnings only describe problems the owner can still fix.

To verify this and the rest of the Phase 4 logic, I relied on the automated test suite instead of just reading the code. `python -m pytest` now runs 42 tests, and all 42 pass. They cover chronological sorting, filtering by pet and status, Daily (+1 day) and Weekly (+7 days) recurrence, `"One-time"` normalization, same-time conflict warnings, completed tasks being excluded from conflicts, and the `ValueError` guardrails for invalid times, blank fields, duplicate pet names, and double completion. I ran the suite after each change before committing, so a regression in one feature couldn't slip in while I was working on another.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

The suite in `tests/test_pawpal.py` has **42 tests in eight sections**. Each feature has at least one normal-case test and several edge-case tests:

- **Sorting (`sort_by_time`)**: Tasks are sorted earliest to latest, including the case where `"9:00"` must come before `"10:00"` (comparing them as text gets this wrong). Sorting goes by date first, so tomorrow at 07:00 comes after today at 19:00. An empty list works, and the list passed in is not changed.
- **Recurrence (`mark_complete` / `complete_task`)**: Daily tasks come back 1 day later and Weekly tasks 7 days later. The new copy keeps the task's time, duration, priority, and pet. Dates roll over correctly at the end of a month and at Dec 31 → Jan 1. Once tasks don't come back, and the `"One-time"` spelling is treated as `"Once"`.
- **Conflict detection (`detect_conflicts`)**: Tasks with the same start time conflict, and so do tasks whose time windows partly overlap. Back-to-back tasks (08:00–08:30 then 08:30) don't conflict, and neither do tasks at the same time on different days. Completed tasks are ignored, and a three-way overlap gives one warning for each overlapping pair.
- **Daily plan (`build_daily_plan`)**: The plan stays within the owner's minutes, picks higher priorities first, and skips a lower-priority task whose time overlaps a task already in the plan.
- **Persistence (`save_to_json` / `load_from_json`)**: Saving and loading restores the owner, pets, tasks, completion status, and due dates exactly. A missing file raises `FileNotFoundError`, and a saved task with a bad time is rejected on load.
- **Input checks**: These all raise `ValueError`: bad times (`8am`, `25:00`, `12:60`, `800`, `None`), blank descriptions or pet names, negative ages, durations, or minutes, unknown priorities or frequencies, duplicate pet names (any case), adding the same task twice, completing a task twice, and completing a task through the wrong pet.

These tests matter because the bugs in a scheduler are usually at the edges. A test with a few tidy times would pass even if the code compared times as text, counted back-to-back tasks as conflicts, or created a duplicate occurrence when a task was completed twice. The edge-case tests are designed to catch those exact mistakes. The input-check tests also matter because every other feature assumes the data is valid. If `"8am"` got into a task, sorting would crash later and far from where the bad data came in.


**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

**Confidence Level: ⭐⭐⭐⭐⭐ 5/5** for the scheduling logic. All 42 tests pass with `python -m pytest` in about 0.2 seconds. Every public method of `Scheduler`, `Task`, `Pet`, and `Owner` has tests for normal and edge cases. Each requirement from the project brief (sorting, Daily/Weekly recurrence, conflict detection, input checks) has its own tests that fail if the behavior changes. I'm less sure about the Streamlit UI in `app.py`. I tested it by hand, not with automated tests.

Edge cases I would test next:

- **Tasks that go past midnight**, for example 23:45 for 30 minutes. Right now the window stops at the end of the day, so it wouldn't conflict with a task at 00:05 the next morning.
- **Completing an old occurrence of a recurring task** after its next occurrence already exists, to make sure the schedule doesn't fill up with copies.
- **Very large or zero `available_minutes`** and many tasks, to measure the cost of the pairwise conflict check.
- **Renaming a pet** after tasks are assigned, since tasks store `pet_name` as text and `complete_task()` uses it to find the pet.
- **UI tests** using Streamlit's `AppTest` to check that error messages appear when the user enters bad data.


---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied with how reliable the core logic is. Every value is checked and cleaned up when a `Task` or `Pet` is created: times become zero-padded `HH:MM`, and priorities and frequencies become one standard spelling. Because of that, the rest of the code never has to deal with messy input. Sorting, filtering, conflict detection, and planning all assume valid data and stay short. The test suite grew from 10 to 40 tests without any changes to the scheduling logic, which tells me the earlier design was solid. I'm also happy that conflicts produce readable warnings instead of crashing the app.


**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

- **Link tasks to pets by reference, not by name.** Tasks store `pet_name` as text, so renaming a pet would break `Scheduler.complete_task()`. A direct reference to the `Pet` or a stable ID would be safer.
- **Use real time types.** Storing `datetime.time` (or a full `datetime`) instead of an `"HH:MM"` string would remove the string parsing and let tasks run past midnight.
- **Explain the plan.** The UI now lists tasks that didn't fit, but `build_daily_plan()` doesn't say *why* each one was skipped. I would return the reason too (for example, "skipped Play: not enough time left"), so the owner understands the plan.
- **Faster conflict detection.** Since tasks are already sorted, a sweep-line pass could find overlaps in O(n log n) instead of comparing every pair.
- **Safer saving.** JSON save/load now works (`Owner.save_to_json()` / `load_from_json()`), but it rewrites the whole file on every change. Writing to a temporary file and then renaming it would keep a crash mid-save from corrupting `data.json`.


**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

I learned that with AI, I'm the one who decides what "correct" means, and tests are how I write that down. AI was fast at producing working code, like the sort-key lambdas, the `timedelta` recurrence, and the overlap check. But its first versions handled the normal case and missed the edge cases, such as completed tasks still being flagged as conflicts and the risk of completing a task twice. What worked was writing a design and test cases first, giving the AI specific prompts that named the method and the behavior I wanted, and accepting a change only after `python -m pytest` passed. On the design side, I learned that checking data once, when it enters the system, keeps the rest of the code much simpler.

---

## 6. AI Strategy (Phase 6)

> ✏️ Draft written with my AI assistant. Personalize anything that doesn't match what I actually did.

**a. Most effective AI coding assistant features**

- **Agent mode with the whole codebase in view.** The assistant read `pawpal_system.py` before writing UI code, so it called real methods (`filter_tasks(pet_name=..., completed=...)`, `build_daily_plan()`) instead of guessing names.
- **Running code, not just writing it.** It ran `python -m pytest` after every change, and it drove the Streamlit app headlessly with `streamlit.testing.v1.AppTest` to click buttons and submit forms. That's how bugs were caught before I opened the browser.
- **Multi-file edits in one pass.** Adding JSON persistence touched `pawpal_system.py`, `app.py`, the tests, the UML, and the README together, so the docs never drifted from the code.

**b. An AI suggestion I rejected or modified**

The ready-made `app.py` I was given for the UI polish step looked good but had real bugs, so I kept the design and changed the logic:

- Its "Done! 🎉" button key was `complete_{pet}_{description}_{time}`. After completing a Daily task, the next occurrence has the same pet, description, and time, so two buttons get the same key and Streamlit crashes. I kept the `id(task)` key from my earlier version.
- It called `st.success(...)` right before `st.rerun()`, so the message vanished instantly. I store it in `st.session_state` and show it on the next run instead.
- Filtering by pet called `filter_tasks()` on the unsorted list, which threw away the time order. I sort *after* filtering.
- It put pet names straight into HTML. I escape them with `html.escape()`.

This kept the system design clean: the UI only calls `Scheduler` methods and shows what they return, and no scheduling logic leaked into `app.py`.

**c. Using separate chat sessions for different phases**

I kept each phase (UML design, core classes, scheduling algorithms, testing, UI and docs) in its own session. Each session started with only the files and goals for that phase, so the assistant wasn't distracted by stale decisions from earlier phases. Committing at the end of each phase gave the next session a clean starting point, and I could see in `git log` exactly what changed in each phase.

**d. Being the "lead architect"**

The AI can generate a lot of plausible code very quickly, which makes my job deciding *what* to build and *whether it's right*. I owned the class boundaries (the Scheduler works through the Owner, and Tasks validate themselves), the definition of correct (written as 42 tests), and the final call on every suggestion. When pasted code and my design disagreed, the design and tests won. The most valuable habit was asking the AI to prove a change worked, by running the tests or the app, instead of trusting that it looked right.
