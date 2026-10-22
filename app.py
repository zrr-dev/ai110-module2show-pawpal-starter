import html
from datetime import date
from pathlib import Path

import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

# --- Page Configuration ---
st.set_page_config(
    page_title="PawPal+ 🐾 Smart Pet Care",
    page_icon="🐶",
    layout="centered",
    initial_sidebar_state="expanded",
)

SPECIES_EMOJI = {"Dog": "🐶", "Cat": "🐱", "Bird": "🦜", "Rabbit": "🐰"}
PRIORITY_BADGE = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}

# --- Custom CSS for Cute & Professional UI ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF6B6B;
        text-align: center;
        font-weight: 700;
        margin-bottom: 0rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4A5568;
        text-align: center;
        margin-bottom: 2rem;
    }
    .pet-card {
        background-color: #FFF5F5;
        color: #2D3748;
        border-radius: 12px;
        padding: 15px;
        border-left: 5px solid #FF6B6B;
        margin-bottom: 15px;
    }
    .stButton>button {
        border-radius: 20px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- Persistence: load saved data once per session, save after every change ---
DATA_FILE = Path(__file__).parent / "data.json"


def default_owner() -> Owner:
    """Sample owner shown on first launch, before anything has been saved."""
    owner = Owner(name="Alex", available_minutes=120)
    pet = Pet(name="Buddy", species="Dog", age=3)
    pet.add_task(Task(description="Morning Walk", time="08:00", frequency="Daily", priority="High", duration_minutes=30))
    owner.add_pet(pet)
    return owner


if "owner" not in st.session_state:
    try:
        st.session_state.owner = Owner.load_from_json(DATA_FILE)
    except FileNotFoundError:
        st.session_state.owner = default_owner()
    except (ValueError, KeyError, TypeError) as e:
        st.session_state.owner = default_owner()
        st.session_state.flash_error = f"⚠️ Couldn't read {DATA_FILE.name} ({e}); starting with sample data."

owner = st.session_state.owner
scheduler = Scheduler(owner)


def save() -> None:
    """Persist the owner, pets, and tasks so they survive an app restart."""
    owner.save_to_json(DATA_FILE)


def task_row(task: Task) -> dict:
    """Flatten a task into a row for st.table."""
    return {
        "Date": f"{task.due_date:%b %d}",
        "Time": task.time,
        "Pet": task.pet_name,
        "Task": task.description,
        "Minutes": task.duration_minutes,
        "Priority": f"{PRIORITY_BADGE[task.priority]} {task.priority}",
        "Frequency": task.frequency,
    }


# --- Sidebar Navigation & Cute Banner ---
st.sidebar.markdown("### 🐾 PawPal+ Menu")
choice = st.sidebar.radio("Navigate", ["📋 View Schedule", "🐶 Add Pet", "⏰ Schedule Task", "📊 Pet Dashboard"])

st.sidebar.markdown("---")
minutes = st.sidebar.number_input(
    f"⏱️ {owner.name}'s free minutes today", min_value=0, max_value=1440, value=owner.available_minutes, step=15
)
if minutes != owner.available_minutes:
    owner.available_minutes = minutes
    save()
st.sidebar.caption(f"💾 Changes are saved to `{DATA_FILE.name}` automatically.")
st.sidebar.info("💡 **Tip:** Keep your furry friends happy, healthy, and on schedule!")

# --- Main App Title & Header ---
st.markdown('<p class="main-header">PawPal+ 🐾</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Your intelligent, caring companion for multi-pet routines</p>', unsafe_allow_html=True)

# Messages set before st.rerun() would be lost, so show them on the next run instead.
if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))
if "flash_error" in st.session_state:
    st.error(st.session_state.pop("flash_error"))

