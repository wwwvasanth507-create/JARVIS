# Central Resource Arbitrator

## Resource Arbitration (`src/jarvis/system/resource_arbitrator.py`)
Governs time-bounded resource leases and concurrency limits for Model, Browser, Vision, and Voice subsystems.

### Priority Rules:
- Higher-priority user commands (Priority 3) automatically preempt background leases (Priority 1), enforcing low idle CPU and CPU-first memory limits.
