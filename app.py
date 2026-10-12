import datetime

import streamlit as st

from pawpal_system import Cat, Dog, OtherPet, Owner, Priority, Scheduler, Task, format_time

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
PawPal+ plans your pets' care tasks for the day based on the time you have and each task's priority.
Add your pets, add tasks, then generate a schedule.
"""
)

# st.session_state persists across reruns. Streamlit re-executes this whole script on every
# interaction, so only create the Owner if one is not already stored.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
owner = st.session_state.owner
scheduler = Scheduler(owner)


def task_rows(pairs):
    """Turn (pet, task) pairs into rows for st.table."""
    return [
        {
            "Time": format_time(t.preferred_time) if t.preferred_time is not None else "-",
            "Pet": p.name,
            "Task": t.title,
            "Type": t.task_type,
            "Minutes": t.duration_minutes,
            "Priority": t.priority.name,
            "Repeats": t.frequency,
            "Due": t.due_date.isoformat() if t.due_date else "today",
            "Status": "done" if t.is_completed else "todo",
        }
        for p, t in pairs
    ]


def show_conflicts(note):
    """Show one warning per overlapping pair, or a success message when there are none."""
    conflicts = scheduler.find_conflicts()
    if not conflicts:
        st.success("No time conflicts between your tasks.")
        return
    st.warning(f"{len(conflicts)} time conflict(s) found. {note}")
    for message in conflicts:
        st.warning(message, icon="⚠️")


tab_setup, tab_tasks, tab_schedule = st.tabs(["1. Setup", "2. Tasks", "3. Schedule"])

with tab_setup:
    st.subheader("Owner")
    col1, col2 = st.columns(2)
    with col1:
        owner.name = st.text_input("Owner name", value=owner.name)
    with col2:
        owner.available_minutes = int(
            st.number_input(
                "Time available today (minutes)",
                min_value=10,
                max_value=720,
                value=owner.available_minutes,
            )
        )

    st.subheader("Pets")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        st.write("")
        st.write("")
        add_pet_clicked = st.button("Add pet")

    if add_pet_clicked:
        if not pet_name.strip():
            st.error("Pet name cannot be empty.")
        else:
            pet_class = {"dog": Dog, "cat": Cat, "other": OtherPet}[species]
            owner.add_pet(pet_class(name=pet_name.strip()))

    if owner.pets:
        st.table(
            [{"Name": p.name, "Species": p.species(), "Tasks": len(p.tasks)} for p in owner.pets]
        )
    else:
        st.info("No pets yet. Add one above.")

with tab_tasks:
    st.subheader("Add a task")

    if not owner.pets:
        st.caption("Add a pet in the Setup tab first, then you can give it tasks.")
    else:
        pet_index = st.selectbox(
            "Pet",
            range(len(owner.pets)),
            format_func=lambda i: f"{owner.pets[i].name} ({owner.pets[i].species()})",
        )
        selected_pet = owner.pets[pet_index]

        col1, col2 = st.columns(2)
        with col1:
            # Only the task types that make sense for this pet's species are offered.
            task_type = st.selectbox("Task type", selected_pet.allowed_task_types())
            task_title = st.text_input("Task title", value="Morning walk")
            frequency = st.selectbox("Repeats", ["once", "daily", "weekly"])
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

        use_preferred = st.checkbox("Set a preferred time")
        preferred_time = None
        if use_preferred:
            picked = st.time_input("Preferred time", value=datetime.time(8, 0))
            preferred_time = picked.hour * 60 + picked.minute

        if st.button("Add task"):
            try:
                selected_pet.add_task(
                    Task(
                        title=task_title.strip() or task_type,
                        task_type=task_type,
                        duration_minutes=int(duration),
                        priority=Priority[priority.upper()],
                        preferred_time=preferred_time,
                        frequency=frequency,
                    )
                )
            except ValueError as e:
                st.error(str(e))

    st.divider()
    st.subheader("Your tasks")

    if not owner.get_all_tasks():
        st.info("No tasks yet. Add one above.")
    else:
        st.subheader("Mark a task done")
        pending = scheduler.sort_by_time(scheduler.filter_tasks(completed=False))
        if pending:
            choice = st.selectbox(
                "Task",
                range(len(pending)),
                format_func=lambda i: f"{pending[i][1].title} ({pending[i][0].name})",
            )
            if st.button("Mark done"):
                pet, task = pending[choice]
                following = scheduler.mark_task_complete(pet, task)
                if following is None:
                    st.success(f"Completed '{task.title}'.")
                else:
                    st.success(
                        f"Completed '{task.title}'. Next {following.frequency} occurrence "
                        f"is due {following.due_date}."
                    )
        else:
            st.caption("Nothing pending.")

        # Conflicts are shown here, before a plan exists, so the owner can fix them early.
        show_conflicts("The scheduler will move the lower-priority task to the next free slot.")

        col1, col2 = st.columns(2)
        with col1:
            pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
        with col2:
            status_filter = st.selectbox("Show status", ["All", "Pending", "Completed"])

        pairs = scheduler.filter_tasks(
            pet_name=None if pet_filter == "All pets" else pet_filter,
            completed={"All": None, "Pending": False, "Completed": True}[status_filter],
        )
        if pairs:
            st.caption("Sorted by preferred time. Tasks without a time are listed last.")
            st.table(task_rows(scheduler.sort_by_time(pairs)))
        else:
            st.info("No tasks match these filters.")

with tab_schedule:
    st.subheader("Build Schedule")

    if st.button("Generate schedule"):
        if not owner.get_all_tasks():
            st.warning("Add at least one task first.")
        else:
            plan = scheduler.generate_plan()

            st.success(
                f"Scheduled {len(plan.scheduled)} task(s), "
                f"{plan.total_minutes} of {owner.available_minutes} minutes used."
            )
            show_conflicts("The plan below resolves them by shifting tasks; see the Why column.")

            if plan.scheduled:
                st.table(
                    [
                        {
                            "Time": f"{format_time(s.start_time)}-{format_time(s.end_time)}",
                            "Task": s.task.title,
                            "Pet": s.pet.name,
                            "Priority": s.task.priority.name,
                            "Why": s.reason,
                        }
                        for s in plan.scheduled
                    ]
                )
            if plan.skipped:
                st.warning(f"Skipped {len(plan.skipped)} task(s):")
                st.table(
                    [
                        {"Task": k.task.title, "Pet": k.pet.name, "Reason": k.reason}
                        for k in plan.skipped
                    ]
                )
