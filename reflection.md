# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I started with four classes: `Owner`, `Pet`, `Task`, and `Scheduler`. The idea was to keep responsibilities separated: `Pet` holds tasks, `Owner` holds pets and the available time budget, and `Scheduler` handles all the scheduling logic. I also added `TimeWindow`, `Recurrence`, and `ScheduleItem` as supporting types to make constraints and output explicit rather than buried in strings or raw integers. The full diagram is in [notes/umldiagram.md](notes/umldiagram.md).

**b. Design changes**

Two things changed. First, I switched time fields from strings to integer minutes, so `9:00 AM` becomes `540`. This made sorting and conflict checks a lot simpler since you can just compare numbers. Second, I added a `schedule_date` field to `Scheduler` and a `reference_date` parameter to `Task.reschedule_next()`. Without a date reference, weekly recurring tasks had no way to know when they were next due or how to advance correctly.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers fixed times, time windows, priority (1-5), the critical flag, available time, duration, and recurrence rules. The priority order I settled on is: fixed time first, then critical flag, then priority level, then shorter duration as a tiebreaker. Fixed time is at the top because those tasks have no flexibility. Critical is next because something like medication shouldn't get skipped just because the schedule is full. See [notes/edgecases.md](notes/edgecases.md) for the edge cases that shaped these decisions.

**b. Tradeoffs**

The scheduler is greedy. It places tasks one at a time in priority order and never rearranges earlier ones to fit later ones. So if a 30-minute high-priority task locks in a time slot, a lower-priority task that could've fit if things were reordered just gets skipped. The alternative would be something like bin-packing, which could fit more tasks overall, but it's NP-complete and unpredictable. A pet owner probably doesn't want the morning walk randomly moved to fit something else. Predictability felt more important than squeezing in one extra task.

---

## 3. AI Collaboration

**a. How you used AI**

I mainly used AI for implementing the lambda sorting key and for thinking through the conflict detection algorithm. The prompts that helped most were asking how to sort by multiple criteria at once (which led to the tuple-based key in `sort_by_time`) and asking what a lightweight conflict detection strategy would look like (which confirmed the sort-then-linear-scan approach). I also used it to debug why recurring tasks weren't advancing. The issue turned out to be missing the `reference_date` parameter. More detail on the algorithm decisions is in [notes/algorithm_reference.md](notes/algorithm_reference.md).

**b. Judgment and verification**

When I asked for help with `detect_conflicts()`, the initial suggestion was a nested loop that compared every pair of tasks. It was O(n²) and would report the same conflict twice (once for A to B, once for B to A). I rejected that and kept the sort-first, sequential-check approach instead. It's O(n log n), finds each conflict exactly once, and is easier to follow. I verified it manually with overlapping test cases and confirmed it caught all conflicts without duplicates.

---

## 4. Testing and Verification

**a. What you tested**

I tested the core scheduling behaviors: that tasks sort correctly by priority and fixed time, that filtering by pet, recurrence, priority, and critical flag all work individually and in combination, that recurring tasks advance by the right number of days, that `detect_conflicts` catches overlaps, time window violations, and over-scheduling, and that `get_unscheduled_tasks` correctly identifies tasks that didn't fit. These mattered because they're the behaviors the scheduler depends on. If sorting or filtering is wrong, the generated schedule is wrong.

**b. Confidence**

I'm fairly confident the scheduler handles the main cases correctly. The tests cover the algorithm improvements and the happy path. Edge cases I'd want to add more coverage for: tasks with both a fixed time and a time window that conflict with each other, schedules where every task is critical and exceeds available time, and multiple pets with overlapping fixed-time tasks. The existing edge case list in [notes/edgecases.md](notes/edgecases.md) has a few more I didn't fully test.

---

## 5. Reflection

**a. What went well**

The class structure held up well throughout. I didn't have to rethink the overall design, just fill in the details. Having `Scheduler` separate from the data classes meant I could change scheduling logic without touching `Task` or `Pet`, which made iteration easier.

**b. What you would improve**

The greedy scheduler works, but it sometimes produces schedules with gaps that look odd. For example, a task might end up at midnight because that was the first open slot. I'd want to add a preference for scheduling tasks later in the day (closer to when they'd actually happen) rather than always packing them toward the start. I'd also improve the Streamlit UI to actually reflect the full system, since right now it's mostly a placeholder.

**c. Key takeaway**

The main thing I learned is that AI suggestions are a starting point, not a final answer. The nested-loop conflict detection it suggested would have worked, but it wasn't the right tradeoff for this case. Having a clear sense of what I actually needed (single-pass, no duplicate messages, readable) made it easy to evaluate the suggestion and push back.