# --- VIEW SCHEDULE ---
if choice == "📋 View Schedule":
    st.image(
        "https://images.unsplash.com/photo-1543466835-00a7907e9de1?auto=format&fit=crop&w=800&q=80",
        caption="Happy pets make happy homes! 🐶🐱🦜",
        width="stretch",
    )

    # Conflicts are shown up front, with a suggested fix, so the owner sees them before the timeline.
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.warning(
            f"⚠️ **{len(conflicts)} schedule conflict(s)** — you can't be in two places at once!\n\n"
            + "\n".join(f"- {warning}" for warning in conflicts)
            + "\n\n👉 Try moving one task to a different time or shortening its duration."
        )
    else:
        st.success("✅ No scheduling conflicts — every open task has its own time slot.")

    tab_timeline, tab_plan = st.tabs(["📅 Care Timeline", "🧠 Smart Daily Plan"])

    with tab_timeline:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            pet_filter = st.selectbox("Filter by Pet", ["All Pets"] + [p.name for p in owner.pets])
        with col_f2:
            status_filter = st.selectbox("Filter Status", ["All", "Pending ⏳", "Completed ✅"])
        with col_f3:
            sort_mode = st.selectbox("Sort by", ["🕒 Time", "🔴 Priority, then time"])

        completed = {"All": None, "Pending ⏳": False, "Completed ✅": True}[status_filter]
        filtered_tasks = scheduler.sort_by_time(
            scheduler.filter_tasks(
                pet_name=None if pet_filter == "All Pets" else pet_filter,
                completed=completed,
            ),
            by_priority=sort_mode != "🕒 Time",
        )

        if not filtered_tasks:
            st.info("✨ No tasks found matching your filter. Time to relax or add a new task!")
        else:
            for task in filtered_tasks:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    status_icon = "✅" if task.completed else "⏳"
                    st.markdown(
                        f"**{status_icon} [{task.pet_name}]** {task.description}  \n"
                        f"🕒 `{task.time}` ({task.duration_minutes}m) | "
                        f"{PRIORITY_BADGE[task.priority]} {task.priority} | Freq: *{task.frequency}*"
                    )
                with col2:
                    st.caption(f"Due: {task.due_date:%b %d}")
                with col3:
                    # id(task) is unique per task; description/time alone repeat across recurring occurrences.
                    if not task.completed and st.button("Done! 🎉", key=f"complete_{id(task)}"):
                        try:
                            next_task = scheduler.complete_task(task)
                            save()
                            if next_task:
                                st.session_state.flash = f"🎉 Completed '{task.description}'! Next one scheduled for {next_task.due_date:%b %d}."
                            else:
                                st.session_state.flash = f"🎉 Completed '{task.description}'!"
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))

    with tab_plan:
        plan = scheduler.build_daily_plan()
        todays_open = scheduler.filter_tasks(completed=False, on_date=date.today())
        used = sum(task.duration_minutes for task in plan)

        col_p1, col_p2 = st.columns(2)
        col_p1.metric("Planned Tasks 📋", f"{len(plan)} / {len(todays_open)}")
        col_p2.metric("Minutes Used ⏱️", f"{used} / {owner.available_minutes}")

        if not plan:
            st.info("✨ Nothing planned for today. Add a task or free up some minutes in the sidebar!")
        else:
            st.caption("Highest-priority tasks are picked first until your free minutes run out, then shown in time order.")
            st.table([task_row(task) for task in plan])

        skipped = [task for task in scheduler.sort_by_time(todays_open) if task not in plan]
        if skipped:
            st.warning(
                "🐾 **Didn't fit today** (not enough time, or overlaps a higher-priority task):\n\n"
                + "\n".join(f"- {task.time} [{task.pet_name}] {task.description}" for task in skipped)
            )

# --- ADD PET ---
elif choice == "🐶 Add Pet":
    st.markdown("### 🐶 Welcome a New Pet Family Member!")
    st.image(
        "https://images.unsplash.com/photo-1537151608828-ea2b11777ee8?auto=format&fit=crop&w=800&q=80",
        caption="Expand your happy crew!",
        width="stretch",
    )

    with st.form("pet_form"):
        pet_name = st.text_input("Pet Name 🐾")
        species = st.selectbox("Species", ["Dog 🐶", "Cat 🐱", "Bird 🦜", "Rabbit 🐰", "Other 🐾"])
        age = st.number_input("Age (years)", min_value=0, max_value=30, value=1)
        submitted = st.form_submit_button("Add Pet ✨")

        if submitted:
            clean_species = species.split()[0]  # Strip emoji for backend storage
            try:
                new_pet = Pet(name=pet_name, species=clean_species, age=int(age))
                owner.add_pet(new_pet)
                save()
                st.success(f"🎉 Successfully welcomed {new_pet.name} the {clean_species} to {owner.name}'s family!")
            except ValueError as e:
                st.error(f"❌ Couldn't add pet: {e}")

