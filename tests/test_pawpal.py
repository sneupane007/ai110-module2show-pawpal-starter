from datetime import date, timedelta

from pawpal_system import (
    Cat,
    Dog,
    Owner,
    Priority,
    Scheduler,
    Task,
    filter_tasks,
    find_conflicts,
    parse_time,
    sort_by_time,
)


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


def make_owner():
    owner = Owner(name="Jordan")
    mochi, luna = Dog(name="Mochi"), Cat(name="Luna")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    return owner, mochi, luna


def test_parse_time():
    assert parse_time("08:30") == 510


def test_sort_by_time_puts_unscheduled_last():
    owner, mochi, luna = make_owner()
    mochi.add_task(Task("Play", "play", 20))
    mochi.add_task(Task("Walk", "walk", 30, preferred_time=parse_time("09:00")))
    luna.add_task(Task("Feed", "feeding", 10, preferred_time=parse_time("07:00")))

    titles = [t.title for _, t in sort_by_time(owner.get_all_tasks())]

    assert titles == ["Feed", "Walk", "Play"]


def test_filter_by_pet_and_status():
    owner, mochi, luna = make_owner()
    done = Task("Walk", "walk", 30)
    done.mark_complete()
    mochi.add_task(done)
    mochi.add_task(Task("Play", "play", 20))
    luna.add_task(Task("Feed", "feeding", 10))

    assert [t.title for _, t in filter_tasks(owner, "Mochi")] == ["Walk", "Play"]
    assert [t.title for _, t in filter_tasks(owner, completed=False)] == ["Play", "Feed"]
    assert [t.title for _, t in filter_tasks(owner, "Luna", completed=True)] == []


def test_daily_task_recurs_tomorrow():
    pet = Dog(name="Mochi")
    task = Task("Meds", "medication", 5, frequency="daily", due_date=date(2020, 1, 1))
    pet.add_task(task)

    following = pet.complete_task(task)

    assert task.is_completed is True
    assert following.due_date == date.today() + timedelta(days=1)
    assert following.is_completed is False
    assert following in pet.tasks


def test_weekly_task_recurs_in_seven_days():
    owner, mochi, _ = make_owner()
    task = Task("Bath", "grooming", 20, frequency="weekly")
    mochi.add_task(task)

    following = Scheduler(owner).mark_task_complete(mochi, task)

    assert following.due_date == date.today() + timedelta(days=7)
    assert [t.is_completed for t in mochi.tasks] == [True, False]


def test_one_off_task_does_not_recur():
    pet = Dog(name="Mochi")
    task = Task("Bath", "grooming", 20)
    pet.add_task(task)

    assert pet.complete_task(task) is None
    assert len(pet.tasks) == 1


def test_find_conflicts_detects_overlap_across_pets():
    owner, mochi, luna = make_owner()
    mochi.add_task(Task("Walk", "walk", 30, preferred_time=parse_time("08:00")))
    luna.add_task(Task("Feed", "feeding", 10, preferred_time=parse_time("08:10")))

    warnings = find_conflicts(owner.get_all_tasks())

    assert len(warnings) == 1
    assert "different pets" in warnings[0]


def test_find_conflicts_ignores_back_to_back_and_completed():
    owner, mochi, _ = make_owner()
    mochi.add_task(Task("Walk", "walk", 30, preferred_time=parse_time("08:00")))
    mochi.add_task(Task("Feed", "feeding", 10, preferred_time=parse_time("08:30")))
    skipped = Task("Play", "play", 30, preferred_time=parse_time("08:15"))
    skipped.mark_complete()
    mochi.add_task(skipped)

    assert find_conflicts(owner.get_all_tasks()) == []


def test_scheduler_warns_on_same_time_same_pet_without_crashing():
    owner, mochi, _ = make_owner()
    mochi.add_task(Task("Walk", "walk", 30, preferred_time=parse_time("08:00")))
    mochi.add_task(Task("Training", "training", 15, preferred_time=parse_time("08:00")))

    warnings = Scheduler(owner).find_conflicts()

    assert len(warnings) == 1
    assert "same pet" in warnings[0]
    assert len(Scheduler(owner).generate_plan().scheduled) == 2


# --- Sorting edge cases ---

def test_sort_by_time_with_no_tasks_returns_empty():
    owner, _, _ = make_owner()  # two pets, zero tasks

    assert sort_by_time(owner.get_all_tasks()) == []


