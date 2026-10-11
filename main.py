"""Temporary testing ground: build an owner, pets, and tasks, then print a schedule."""

from pawpal_system import (
    Cat,
    Dog,
    Owner,
    Priority,
    Scheduler,
    Task,
    format_time,
    parse_time,
)


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90)

    mochi = Dog(name="Mochi", age=3)
    luna = Cat(name="Luna", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added deliberately out of time order.
    luna.add_task(Task("Brush fur", "grooming", 15, Priority.MEDIUM, preferred_time=parse_time("09:00")))
    mochi.add_task(Task("Play session", "play", 45, Priority.LOW))
    mochi.add_task(Task("Feeding", "feeding", 10, Priority.HIGH, preferred_time=parse_time("08:30")))
    luna.add_task(Task("Feeding", "feeding", 10, Priority.HIGH, preferred_time=parse_time("08:10")))
    mochi.add_task(Task("Meds", "medication", 5, Priority.HIGH, frequency="daily"))
    mochi.add_task(Task("Morning walk", "walk", 30, Priority.HIGH, preferred_time=parse_time("08:00")))

    # Two more tasks at exactly 08:00, the same time as Mochi's walk:
    mochi.add_task(Task("Training", "training", 15, Priority.MEDIUM, preferred_time=parse_time("08:00")))  # same pet
    luna.add_task(Task("Litter box", "litter box", 10, Priority.MEDIUM, preferred_time=parse_time("08:00")))  # other pet

    scheduler = Scheduler(owner)

    def show(label, pairs) -> None:
        print(f"\n{label}")
        for pet, task in pairs:
            when = format_time(task.preferred_time) if task.preferred_time is not None else "--:--"
            status = "done" if task.is_completed else "todo"
            print(f"  {when}  {task.title:<14} {pet.name:<6} [{status}]")

    show("As added (out of order):", owner.get_all_tasks())
    show("Sorted by time:", scheduler.sort_by_time())

    meds = next(t for t in mochi.tasks if t.title == "Meds")
    following = scheduler.mark_task_complete(mochi, meds)
    print(f"\nCompleted '{meds.title}' (daily); next occurrence due {following.due_date}")

    bath = Task("Bath", "grooming", 20, frequency="weekly")
    mochi.add_task(bath)
    following = scheduler.mark_task_complete(mochi, bath)
    print(f"Completed '{bath.title}' (weekly); next occurrence due {following.due_date}")

    show("Mochi only:", scheduler.filter_tasks(pet_name="Mochi"))
    show("Completed:", scheduler.filter_tasks(completed=True))
    show("Luna, pending, by time:", scheduler.sort_by_time(scheduler.filter_tasks("Luna", completed=False)))

    print("\nConflicts:")
    for warning in scheduler.find_conflicts() or ["none"]:
        print(f"  ! {warning}")
    print()

    plan = Scheduler(owner).generate_plan()

    print("=" * 52)
    print(f" Today's Schedule - {owner.name}")
    print("=" * 52)
    print(plan.explain(owner.available_minutes))


if __name__ == "__main__":
    main()
