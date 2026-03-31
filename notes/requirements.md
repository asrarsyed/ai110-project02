### Core Functional Requirements

#### Owner

- Name
- Available time (total or time window)
- Preferences (optional)

#### Pet

- Name
- Type
- Optional attributes (age, medical needs)

#### Task

- Name
- Duration (minutes)
- Priority (e.g., 1–5)
- Optional time constraint:

  - Fixed time (e.g., 8:00 AM)
  - Time window (e.g., 7–10 AM)
- Recurrence (daily, weekly, one-time)

#### Scheduler

- Input: tasks + available time
- Output: daily schedule
- Must:

  - Prioritize tasks
  - Respect time constraints
  - Avoid overlaps
  - Stay within available time

#### Output

- Ordered schedule with times
- Optional explanation of decisions