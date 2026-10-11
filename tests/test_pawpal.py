from pawpal_system import Dog, Priority, Task


def make_task() -> Task:
    return Task("Morning walk", "walk", 30, Priority.HIGH)


def test_mark_complete_changes_status():
    task = make_task()
    assert task.is_completed is False

    task.mark_complete()

    assert task.is_completed is True


def test_add_task_increases_pet_task_count():
    pet = Dog(name="Mochi")
    assert len(pet.tasks) == 0

    pet.add_task(make_task())

    assert len(pet.tasks) == 1
