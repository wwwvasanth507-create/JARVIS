# Tool Dispatching & Standardization

The Tool Dispatcher (`src/jarvis/core/orchestration/dispatcher.py`) maps plan step tool names directly to tool instances registered in `ALL_TOOLS` (`src/jarvis/tools`).

---

## Tool Registry Mapping

The dispatcher searches across all tool domains:
* `application.*`
* `filesystem.*`
* `computer.*`
* `browser.*`
* `shell.*`

---

## Standardized Tool Result

All tools return a standardized `ToolResult` model:

```python
class ToolResult(BaseModel):
    success: bool
    status: ToolResultStatus  # SUCCESS, FAILED, DENIED, CONFIRMATION_REQUIRED, AMBIGUOUS, NOT_FOUND, TIMEOUT, CANCELLED, VERIFICATION_FAILED
    data: Optional[Any] = None
    error: Optional[str] = None
    observations: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
    duration_ms: float = 0.0
```
