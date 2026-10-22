import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# --- Step 2: Manage Application "Memory" (Session State) ---
if "owner" not in st.session_state:
    # Initialize default owner and some sample pets/tasks if empty
    default_owner = Owner(name="Alex")
    default_pet = Pet(name="Buddy", species="Dog", age=3)
    default_pet.add_task(Task(description="Morning Walk", time="08:00", frequency="Daily", pet_name="Buddy"))
    default_owner.add_pet(default_pet)
    st.session_state.owner = default_owner

owner = st.session_state.owner
scheduler = Scheduler(owner)

st.title("🐾 PawPal+ : Smart Pet Care Management")
st.sidebar.header("Navigation")
choice = st.sidebar.selectbox("Choose Action", ["View Schedule", "Add Pet", "Add Task"])

# --- Step 3: Wire UI Actions to Backend Methods ---

if choice == "View Schedule":
    st.header("📋 Today's Pet Schedule")
    
    # Retrieve all tasks sorted chronologically using your Scheduler class
    all_tasks = owner.get_all_tasks()
    sorted_tasks = scheduler.sort_by_time(all_tasks)
    
    # Check for scheduling conflicts
    conflicts = scheduler.detect_conflicts(sorted_tasks)
    if conflicts:
        for warning in conflicts:
            st.warning(f"⚠️ {warning}")

    if not sorted_tasks:
        st.info("No tasks scheduled yet! Use the sidebar to add pets and tasks.")
    else:
        for task in sorted_tasks:
            col1, col2 = st.columns([4, 1])
            with col1:
                status_icon = "✅" if task.completed else "⏳"
                st.write(f"{status_icon} **[{task.pet_name}]** {task.description} on {task.due_date:%b %d} at **{task.time}** (Freq: {task.frequency})")
            with col2:
                if not task.completed:
                    # id(task) keeps each button's key stable when new tasks shift the list
                    if st.button("Complete", key=f"complete_{id(task)}"):
                        # Completes via the pet so Daily/Weekly tasks get their next occurrence
                        next_task = scheduler.complete_task(task)
                        if next_task:
                            st.toast(f"Next '{next_task.description}' scheduled for {next_task.due_date:%b %d}")
                        st.rerun()

elif choice == "Add Pet":
    st.header("🐶 Add a New Pet")
    with st.form("pet_form"):
        pet_name = st.text_input("Pet Name")
        species = st.selectbox("Species", ["Dog", "Cat", "Bird", "Other"])
        age = st.number_input("Age (years)", min_value=0, max_value=30, value=1)
        submitted = st.form_submit_button("Add Pet")
        
        if submitted and pet_name:
            # Wire form directly to backend Pet class and Owner method
            try:
                new_pet = Pet(name=pet_name, species=species, age=int(age))
                owner.add_pet(new_pet)
                st.success(f"Successfully added {pet_name} the {species}!")
            except ValueError as error:
                st.error(f"Couldn't add pet: {error}")

elif choice == "Add Task":
    st.header("⏰ Schedule a Care Task")
    if not owner.pets:
        st.warning("Please add a pet first before scheduling tasks!")
    else:
        with st.form("task_form"):
            pet_names = [pet.name for pet in owner.pets]
            selected_pet_name = st.selectbox("Select Pet", pet_names)
            description = st.text_input("Task Description (e.g., Morning Walk, Feeding)")
            time_str = st.text_input("Time (HH:MM format, e.g., 08:00)", value="08:00")
            # Shows "One-time" to the user but passes the canonical "Once" to Task
            frequency = st.selectbox(
                "Frequency",
                ["Daily", "Weekly", "Once"],
                format_func=lambda f: "One-time" if f == "Once" else f,
            )
            
            submitted = st.form_submit_button("Add Task")
            
            if submitted and description:
                target_pet = owner.get_pet(selected_pet_name)
                if target_pet:
                    # Wire form to backend Task class and Pet method
                    try:
                        new_task = Task(
                            description=description,
                            time=time_str,
                            frequency=frequency,
                            pet_name=target_pet.name
                        )
                        target_pet.add_task(new_task)
                        st.success(f"Added task '{description}' for {target_pet.name} at {new_task.time}!")
                    except ValueError as error:
                        st.error(f"Couldn't add task: {error}")
