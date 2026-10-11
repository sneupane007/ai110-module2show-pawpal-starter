"""Temporary testing ground: build an owner, pets, and tasks, then print a schedule."""

from pawpal_system import Cat, Dog, Owner, Priority, Scheduler, Task


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90)

    mochi = Dog(name="Mochi", age=3)
    luna = Cat(name="Luna", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Morning walk", "walk", 30, Priority.HIGH, preferred_time=8 * 60))
    mochi.add_task(Task("Feeding", "feeding", 10, Priority.HIGH, preferred_time=8 * 60 + 30))
    mochi.add_task(Task("Play session", "play", 45, Priority.LOW))
    luna.add_task(Task("Feeding", "feeding", 10, Priority.HIGH, preferred_time=8 * 60 + 10))
    luna.add_task(Task("Brush fur", "grooming", 15, Priority.MEDIUM, preferred_time=9 * 60))

    plan = Scheduler(owner).generate_plan()

    print("=" * 52)
    print(f" Today's Schedule - {owner.name}")
    print("=" * 52)
    print(plan.explain(owner.available_minutes))


if __name__ == "__main__":
    main()
