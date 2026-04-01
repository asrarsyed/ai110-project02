# Algorithm Improvements Reference

Quick reference for the 8 algorithm improvements implemented in PawPal+ scheduling system.

---

## 1. Enhanced Sorting

### `sort_by_time(tasks)` - Multi-level Priority Sorting
Optimized order: fixed-time → critical → priority → duration

```python
sorted_tasks = scheduler.sort_by_time(tasks)
# Returns: [Fixed 7:30 task, Fixed 8:00 task, Critical, Priority 5, Priority 4...]
```

**Implementation:** Tuple-based lambda sorting
```python
key=lambda task: (
    0 if task.fixed_time_minute is not None else 1,  # Fixed time first
    task.fixed_time_minute if task.fixed_time_minute is not None else 10_000,
    0 if task.is_critical else 1,                    # Critical next
    -task.priority,                                  # Higher priority (negative = descending)
    task.duration_minutes,                           # Shorter tasks easier to fit
)
```

### `sort_by_status(tasks)` - NEW
Incomplete tasks first (for to-do lists)

```python
sorted_tasks = scheduler.sort_by_status(tasks)
# Returns: [Incomplete tasks...] then [Complete tasks...]
```

### `sort_by_pet_and_time(schedule_items)` - NEW  
Organize multi-pet schedules by pet, then time

```python
organized = scheduler.sort_by_pet_and_time(schedule)
# Groups all of Max's tasks, then all of Bella's tasks, each chronologically
```

---

## 2. Advanced Filtering

### `filter_tasks()` - Multi-Criteria Filtering (Enhanced: 2 → 5 criteria)

**All parameters are optional:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `completed` | `bool \| None` | Filter by completion status |
| `pet` | `Pet \| None` | Filter specific pet's tasks |
| `recurrence` | `Recurrence \| None` | DAILY, WEEKLY, or ONE_TIME |
| `critical` | `bool \| None` | Filter by critical flag |
| `min_priority` | `int \| None` | Tasks with priority >= value |

**Examples:**
```python
# High-priority incomplete tasks
tasks = scheduler.filter_tasks(completed=False, min_priority=4)

# All critical daily tasks
tasks = scheduler.filter_tasks(recurrence=Recurrence.DAILY, critical=True)

# Combine any criteria
tasks = scheduler.filter_tasks(pet=max_pet, completed=False, min_priority=3)
```

### `filter_by_pets(pets_list)` - NEW
Get tasks for multiple pets at once

```python
tasks = scheduler.filter_by_pets([max_pet, bella_pet])
```

---

## 3. Recurring Task Automation

### `advance_recurring_tasks(tasks)` - NEW
Auto-advances completed recurring tasks to next occurrence

```python
# Mark task complete
task.mark_complete()

# Auto-advance (resets is_complete and advances due date)
scheduler.advance_recurring_tasks([task])

# DAILY tasks → next_due_date = today + timedelta(days=1)
# WEEKLY tasks → next_due_date = today + timedelta(days=7)  
# ONE_TIME → no change
```

**Uses Python's `timedelta`:**
```python
from datetime import timedelta

# In Task.reschedule_next()
if self.recurrence == Recurrence.DAILY:
    self.next_due_date = reference_date + timedelta(days=1)
    self.is_complete = False
```

### `handle_recurring_tasks(tasks)` - Enhanced
Improved date logic for filtering tasks due today

**Logic:**
- ONE_TIME: Include if not complete AND (no due date OR due date ≤ today)
- DAILY/WEEKLY: Include if no due date OR due date ≤ today

---

## 4. Conflict Detection

### `detect_conflicts(schedule_items)` - Enhanced (2 → 5 types)

Returns list of warning messages (doesn't crash program)

**Detects:**
1. **Invalid time ranges** - Start/end outside 0-1440 or start ≥ end
2. **Time window violations** - Task scheduled outside its allowed window
3. **Overlapping tasks** - Shows overlap duration in minutes
4. **Over-scheduling** - Total time exceeds available time

```python
conflicts = scheduler.detect_conflicts(schedule)
# Returns: ["Overlap detected: 'Walk' and 'Feed' conflict by 10 minutes", ...]
```

**Algorithm:** O(n log n) - Sort first, then check each task against previous
```python
items = sorted(schedule_items, key=lambda item: item.start_minute)
for idx, item in enumerate(items):
    if idx > 0:
        prev = items[idx - 1]
        if item.start_minute < prev.end_minute:
            # Conflict detected
```

### `get_unscheduled_tasks(schedule_items)` - NEW
Identifies tasks that couldn't fit in schedule

```python
unscheduled = scheduler.get_unscheduled_tasks(schedule)
# Returns: [(task, pet), (task, pet), ...]

for task, pet in unscheduled:
    print(f"{task.name} ({pet.name}) couldn't fit")
```

---

## Common Usage Patterns

### Pattern 1: Daily Schedule Generation
```python
scheduler = Scheduler(owner=owner, schedule_date=date.today())
schedule = scheduler.generate_schedule()

# Check for issues
conflicts = scheduler.detect_conflicts(schedule)
unscheduled = scheduler.get_unscheduled_tasks(schedule)
```

### Pattern 2: Filter & Sort for Display
```python
# Get high-priority incomplete tasks
tasks = scheduler.filter_tasks(completed=False, min_priority=4)

# Sort by time priority
sorted_tasks = scheduler.sort_by_time(tasks)
```

### Pattern 3: End-of-Day Processing
```python
# Mark completed tasks
for task in completed_today:
    task.mark_complete()

# Auto-advance recurring tasks for tomorrow
all_tasks = owner.get_all_tasks()
scheduler.advance_recurring_tasks(all_tasks)
```

---

## Performance Summary

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| `sort_by_time()` | O(n log n) | Python's Timsort |
| `filter_tasks()` | O(n) | Single pass with multiple criteria |
| `detect_conflicts()` | O(n log n) | Sort + linear check |
| `advance_recurring_tasks()` | O(n) | Single pass |

---

## Step 5: Algorithm Evaluation Decision

**Question:** "How could `detect_conflicts()` be simplified for better readability or performance?"

**AI Suggestion:** Use list comprehensions (more "Pythonic")
```python
# AI's more "Pythonic" version
conflicts = [f"Invalid..." for item in items if invalid_condition]
conflicts.extend([f"Overlap..." for prev, curr in zip(items, items[1:]) if overlap])
```

**My Decision:** ❌ Rejected - Kept original loop-based version

**Reasoning:**
1. **Readability** - Explicit loop is clearer than nested comprehensions
2. **Performance** - Single pass vs. 4 separate comprehensions  
3. **Debuggability** - Can set breakpoints and inspect state
4. **Maintainability** - Easier for future developers to modify

**Key Takeaway:** "Pythonic" doesn't always mean "better" - prioritize readability and maintainability for production code.

---

## Key Design Tradeoff

**Scheduler uses sequential greedy approach** (not optimal bin-packing)

- Schedules tasks one at a time in priority order
- Does NOT rearrange already-scheduled tasks
- Higher priority tasks always get their preferred times

**Why this is reasonable:**
- Simple and predictable for users
- Fast: O(n log n) vs. NP-complete for optimal packing
- Matches real-world pet routines (morning walk stays at 8 AM)
- Critical flag handles edge cases

**Alternative (rejected):** Constraint satisfaction or bin-packing would fit more tasks but sacrifice predictability and performance.

---

## Testing

Run comprehensive test suite:
```bash
python -m pytest tests/ -v
```

Run demo:
```bash
python3 main.py  # Shows all improvements in action
```
