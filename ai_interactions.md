# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

Using Claude Code in agent mode (VS Code), I asked it to complete Phase 6: give `app.py` a polished, pet-friendly UI built on my `Scheduler` methods, finalize `diagrams/uml_final.mmd`, polish the README (features, demo walkthrough, CLI output), and draft my reflection. Then I asked it to audit the whole project against the grading rubric and fill any gaps, which led to the **JSON persistence** stretch feature. The third algorithmic capability, `Scheduler.build_daily_plan()` (priority-weighted selection within a time budget, with time-blocking so chosen tasks never overlap), was already built and is now surfaced in both the UI and `main.py`.

**What did the agent do?**

1. Read `pawpal_system.py` and the existing `app.py` first, to check that the UI code it was given matched my real class APIs.
2. **`app.py`:** rewrote the UI with custom CSS, sidebar navigation, `st.tabs`, `st.metric`, and `st.table`. It added a conflict banner with a suggested fix, a "Smart Daily Plan" tab using `build_daily_plan()`, an instant conflict warning when a new task is scheduled, and load/save to `data.json`.
3. **`main.py`:** rewrote the CLI demo to show sorting, filtering, conflict warnings, the daily plan, and recurrence (the old version printed tasks without using the Scheduler).
4. **`pawpal_system.py`:** added `to_dict()` / `from_dict()` on `Task`, `Pet`, and `Owner`, plus `Owner.save_to_json()` and `Owner.load_from_json()`.
5. **`tests/test_pawpal.py`:** added section 8 (persistence) with a save/load round-trip test and a missing/invalid-file test (40 → 42 tests).
6. **`diagrams/uml_final.mmd`:** created it from my Phase 1 UML, with the new persistence methods.
7. **`README.md`, `reflection.md`, `.gitignore`:** added the system design, run instructions, features, sample CLI output, persistence and formatting sections, and the demo walkthrough. Updated test counts and reflection answers. Ignored `data.json`.
8. **Verified:** ran `python -m pytest` after each change (42 passed). It also drove every page of the app headlessly with `streamlit.testing.v1.AppTest`: adding pets and tasks, bad input, conflict warnings, completing the same recurring task repeatedly, restarting with saved data, and loading a corrupted `data.json`.

**What did you have to verify or fix manually?**

- The ready-made `app.py` I was given had bugs that the agent caught and fixed instead of pasting it as-is: duplicate button keys after a recurring task's next occurrence was created (a Streamlit crash), success messages lost to `st.rerun()`, a pet filter that dropped the time sort, and unescaped pet names in HTML.
- Its first README rewrite dropped the `platform ...` line from the pytest output block; the agent noticed and restored it.
- It couldn't run the Mermaid CLI on my machine, so I should paste `diagrams/uml_final.mmd` into the [Mermaid Live Editor](https://mermaid.live) to confirm it renders.
- <!-- TODO: add anything you checked or changed by hand after running `streamlit run app.py` yourself -->

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

**Task:** calculating the next occurrence of a Weekly (and Daily) task with `timedelta`, correctly across month and year boundaries.

**Prompt (identical for both models):**

> In Python, I have a `Task` dataclass with `due_date: date`, `completed: bool`, and `frequency` that is `"Daily"`, `"Weekly"`, or `"Once"`. Write a `mark_complete()` method that marks the task done and returns a new `Task` for the next occurrence (or `None` for `"Once"`). It must work across month and year boundaries, e.g. a Weekly task due Jan 28 → Feb 4, and Dec 29 → Jan 5 of the next year. Include a pytest test for the boundary cases.

<!-- TODO: paste the prompt above into the second model (ChatGPT / Gemini) and fill in the Option A column from its actual answer. Don't guess what it would have said. -->

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | <!-- TODO: e.g. ChatGPT (GPT-4o) or Gemini --> | Claude (Claude Code agent in VS Code) |
| **Prompt** | Same prompt as above | Same prompt as above |
| **Response summary** | <!-- TODO: summarize its approach: timedelta? manual day math? relativedelta? --> | Mapped each frequency to a day interval (`FREQUENCY_DAYS = {"Once": None, "Daily": 1, "Weekly": 7}`), then built the next task with `dataclasses.replace(self, due_date=self.due_date + timedelta(days=interval), completed=False)`. Added a test covering Dec 31, 2026 → Jan 1, 2027 (Daily, year rollover) and Feb 25 → Mar 4 (Weekly, across the short month of February). |
| **What was useful** | <!-- TODO --> | `date + timedelta` handles month lengths, leap years, and year rollover itself, so there's no calendar math to get wrong. `replace()` copies every other field (description, time, priority, pet) automatically, so new fields added later carry over without editing this method. The lookup table makes adding a "Monthly"-style interval a one-line change. |
| **Problems noticed** | <!-- TODO: e.g. did it do `date(y, m, d + 7)` (crashes at month end), add a dependency like `dateutil`, or mutate the original task? --> | Its first version didn't guard against completing the same task twice, which would queue a duplicate next occurrence. I had it raise `ValueError` if the task is already completed (commit `a2faae1`). It also only *returns* the next task, so something still has to add it to the pet; that's why the app completes tasks through `Scheduler.complete_task()`, which calls `Pet.complete_task()`. |
| **Decision** | <!-- TODO --> | Used in the final code: `Task.mark_complete()` in `pawpal_system.py`, tested by `test_recurrence_crosses_month_and_year_boundaries` and `test_double_completion_raises_value_error`. |

**Which approach did you use in your final implementation and why?**

<!-- TODO: finish once Option A is filled in. A starting point: -->
I kept the `timedelta` + `dataclasses.replace()` version because it lets the standard library handle every calendar edge case and keeps the method short. <!-- TODO: one sentence on what Option A did better or worse, and whether you borrowed anything from it. -->