def test_sort_by_time_is_stable_for_equal_times():
    owner, mochi, luna = make_owner()
    mochi.add_task(Task("A", "play", 10, preferred_time=parse_time("08:00")))
    mochi.add_task(Task("B", "play", 10, preferred_time=parse_time("08:00")))
    luna.add_task(Task("C", "feeding", 10, preferred_time=parse_time("07:00")))

    titles = [t.title for _, t in sort_by_time(owner.get_all_tasks())]

    assert titles == ["C", "A", "B"]


def test_sort_by_time_treats_midnight_as_a_real_time():
    owner, mochi, _ = make_owner()
    mochi.add_task(Task("Untimed", "play", 10))
    mochi.add_task(Task("Midnight", "medication", 5, preferred_time=0))

    titles = [t.title for _, t in sort_by_time(owner.get_all_tasks())]

    assert titles == ["Midnight", "Untimed"]


def test_sort_by_time_does_not_modify_input():
    owner, mochi, _ = make_owner()
    mochi.add_task(Task("Late", "walk", 30, preferred_time=parse_time("18:00")))
    mochi.add_task(Task("Early", "feeding", 10, preferred_time=parse_time("07:00")))
    pairs = owner.get_all_tasks()

    sort_by_time(pairs)

    assert [t.title for _, t in pairs] == ["Late", "Early"]


# --- Recurrence edge cases ---

def test_recurring_copy_keeps_fields_but_is_a_new_pending_task():
    pet = Dog(name="Mochi")
    task = Task("Meds", "medication", 5, Priority.HIGH,
                preferred_time=parse_time("09:00"), frequency="daily")
    pet.add_task(task)

    following = pet.complete_task(task)

    assert following is not task
    assert (following.title, following.priority, following.preferred_time,
            following.frequency) == ("Meds", Priority.HIGH, 540, "daily")
    assert following.is_completed is False


# --- Conflict edge cases ---

def test_find_conflicts_flags_identical_time_on_different_pets():
    owner, mochi, luna = make_owner()
    mochi.add_task(Task("Walk", "walk", 30, preferred_time=parse_time("08:00")))
    luna.add_task(Task("Feed", "feeding", 30, preferred_time=parse_time("08:00")))

    warnings = find_conflicts(owner.get_all_tasks())

    assert len(warnings) == 1
    assert "different pets" in warnings[0]


def test_find_conflicts_three_tasks_at_same_time_gives_three_pairs():
    owner, mochi, _ = make_owner()
    for title, kind in [("A", "walk"), ("B", "play"), ("C", "training")]:
        mochi.add_task(Task(title, kind, 15, preferred_time=parse_time("08:00")))

    assert len(find_conflicts(owner.get_all_tasks())) == 3


def test_find_conflicts_ignores_untimed_tasks_and_empty_pets():
    owner, mochi, _ = make_owner()
    mochi.add_task(Task("Play", "play", 20))
    mochi.add_task(Task("Feed", "feeding", 10))

    assert Scheduler(owner).find_conflicts() == []


# --- Plan edge cases ---

def test_generate_plan_with_no_tasks_is_empty():
    owner, _, _ = make_owner()

    plan = Scheduler(owner).generate_plan()

    assert plan.scheduled == []
    assert plan.skipped == []
    assert plan.total_minutes == 0
    assert "Scheduled: 0 tasks" in plan.explain()


def test_same_time_tasks_are_both_scheduled_without_overlap():
    owner, mochi, _ = make_owner()
    mochi.add_task(Task("Walk", "walk", 30, preferred_time=parse_time("08:00")))
    mochi.add_task(Task("Training", "training", 30, preferred_time=parse_time("08:00")))

    plan = Scheduler(owner).generate_plan()

    assert [(s.start_time, s.end_time) for s in plan.scheduled] == [(480, 510), (510, 540)]


def test_task_over_time_budget_is_skipped_with_reason():
    owner, mochi, _ = make_owner()
    owner.available_minutes = 30
    mochi.add_task(Task("Walk", "walk", 30))
    mochi.add_task(Task("Play", "play", 20))

    plan = Scheduler(owner).generate_plan()

    assert [s.task.title for s in plan.scheduled] == ["Walk"]
    assert [k.task.title for k in plan.skipped] == ["Play"]
    assert "not enough time" in plan.skipped[0].reason
