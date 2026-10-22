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

def test_one_time_frequency_alias():
    # "One-time" is accepted and stored as the canonical "Once"; it does not recur
    task = Task(description="Vet Visit", time="09:00", frequency="One-time")
    assert task.frequency == "Once"
    assert task.mark_complete() is None

def test_completing_daily_task_schedules_next_day():
    # Completing a recurring task via the Scheduler adds the next occurrence to the pet
    from datetime import date, timedelta
    owner = Owner(name="Alex")
    pet = Pet(name="Buddy", species="Dog")
    owner.add_pet(pet)
    task = Task(description="Morning Walk", time="08:00", frequency="Daily", due_date=date(2026, 1, 1))
    pet.add_task(task)
    next_task = Scheduler(owner).complete_task(task)
    assert task.completed is True
    assert next_task.due_date == date(2026, 1, 1) + timedelta(days=1)
    assert next_task.completed is False
    assert next_task in pet.tasks

def test_completed_tasks_do_not_conflict():
    # Only active (incomplete) tasks are checked for double-booking
    owner = Owner(name="Alex")
    pet = Pet(name="Buddy", species="Dog")
    owner.add_pet(pet)
    walk = Task(description="Walk", time="08:00", duration_minutes=30, frequency="Once")
    feed = Task(description="Feed", time="08:10", duration_minutes=5, frequency="Once")
    pet.add_task(walk)
    pet.add_task(feed)
    scheduler = Scheduler(owner)
    assert len(scheduler.detect_conflicts()) == 1
    walk.mark_complete()
    assert scheduler.detect_conflicts(owner.get_all_tasks()) == []
