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

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.
"""
    )

# st.session_state persists across reruns. Streamlit re-executes this whole script on every
# interaction, so only create the Owner if one is not already stored.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
owner = st.session_state.owner

st.divider()

st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.available_minutes = int(
        st.number_input(
            "Time available today (minutes)", min_value=10, max_value=720, value=owner.available_minutes
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

st.markdown("### Tasks")

if not owner.pets:
    st.caption("Add a pet first, then you can give it tasks.")
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
                )
            )
        except ValueError as e:
            st.error(str(e))

all_pairs = owner.get_all_tasks()
if all_pairs:
    st.write("Current tasks:")
    st.table(
        [
            {
                "Pet": pet.name,
                "Task": task.title,
                "Type": task.task_type,
                "Minutes": task.duration_minutes,
                "Priority": task.priority.name,
                "Preferred": format_time(task.preferred_time) if task.preferred_time is not None else "-",
            }
            for pet, task in all_pairs
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if not all_pairs:
        st.warning("Add at least one task first.")
    else:
        plan = Scheduler(owner).generate_plan()

        st.success(
            f"Scheduled {len(plan.scheduled)} task(s), "
            f"{plan.total_minutes} of {owner.available_minutes} minutes used."
        )
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
                [{"Task": k.task.title, "Pet": k.pet.name, "Reason": k.reason} for k in plan.skipped]
            )
