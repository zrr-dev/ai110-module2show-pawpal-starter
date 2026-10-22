from pawpal_system import Owner, Pet, Task, Scheduler

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
