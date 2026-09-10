# Structured UI State & State Diff Engine

## UI State Model (`src/jarvis/computer/vision/ui_state_model.py`)
Represents screen and desktop application state as structured descriptors (`UIStateModel`, `UIElementDescriptor`) with confidence ratings (`HIGH`, `MEDIUM`, `LOW`).

## State Diff Engine (`UIStateDiffEngine`)
Computes structured before/after diffs detecting app changes, window title updates, modal dialog appearances, and loading completion without requiring expensive full-image visual models.
