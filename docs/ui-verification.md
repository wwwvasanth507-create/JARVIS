# UI Action Verification & Classified Change Detection

JARVIS verifies action completion by comparing before and after semantic snapshots.

## Classified UI State Changes (`UIStateDiffEngine`)

Categorizes UI state diffs:
- `NO_CHANGE`
- `MINOR_CHANGE`
- `MAJOR_CHANGE`
- `NAVIGATION`
- `DIALOG_OPENED`
- `DIALOG_CLOSED`
- `FORM_UPDATED`
- `TABLE_UPDATED`
- `LOADING_STARTED`
- `LOADING_FINISHED`
- `ERROR_APPEARED`
- `SUCCESS_APPEARED`

## Post-Action Verification Strategy

After executing a UI action (e.g. clicking Submit):
1. Captures post-action `ScreenSemanticSnapshot`.
2. Computes diff against pre-action state.
3. Verifies expected post-conditions (e.g., dialog closed, success toast appeared, navigation occurred).
4. Emits `ACTION_VERIFIED` or `ACTION_FAILED` event.
