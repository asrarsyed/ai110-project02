# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

For my initial UML design of PawPal+, I identified four main classes based on the core functional requirements and anticipated edge cases: **Owner, Pet, Task, and Scheduler**. Each class has clearly defined responsibilities that ensure modularity and allow for independant debugging.

#### Classes and Responsibilities

1. **Owner**

   - **Attributes**: `name`, `available_time`, `preferences` (optional)
   - **Responsibilities**:

     - Manage multiple pets
     - Provide access to pet and task data across pets
     - Store scheduling constraints and preferences that the Scheduler reads

   The `get_all_tasks()` method is a data-access helper that aggregates tasks across pets. The `Scheduler` remains solely responsible for scheduling decisions.

2. **Pet**

   - **Attributes**: `name`, `type`, optional details (`age`, `medical_needs`)
   - **Responsibilities**:

     - Store pet-specific information
     - Maintain a list of tasks assigned to this pet
     - Support adding or retrieving tasks

3. **Task**

   - **Attributes**: `name`, `duration`, `priority`, optional time constraint (`fixed_time` or `time_window`), `recurrence`
   - **Responsibilities**:

     - Represent a single activity for a pet
     - Track completion status
     - Handle recurrence rules for daily or weekly tasks
     - Ensure validity of task details (e.g., positive duration, valid priority)

4. **Scheduler**

   - **Attributes/Inputs**: `owner` plus derived working data (tasks and available time)
   - **Responsibilities**:

     - Generate a daily schedule that prioritizes tasks based on priority, recurrence, and time constraints
     - Use internal helper steps (sorting, conflict detection, recurrence handling) as part of `generate_schedule()`
     - Handle edge cases such as exceeding available time, skipped critical tasks, and duplicate recurring tasks
     - Produce a list of `ScheduleItem` outputs with task, start time, end time, and reasoning

   The Scheduler derives tasks and available time from the Owner and may store them as temporary working data during schedule generation rather than as independent sources of truth.

#### UML Overview

- **Relationships**:

  - `Owner` owns multiple `Pets`
  - Each `Pet` has multiple `Tasks`
  - `Scheduler` reads constraints from the `Owner`, gathers all tasks, and generates a coherent daily schedule
  - The final output is represented as a list of `ScheduleItem` objects

- **Design Principles**:

  - Separation of concerns: Each class has a single responsibility
  - Modularity: Adding new pets or task types requires minimal changes
  - Edge case handling is incorporated early to ensure robustness

- **Edge Case to Design Mapping**:

  - `Task.validate()` ensures valid duration and priority values
  - `Scheduler.detect_conflicts()` identifies overlapping or invalid task timings
  - `Scheduler.generate_schedule()` handles time overflow by prioritizing tasks and dropping lower-priority tasks when needed
  - `Task.is_critical` helps ensure essential tasks (for example medication) are not skipped


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
