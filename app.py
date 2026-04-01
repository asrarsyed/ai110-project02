from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Recurrence, Scheduler, Task, TimeWindow

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ── helpers ──────────────────────────────────────────────────────────────────

def minute_to_hhmm(minute: int) -> str:
    return f"{minute // 60:02d}:{minute % 60:02d}"


def map_priority(label: str) -> int:
    return {"low": 1, "medium": 3, "high": 5}.get(label, 3)


def priority_label(value: int) -> str:
    if value >= 5:
        return "High"
    if value >= 3:
        return "Medium"
    return "Low"


def get_or_create_pet(owner: Owner, name: str, species: str) -> Pet:
    for pet in owner.pets:
        if pet.name == name:
            return pet
    new_pet = Pet(name=name, species=species)
    owner.add_pet(new_pet)
    return new_pet


# ── session state init ────────────────────────────────────────────────────────

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_time_minutes=180)

# ── header ────────────────────────────────────────────────────────────────────

st.title("🐾 PawPal+")
st.caption("A daily pet care planner that schedules tasks by priority, time constraints, and recurrence.")
st.divider()

# ── sidebar: owner & pet setup ───────────────────────────────────────────────

with st.sidebar:
    st.header("Owner")
    owner_name = st.text_input("Name", value=st.session_state.owner.name)
    available_time = st.number_input(
        "Available time today (min)", min_value=0, max_value=1440,
        value=st.session_state.owner.available_time_minutes,
    )
    st.session_state.owner.name = owner_name
    st.session_state.owner.available_time_minutes = int(available_time)
    owner: Owner = st.session_state.owner

    st.divider()
    st.header("Add Pet")
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    age = st.number_input("Age (years, optional)", min_value=0, max_value=30, value=0)
    medical = st.text_input("Medical needs (optional)", value="")

    if st.button("Add / Select Pet", use_container_width=True):
        if not pet_name.strip():
            st.error("Pet name cannot be empty.")
        else:
            pet = get_or_create_pet(owner, pet_name.strip(), species)
            pet.age = age if age > 0 else None
            pet.medical_needs = medical.strip() or None
            st.session_state.active_pet_name = pet.name
            st.success(f"'{pet.name}' is active.")

    if owner.pets:
        st.divider()
        st.caption("Pets on roster")
        for p in owner.pets:
            badge = f"**{p.name}**  `{p.species}`"
            if p.medical_needs:
                badge += f"  ⚕ {p.medical_needs}"
            st.markdown(badge)

# ── tabs ──────────────────────────────────────────────────────────────────────

