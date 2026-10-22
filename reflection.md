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

My scheduler primary considers time constraints (`HH:MM` timestamps) and completion status to order and filter tasks effectively. In addition, task attributes like priority (Low, Medium, High) and duration in minutes allow for organized daily routines. Time and status were prioritized as the most critical constraints because ensuring tasks are performed chronologically without duplicate time slots is fundamental to maintaining a functional pet care routine.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

One tradeoff the scheduler makes is using exact timestamp matching (`08:00`) rather than calculating full overlapping time windows (e.g., assessing a 30-minute walk starting at 08:00 vs a 10-minute feeding at 08:15). This exact-string matching tradeoff was chosen because it keeps the code lightweight and simple while still successfully alerting pet owners to double-booked time slots.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI tools throughout the project lifecycle to brainstorm class relationships, scaffold Python dataclasses for `Task` and `Pet`, generate unit test cases with `pytest`, and refine my Mermaid.js class diagram. Prompts that clearly specified the exact class structures, expected return types, and constraints (e.g., asking how `Scheduler` should aggregate tasks directly from the `Owner` class) yielded the most accurate and actionable code stubs.

## 3. AI Collaboration & Strategy
- **Effective AI Features:** The AI assistant was exceptionally helpful for quickly scaffolding object-oriented dataclasses and drafting unit test structures.
- **Human Oversight:** I reviewed all generated methods to ensure proper multi-pet aggregation via the Owner model rather than querying individual pets directly.
- **Verification:** Verified system behavior successfully using a CLI demo script (`main.py`) and automated `pytest` suites.

Initial Bug: Task frequency string mismatch between "One-time" and "Once", and finished tasks triggering false conflict warnings.

Refinement: Updated conflict detection to check only active tasks and added try/except guardrails in Streamlit to handle invalid inputs gracefully without breaking the user state.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

When implementing recurring task automation, the AI initially suggested a direct string manipulation approach for updating dates. I did not accept this as-is because it failed to account for month and year rollovers (such as December 31 rolling over to January 1). I evaluated and verified the suggestion by writing a targeted test case specifically for end-of-year and end-of-month dates, prompting the AI to revise its code to use Python's datetime and timedelta libraries to correctly handle date increments.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I tested core scheduling behaviors across 40 unit test cases, covering chronological task sorting, recurrence logic (daily and weekly rollovers), active conflict detection for overlapping time windows, priority-based daily planning constraints, and strict input guardrails (raising ValueError for blank descriptions, negative ages, invalid HH:MM time formats like '8am', and duplicate pet names). These tests were important to ensure robust error handling and prevent invalid data or double-booked schedules from breaking the application layer.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I am very confident (⭐⭐⭐⭐⭐ 5/5) in the backend scheduler's reliability based on the 40 passing pytest assertions and end-to-end CLI runs. If I had more time, the next edge cases I would test include tasks that cross midnight (e.g., starting at 23:45 and lasting 30 minutes) and handling time zone shifts or leap years during recurring task calculations.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I am very confident (⭐⭐⭐⭐⭐ 5/5) in the backend scheduler's reliability based on the 40 passing pytest assertions and end-to-end CLI runs. If I had more time, the next edge cases I would test include tasks that cross midnight (e.g., starting at 23:45 and lasting 30 minutes) and handling time zone shifts or leap years during recurring task calculations.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

If I had another iteration, I would implement a full JSON/CSV data persistence layer so pets and schedules are automatically saved to disk between application runs rather than relying entirely on st.session_state memory.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

My key takeaway is that treating the AI as an architectural co-pilot rather than an oracle is essential; human oversight is critical for catching subtle logic bugs—such as edge cases around double-completions or date rollovers—that automated scaffolding might initially miss.