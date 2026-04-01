import streamlit as st
from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
available_time_minutes = st.number_input(
    "Available time today (minutes)", min_value=0, max_value=1440, value=120
)
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

# Persist the main domain object across Streamlit reruns.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name=owner_name, available_time_minutes=int(available_time_minutes)
    )
else:
    # Reuse the same object while syncing editable UI fields.
    st.session_state.owner.name = owner_name
    st.session_state.owner.available_time_minutes = int(available_time_minutes)

owner = st.session_state.owner


def get_or_create_pet(current_owner: Owner, name: str, pet_species: str) -> Pet:
    for existing_pet in current_owner.pets:
        if existing_pet.name == name:
            return existing_pet
    new_pet = Pet(name=name, species=pet_species)
    current_owner.add_pet(new_pet)
    return new_pet


def map_priority(priority_label: str) -> int:
    if priority_label == "high":
        return 5
    if priority_label == "medium":
        return 3
    return 1


def minute_to_hhmm(minute: int) -> str:
    return f"{minute // 60:02d}:{minute % 60:02d}"


if st.button("Add / Select Pet"):
    if not pet_name.strip():
        st.error("Pet name cannot be empty.")
    else:
        selected_pet = get_or_create_pet(owner, pet_name.strip(), species)
        st.session_state.active_pet_name = selected_pet.name
        st.success(f"Pet '{selected_pet.name}' is ready for tasks.")

if owner.pets:
    st.caption("Pets in owner profile")
    st.write(", ".join(pet.name for pet in owner.pets))

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    active_name = st.session_state.get("active_pet_name", "").strip()
    normalized_pet_name = active_name or pet_name.strip()
    if not normalized_pet_name:
        st.error("Select a pet first using 'Add / Select Pet'.")
    else:
        target_pet = get_or_create_pet(owner, normalized_pet_name, species)
        try:
            target_pet.add_task(
                Task(
                    name=task_title,
                    duration_minutes=int(duration),
                    priority=map_priority(priority),
                )
            )
            st.success(f"Added task '{task_title}' to {target_pet.name}.")
        except ValueError as exc:
            st.error(str(exc))

task_rows = []
for pet in owner.pets:
    for task in pet.get_tasks():
        task_rows.append(
            {
                "pet": pet.name,
                "title": task.name,
                "duration_minutes": task.duration_minutes,
                "priority": task.priority,
            }
        )

if task_rows:
    st.write("Current tasks:")
    st.table(task_rows)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    scheduler = Scheduler(owner=owner)
    schedule = scheduler.generate_schedule()

    if not schedule:
        st.info("No tasks were scheduled. Add tasks and try again.")
    else:
        conflicts = scheduler.detect_conflicts(schedule)
        if conflicts:
            for conflict in conflicts:
                st.warning(f"Schedule conflict: {conflict}")
        else:
            st.success("Schedule generated.")
        schedule_rows = []
        for item in schedule:
            schedule_rows.append(
                {
                    "time": f"{minute_to_hhmm(item.start_minute)}-{minute_to_hhmm(item.end_minute)}",
                    "pet": item.pet.name,
                    "task": item.task.name,
                    "reason": item.reason,
                }
            )
        st.table(schedule_rows)
