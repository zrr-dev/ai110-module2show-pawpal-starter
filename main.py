from pawpal_system import Owner, Pet, Task, Scheduler

# 1. Create an Owner and Pets
owner = Owner(name="Alex")
dog = Pet(name="Buddy", species="Dog")
cat = Pet(name="Whiskers", species="Cat")

owner.add_pet(dog)
owner.add_pet(cat)

# 2. Add Tasks
dog.add_task(Task(description="Morning Walk", time="08:00", frequency="Daily", pet_name="Buddy"))
dog.add_task(Task(description="Evening Walk", time="18:00", frequency="Daily", pet_name="Buddy"))
cat.add_task(Task(description="Feed Breakfast", time="07:30", frequency="Daily", pet_name="Whiskers"))

# 3. Initialize Scheduler and Print Today's Schedule
scheduler = Scheduler(owner)
all_tasks = owner.get_all_tasks()

print("--- Today's Schedule ---")
for task in all_tasks:
    print(f"- [{task.pet_name}] {task.description} at {task.time} (Completed: {task.completed})")
