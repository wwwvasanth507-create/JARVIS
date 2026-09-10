# Recovery, Retries & Loop Detection

The Recovery subsystem (`src/jarvis/core/orchestration/recovery.py`) provides bounded fault handling and prevents infinite execution loops.

---

## Recovery Policies

1. **Step-Level Retries**:
   * Low and Medium risk steps allow `max_retries_per_step = 1`.
   * High and Critical risk steps **never** auto-retry.
2. **Replanning Bounds**:
   * `max_replans = 2`.
   * Any new plan generated during replanning must pass full static validation (`PlanValidator`).
3. **Loop Detection**:
   * Tracks tool action signatures (`tool_name:arguments:error`).
   * If 3 identical tool execution failures occur sequentially, `LoopDetectedError` is raised and execution stops immediately.