tab_tasks, tab_filter, tab_schedule = st.tabs(["Add Tasks", "Browse & Filter", "Schedule"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 – ADD TASKS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_tasks:
    st.subheader("Add a Task")

    active_pet_name = st.session_state.get("active_pet_name", "")
    if not active_pet_name and owner.pets:
        active_pet_name = owner.pets[0].name

    pet_options = [p.name for p in owner.pets] if owner.pets else []
    if not pet_options:
        st.info("Add a pet in the sidebar first, then come back to add tasks.")
    else:
        selected_pet_name = st.selectbox(
            "Assign to pet", pet_options,
            index=pet_options.index(active_pet_name) if active_pet_name in pet_options else 0,
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            task_title = st.text_input("Task name", value="Morning walk")
            duration = st.number_input("Duration (min)", min_value=1, max_value=480, value=30)
        with col2:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
            recurrence_label = st.selectbox("Recurrence", ["One-time", "Daily", "Weekly"])
            recurrence_map = {
                "One-time": Recurrence.ONE_TIME,
                "Daily": Recurrence.DAILY,
                "Weekly": Recurrence.WEEKLY,
            }
            recurrence = recurrence_map[recurrence_label]
        with col3:
            is_critical = st.checkbox("Critical (must schedule)")
            use_fixed = st.checkbox("Fixed time")
            fixed_hhmm = st.text_input(
                "Fixed time (HH:MM)", value="08:00",
                disabled=not use_fixed,
                help="24-hour format, e.g. 08:00 or 14:30",
            )
            use_window = st.checkbox("Time window")
            win_col1, win_col2 = st.columns(2)
            with win_col1:
                window_start = st.text_input("Window start", value="07:00", disabled=not use_window)
            with win_col2:
                window_end = st.text_input("Window end", value="10:00", disabled=not use_window)

        if st.button("Add Task", type="primary", use_container_width=True):
            errors = []

            fixed_minute = None
            if use_fixed:
                try:
                    h, m = map(int, fixed_hhmm.split(":"))
                    fixed_minute = h * 60 + m
                    if not 0 <= fixed_minute <= 1439:
                        errors.append("Fixed time must be between 00:00 and 23:59.")
                except ValueError:
                    errors.append("Fixed time must be in HH:MM format.")

            time_window = None
            if use_window:
                try:
                    sh, sm = map(int, window_start.split(":"))
                    eh, em = map(int, window_end.split(":"))
                    time_window = TimeWindow(sh * 60 + sm, eh * 60 + em)
                    if not time_window.validate():
                        errors.append("Time window is invalid (start must be before end, within 0–1439).")
                except ValueError:
                    errors.append("Time window values must be in HH:MM format.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                today = date.today()
                due = today if recurrence != Recurrence.ONE_TIME else None
                target_pet = get_or_create_pet(owner, selected_pet_name, "unknown")
                try:
                    target_pet.add_task(
                        Task(
                            name=task_title,
                            duration_minutes=int(duration),
                            priority=map_priority(priority),
                            fixed_time_minute=fixed_minute,
                            time_window=time_window,
                            recurrence=recurrence,
                            next_due_date=due,
                            is_critical=is_critical,
                        )
                    )
                    st.success(f"Added '{task_title}' to {selected_pet_name}.")
                except ValueError as exc:
                    st.error(str(exc))

        st.divider()
        st.subheader("All Tasks (sorted by scheduling priority)")

        all_tasks = owner.get_all_tasks()
        if not all_tasks:
            st.info("No tasks yet.")
        else:
            scheduler_preview = Scheduler(owner=owner, schedule_date=date.today())
            sorted_tasks = scheduler_preview.sort_by_time(all_tasks)
            tasks_by_id = {}
            for pet in owner.pets:
                for t in pet.tasks:
                    tasks_by_id[id(t)] = pet.name

            rows = []
            for t in sorted_tasks:
                fixed = minute_to_hhmm(t.fixed_time_minute) if t.fixed_time_minute is not None else "—"
                window = (
                    f"{minute_to_hhmm(t.time_window.start_minute)}–{minute_to_hhmm(t.time_window.end_minute)}"
                    if t.time_window else "—"
                )
                rows.append({
                    "Pet": tasks_by_id.get(id(t), "?"),
                    "Task": ("🚨 " if t.is_critical else "") + t.name,
                    "Duration": f"{t.duration_minutes} min",
                    "Priority": priority_label(t.priority),
                    "Fixed Time": fixed,
                    "Window": window,
                    "Recurrence": t.recurrence.value.capitalize(),
                    "Done": "✓" if t.is_complete else "",
                })
            st.table(rows)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 – BROWSE & FILTER
# ═══════════════════════════════════════════════════════════════════════════════

with tab_filter:
    st.subheader("Browse & Filter Tasks")

    if not owner.pets:
        st.info("No pets or tasks yet.")
    else:
        scheduler_filter = Scheduler(owner=owner, schedule_date=date.today())

        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            pet_filter_options = ["All pets"] + [p.name for p in owner.pets]
            pet_filter = st.selectbox("Pet", pet_filter_options)
        with col_b:
            rec_options = ["All", "One-time", "Daily", "Weekly"]
            rec_filter = st.selectbox("Recurrence", rec_options)
        with col_c:
            pri_filter = st.selectbox("Min priority", ["Any", "Low (1+)", "Medium (3+)", "High (5)"])
        with col_d:
            critical_filter = st.selectbox("Critical", ["All", "Critical only", "Non-critical"])

        selected_pet_obj = None
        if pet_filter != "All pets":
            selected_pet_obj = next((p for p in owner.pets if p.name == pet_filter), None)

        rec_enum_map = {
            "One-time": Recurrence.ONE_TIME,
            "Daily": Recurrence.DAILY,
            "Weekly": Recurrence.WEEKLY,
        }
        rec_enum = rec_enum_map.get(rec_filter)

        min_pri_map = {"Low (1+)": 1, "Medium (3+)": 3, "High (5)": 5}
        min_pri = min_pri_map.get(pri_filter)

        critical_flag = None
        if critical_filter == "Critical only":
            critical_flag = True
        elif critical_filter == "Non-critical":
            critical_flag = False

        filtered = scheduler_filter.filter_tasks(
            pet=selected_pet_obj,
            recurrence=rec_enum,
            critical=critical_flag,
            min_priority=min_pri,
        )

        if not filtered:
            st.warning("No tasks match the selected filters.")
        else:
            st.success(f"{len(filtered)} task(s) found.")
            tasks_by_id = {}
            for pet in owner.pets:
                for t in pet.tasks:
                    tasks_by_id[id(t)] = pet.name

            sorted_filtered = scheduler_filter.sort_by_time(filtered)
            rows = []
            for t in sorted_filtered:
                rows.append({
                    "Pet": tasks_by_id.get(id(t), "?"),
                    "Task": ("🚨 " if t.is_critical else "") + t.name,
                    "Duration": f"{t.duration_minutes} min",
                    "Priority": priority_label(t.priority),
                    "Recurrence": t.recurrence.value.capitalize(),
                    "Status": "Complete" if t.is_complete else "Pending",
                })
            st.table(rows)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 – SCHEDULE
# ═══════════════════════════════════════════════════════════════════════════════

with tab_schedule:
    st.subheader("Generate Daily Schedule")

    schedule_date = st.date_input("Schedule for", value=date.today())

    col_gen, col_reset = st.columns([2, 1])
    with col_gen:
        generate = st.button("Generate Schedule", type="primary", use_container_width=True)
    with col_reset:
        if st.button("Clear Schedule", use_container_width=True):
            st.session_state.pop("last_schedule", None)
            st.session_state.pop("last_scheduler", None)
            st.rerun()

    if generate:
        if not owner.pets or not owner.get_all_tasks():
            st.warning("Add at least one pet and one task before generating a schedule.")
        else:
            scheduler = Scheduler(owner=owner, schedule_date=schedule_date)
            schedule = scheduler.generate_schedule()
            st.session_state.last_schedule = schedule
            st.session_state.last_scheduler = scheduler

    schedule = st.session_state.get("last_schedule")
    scheduler = st.session_state.get("last_scheduler")

    if schedule is not None and scheduler is not None:
        st.divider()

        # summary metrics
        total_scheduled = sum(item.task.duration_minutes for item in schedule)
        available = scheduler.get_available_time_minutes()
        unscheduled = scheduler.get_unscheduled_tasks(schedule)
        conflicts = scheduler.detect_conflicts(schedule)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tasks Scheduled", len(schedule))
        m2.metric("Time Used", f"{total_scheduled} min")
        m3.metric("Time Available", f"{available} min")
        m4.metric("Conflicts", len(conflicts))

        st.divider()

        # conflict warnings
        if conflicts:
            st.subheader("Conflict Warnings")
            for c in conflicts:
                st.warning(c)
        else:
            st.success("No scheduling conflicts detected.")

        # schedule table
        st.subheader("Today's Schedule")
        if not schedule:
            st.info("No tasks could be scheduled with the current constraints.")
        else:
            rows = []
            for item in schedule:
                rows.append({
                    "Time": f"{minute_to_hhmm(item.start_minute)} – {minute_to_hhmm(item.end_minute)}",
                    "Pet": item.pet.name,
                    "Task": ("🚨 " if item.task.is_critical else "") + item.task.name,
                    "Duration": f"{item.task.duration_minutes} min",
                    "Priority": priority_label(item.task.priority),
                    "Reason": item.reason,
                })
            st.table(rows)

        # unscheduled tasks
        if unscheduled:
            st.subheader("Unscheduled Tasks")
            st.warning(f"{len(unscheduled)} task(s) could not fit in the schedule.")
            rows = []
            for task, pet in unscheduled:
                rows.append({
                    "Pet": pet.name,
                    "Task": task.name,
                    "Duration": f"{task.duration_minutes} min",
                    "Priority": priority_label(task.priority),
                    "Critical": "Yes" if task.is_critical else "No",
                })
            st.table(rows)
        else:
            st.success("All tasks were scheduled successfully.")
