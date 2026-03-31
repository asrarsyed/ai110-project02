### Building Blocks

| Class         | Attributes                                                                                                                                                                                | Methods                                                                                                               |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Owner**     | `name`, `available_time`, `preferences` (optional), `pets` (list of Pet objects)                                                                                                          | `add_pet(pet)`, `get_all_tasks()`, `remove_pet(pet)`                                                                  |
| **Pet**       | `name`, `type`, `age` (optional), `medical_needs` (optional), `tasks` (list of Task objects)                                                                                              | `add_task(task)`, `get_tasks()`, `remove_task(task)`                                                                  |
| **Task**      | `name`, `duration` (minutes), `priority` (1–5), `fixed_time` (optional), `time_window` (optional), `recurrence` (daily, weekly, one-time), `is_complete` (bool), `is_critical` (optional) | `mark_complete()`, `reschedule_next()`, `validate()`                                                                  |
| **Scheduler** | `tasks` (list of Task objects), `available_time`, `owner`                                                                                                                                 | `generate_schedule()`, `sort_by_time()`, `filter_tasks(status/pet)`, `detect_conflicts()`, `handle_recurring_tasks()` |


---

### Notes

- **Attributes**: Include all information that the class needs to hold. Optional attributes are marked for future enhancements, i.e. they are not a primary concern for the class.
- **Methods**: Include actions the object can perform, especially ones needed to handle edge cases (conflicts, recurring tasks, critical tasks).