# Phase 5.1 — ValidationSetEditor (Create + Modify merged)

Apply on top of Phase 4: `git apply phase5-1.patch`, or copy the 2 files and
DELETE CreateValidationSet.vue + ModifyValidationSet.vue.

The two pages were 80% identical (280/1430 differing lines, measured). One
component now serves both routes via a `mode` prop set in the router —
routes, paths, and names unchanged, so no navigation call sites moved.
mode='create': localStorage persistence, Clear Stored Data button, simple-
format hint, saveJsonFile. mode='edit': loads from route.query.file via
experimentService (validateData-normalized), tracks originalFileName,
updateJsonFile. Both keep their own root/h2 classes -> pixel-identical.
Small unifications (both modes now get the better variant): deep-copy
updateQuestions, detailed save-error messages, leave-warning dialog.

## SMOKE BEFORE COMMITTING (5 min)
Create: open blank -> restore from localStorage works -> import both PARHAF
formats -> generate facts -> save -> Clear Stored Data visible.
Edit: open a set from Home -> answers show -> rename -> Save Changes ->
old file replaced (no double suffix) -> success dialog says "modified".
Both: leave-warning dialog on unsaved changes; proceed-to-experiment.
