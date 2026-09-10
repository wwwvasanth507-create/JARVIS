# JARVIS Browser Testing & Verification Strategy

## Test Suite Architecture
- **Unit Tests (`tests/unit/test_browser.py`)**: Tests `BrowserManager`, URL validation, `SelectorEngine` resolution, state models, error handling, and tool registrations using mocks.
- **Integration Tests (`tests/integration/test_browser_integration.py`)**: Executes deterministic browser workflows against a local HTML fixture (`tests/browser/fixtures/sample_page.html`) without requiring internet access.
- **Performance Benchmarks (`tests/evaluation/performance/test_browser_benchmark.py`)**: Measures startup time, navigation latency, extraction time, tab creation speed, screenshot latency, and CPU overhead.

## Running Tests
```bash
# Run unit tests
python -m pytest tests/unit/test_browser.py

# Run browser integration test
python -m pytest tests/integration/test_browser_integration.py

# Run browser performance benchmarks with output
python -m pytest tests/evaluation/performance/test_browser_benchmark.py -s

# Run full test suite
python -m pytest
```
