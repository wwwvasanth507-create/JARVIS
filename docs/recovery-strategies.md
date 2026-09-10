# Recovery Strategies Catalog

| Strategy ID | Description | Risk Level | Expected Outcome |
|---|---|---|---|
| `RETRY_ONCE` | Re-attempt failed action once | LOW | Resolve transient timeout |
| `REFRESH_STATE` | Capture fresh screen & window state | LOW | Obtain updated screen coordinates |
| `REFRESH_APPLICATION_REGISTRY` | Rescan installed desktop apps | LOW | Discover updated executable path |
| `RELOAD_BROWSER_PAGE` | Reload browser page and wait | LOW | Restore stale DOM state |
| `REQUERY_FILESYSTEM` | Search alternative permitted directories | LOW | Locate moved or candidate file |
| `REBUILD_PLAN` | Reconstruct plan using evidence | MEDIUM | Execute revised goal steps |
| `REQUEST_USER` | Prompt Boss for guidance | HIGH | Receive explicit human decision |
