# JARVIS Browser Automation Subsystem

## Overview
The JARVIS Browser Automation Subsystem provides a lightweight, local-first browser automation layer powered by **Playwright**. It enables JARVIS to navigate websites, manage tabs, extract structured content, perform web searches, click elements, fill forms, handle downloads/uploads securely, and verify post-action states on CPU-only hardware without third-party AI APIs or cloud dependencies.

## Architecture
```
src/jarvis/browser/
├── __init__.py         # Package initialization
├── manager.py          # BrowserManager orchestrator (lifecycle, session reuse, health check)
├── session.py          # BrowserSession (Playwright process & context manager)
├── navigation.py       # BrowserNavigation (URL validation, goto, back, forward, reload)
├── tabs.py             # BrowserTabs (tab listing, creation, switching, closing)
├── interaction.py      # BrowserInteraction (clicking, typing, filling, pressing, scrolling)
├── extraction.py       # BrowserExtraction (structured page reading, web search extraction)
├── downloads.py        # BrowserDownloads (controlled downloads, security validation)
├── uploads.py          # BrowserUploads (file upload validation)
├── forms.py            # BrowserForms (form field extraction, filling, sensitive action hooks)
├── selectors.py        # SelectorEngine (role, label, text, CSS, XPath resolution)
├── state.py            # BrowserState, TabInfo, BrowserActionResult data models
├── verification.py     # BrowserVerification (post-action assertion & status check)
└── errors.py           # Custom exception classes
```

## Browser Manager Lifecycle & Session Reuse
The `BrowserManager` maintains a persistent `BrowserSession`. The browser process is launched lazily on the first request and kept warm across multiple commands, eliminating process startup overhead.

```python
from jarvis.browser.manager import BrowserManager

manager = BrowserManager()
manager.start()

# Reuses warm browser session
manager.open("https://www.youtube.com")
manager.search("Tamil songs")

manager.stop()
```

## CPU Performance Optimization
- **Structured DOM APIs**: Uses Playwright's accessibility tree and DOM querying instead of continuous screenshots.
- **Content Limits**: Page reading (`read_page`) truncates text to 10,000 characters and limits links/forms to prevent local model context overflow.
- **No Vision Latency**: Vision model calls are completely avoided for standard element location and interaction.
