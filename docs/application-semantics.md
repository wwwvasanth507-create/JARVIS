# Application Semantics & Platform Adapters

JARVIS connects platform-native accessibility APIs and application semantics with universal UI element queries.

## Windows UI Automation (`WindowsUIAutomationAdapter`)

On Windows systems, JARVIS utilizes native UI Automation interfaces via `ctypes` and system window handles to extract:
- Window handles and titles
- Control structures (buttons, inputs, menus, scroll bars)
- Automation IDs and bounding rectangles
- Focus and enabled states

## Playwright DOM Semantic Adapter (`BrowserSemanticAdapter`)

For browser automation, JARVIS extracts DOM accessibility trees and element nodes:
- Role mapping (`aria-label`, HTML tags, CSS selectors)
- Bounding boxes and visibility status
- Stale handle defense: Re-resolves element queries dynamically rather than reusing stale Playwright handles
