### Key Edge Cases

#### Time Issues

- Total task time exceeds available time → drop lowest priority or warn
- Invalid duration (0 or negative) → reject
- Overlapping fixed-time tasks → detect conflict
- Invalid minute values for time fields (must be 0-1439) → reject
- Overnight windows (`end_minute < start_minute`) are out of scope unless explicitly supported

#### Task Conflicts

- Multiple tasks at same time
- Tasks outside allowed windows
- Duplicate tasks

#### Recurring Tasks

- Duplicate recurring entries
- Wrong day for weekly tasks

#### Priority Issues

- Same priority for all tasks → fallback rule (e.g., shortest duration)
- Invalid priority values

#### Input Issues

- No tasks → empty schedule
- No available time set
- Too many tasks

#### Critical Case

- Required tasks (e.g., medication) skipped due to time → must be handled explicitly