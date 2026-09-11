# Priority Scheduling & Starvation Protection

## Scheduling Precedence
The `BoundedGoalPriorityQueue` orders executable goals using deterministic priority rules:
```text
Direct Boss Command (Highest Priority)
  ↓
Critical Deadline Goals
  ↓
High-Priority User Goals
  ↓
Scheduled Goals
  ↓
Background Monitoring
  ↓
Low-Priority Maintenance (Lowest Priority)
```

## Starvation Protection
To prevent low-priority goals from starving indefinitely:
- Enqueued goals track their wait duration (`enqueue_time`).
- Goals waiting longer than `starvation_threshold_sec` (default 300s) receive a bounded priority boost.
- High-priority Boss commands always retain top precedence.
