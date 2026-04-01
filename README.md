# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

- [x] 1. Read the scenario carefully and identify [requirements](notes/requirements.md) and [edge cases](notes/edgecases.md).
- [x] 2. Draft a UML diagram (classes, attributes, methods, relationships).
    - [x] a. List the [building blocks](notes/brainstorm.md) needed for the system
    - [x] b. Actually draft the [UML Diagram](notes/umldiagram.md)
- [x] 3. Convert UML into Python class stubs (no logic yet).
- [x] 4. Implement scheduling logic in small increments.
- [x] 5. Add tests to verify key behaviors.
- [x] 6. Connect your logic to the Streamlit UI in `app.py`.
- [x] 7. Refine UML so it matches what you actually built.

## Testing PawPal+

### Run tests

```bash
python -m pytest tests/ -v
```

### What the tests cover

40 tests across two files:

- **Core behavior** — marking tasks complete, adding tasks to pets
- **Sorting** — schedule output is in chronological order, `sort_by_time` respects the fixed time > critical > priority > duration hierarchy
- **Recurrence** — daily tasks advance by 1 day, weekly by 7, one-time tasks are not rescheduled; future-dated tasks are excluded from today's schedule
- **Conflict detection** — overlapping tasks, tasks outside their time window, invalid time ranges (negative, beyond 1440, start >= end), over-scheduling
- **Edge cases** — midnight boundary (minute 0), end-of-day boundary (minute 1430-1440), tasks that exceed the day are rejected, critical tasks bypass the time budget, zero/negative available time, invalid task names/priority/duration, multi-pet interleaving, back-to-back tasks with no gap

### Confidence level

4/5 stars

The core scheduling logic, sorting, filtering, recurrence, and conflict detection are all well covered and passing. One star held back because the tests don't yet cover every edge case from [notes/edgecases.md](notes/edgecases.md) — specifically tasks with a fixed time that conflicts with their own time window at the scheduler level, and schedules where all tasks are critical and collectively exceed available time.
