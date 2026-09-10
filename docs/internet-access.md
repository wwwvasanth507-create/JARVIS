# JARVIS Controlled Internet Access Layer

## Overview
JARVIS accesses the public internet strictly through controlled local browser automation (`BrowserManager`). External AI APIs, cloud search APIs, and third-party SaaS services are prohibited to maintain total privacy and CPU-first execution.

## Web Search Engine Integration
Web search is performed natively via the browser engine without needing external search API keys:
1. `browser.search` navigates to a configurable search provider (default: DuckDuckGo HTML).
2. `BrowserExtraction.search` extracts structured `SearchResult` items (title, url, snippet, position).
3. Returned search results are formatted for model consumption.

## Allowed Schemes & Network Policy
- **Allowed Schemes**: `http`, `https` (and local `file` in test configurations).
- **Prohibited Schemes**: `javascript:`, `data:`, executable custom URI schemes.
- Security policies defined in `config/permissions.yaml` govern network access risk tiers.
