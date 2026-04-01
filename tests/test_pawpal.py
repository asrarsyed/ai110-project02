from pawpal_system import Pet, Task


def test_task_mark_complete_sets_is_complete_true() -> None:
    task = Task(name="Feed", duration_minutes=15, priority=3)

    task.mark_complete()

    assert task.is_complete is True


def test_adding_task_to_pet_increases_task_count() -> None:
    pet = Pet(name="Mochi", species="cat")
    task = Task(name="Play", duration_minutes=20, priority=2)

    before = len(pet.get_tasks())
    pet.add_task(task)
    after = len(pet.get_tasks())

    assert after == before + 1