# --- SCHEDULE TASK ---
elif choice == "⏰ Schedule Task":
    st.markdown("### ⏰ Plan Care Routine & Tasks")
    if not owner.pets:
        st.warning("⚠️ Please add a pet from the menu before scheduling care tasks!")
    else:
        # Outside the form so the suggestion updates as soon as the length changes.
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            slot_length = st.number_input("🔎 Find a free slot (minutes)", min_value=1, max_value=240, value=30)
        with col_s2:
            slot_after = st.text_input("Starting from (HH:MM)", value="07:00")
        try:
            slot = scheduler.find_next_available_slot(int(slot_length), earliest=slot_after)
            if slot:
                st.info(f"💡 Next free {int(slot_length)}-minute slot today: **{slot}**")
            else:
                st.warning(f"🌙 No free {int(slot_length)}-minute slot left today after {slot_after}.")
        except ValueError as e:
            st.error(f"❌ {e}")

        with st.form("task_form"):
            selected_pet_name = st.selectbox("Select Pet 🐾", [pet.name for pet in owner.pets])
            description = st.text_input("Task Description (e.g., Morning Walk, Feeding, Medication)")

            col_t1, col_t2 = st.columns(2)
            with col_t1:
                time_str = st.text_input("Time (HH:MM format, e.g., 08:00)", value="08:00")
                duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=15)
            with col_t2:
                priority = st.selectbox("Priority Level", ["High", "Medium", "Low"])
                # Shows "One-time" to the user but passes the canonical "Once" to Task
                frequency = st.selectbox(
                    "Frequency",
                    ["Daily", "Weekly", "Once"],
                    format_func=lambda f: "One-time" if f == "Once" else f,
                )

            submitted = st.form_submit_button("Schedule Task 🚀")

            if submitted:
                target_pet = owner.get_pet(selected_pet_name)
                try:
                    new_task = Task(
                        description=description,
                        time=time_str,
                        frequency=frequency,
                        priority=priority,
                        duration_minutes=int(duration),
                        due_date=date.today(),
                    )
                    target_pet.add_task(new_task)
                    save()
                    st.success(f"🌟 Successfully scheduled '{new_task.description}' for {target_pet.name} at {new_task.time}!")
                    # Warn right away if the new task collides with something already booked.
                    for warning in scheduler.detect_conflicts():
                        if new_task.description in warning and new_task.time in warning:
                            st.warning(f"⚠️ Heads up: {warning}")
                except ValueError as e:
                    st.error(f"❌ Couldn't add task: {e}")

# --- PET DASHBOARD ---
elif choice == "📊 Pet Dashboard":
    st.markdown("### 📊 Family Overview & Metrics")

    all_tasks = owner.get_all_tasks()
    completed_tasks = len([t for t in all_tasks if t.completed])

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Registered Pets 🐾", len(owner.pets))
    col_m2.metric("Total Care Tasks 📋", len(all_tasks))
    col_m3.metric("Completed Tasks ✅", f"{completed_tasks} / {len(all_tasks)}")

    st.markdown("---")
    st.markdown("### 🏠 Your Pet Family")
    for pet in owner.pets:
        emoji = SPECIES_EMOJI.get(pet.species, "🐾")
        open_tasks = len([t for t in pet.tasks if not t.completed])
        st.markdown(f"""
        <div class="pet-card">
            <h4>{emoji} {html.escape(pet.name)} ({html.escape(pet.species)})</h4>
            <p><b>Age:</b> {pet.age} years old &nbsp;|&nbsp; <b>Open Tasks:</b> {open_tasks} &nbsp;|&nbsp; <b>All Tasks:</b> {len(pet.tasks)}</p>
        </div>
        """, unsafe_allow_html=True)
