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

To verify this and the rest of the Phase 4 logic, I relied on the automated test suite instead of just reading the code. `python -m pytest` runs 10 unit tests, and all 10 pass. They cover chronological sorting, filtering by pet and status, Daily (+1 day) and Weekly (+7 days) recurrence, `"One-time"` normalization, same-time conflict warnings, completed tasks being excluded from conflicts, and the `ValueError` guardrails for invalid times, blank fields, duplicate pet names, and double completion. I ran the suite after each change before committing, so a regression in one feature couldn't slip in while I was working on another.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
