---
title: Code review - M6f interactive fail and restore
date: 2026-10-27 08:39
verdict: Approve with minor fixes
scope: M6f frontend interactive failure/restore controls, analysis presentation, map updates, tests, and related documentation
status: partially-addressed
---

## Summary

M6f adds accessible node/link selection, request-local failure simulations, restoration to the baseline, and presentation of R8 results without a page reload. The code guards against stale responses through request cancellation and validates returned failure analyses; the frontend test, lint, type-check, and build commands pass. No functional or security defect was confirmed, but whitespace validation fails and the published-image acceptance check remains open.

## Findings

### F1 - Low - README.md:48
- Problem: The newly added paragraph ends in trailing whitespace.
- Why it matters: `git diff --check` fails, preventing the change from passing the repository's whitespace validation.
- Fix: Remove the trailing space at the end of the paragraph.

## Gaps and edge cases

### G1 - frontend/tests/NetworkWorkspace.test.tsx:6
- Gap: The component tests render static markup, and the controls tests also use static markup. They do not automatically exercise the fail/restore event flow, abort handling, or delayed-response race behavior described in the M6f verification notes.
- Risk if it happens: A later change could reintroduce a stale result overwriting a newer failure or a restore while the existing presentation tests still pass. The documented manual browser checks reduce current risk but do not protect against regressions.
- Confidence: confirmed

### G2 - .github/tasks/todo.md:158
- Gap: The documented Compose proof using the published image is still unchecked; only a locally built production image was verified.
- Risk if it happens: The current published image may not contain the M6f frontend or may behave differently from the locally built image, so the one-command user delivery path is not yet demonstrated.
- Confidence: confirmed

## Action checklist for the implementing agent

- [x] F1: Remove the trailing whitespace and rerun `git diff --check`.
- [ ] G1: Consider adding component-level tests for fail, restore, request errors, and delayed responses that ignore abort.
- [ ] G2: After publishing the frontend image, run the documented Compose startup proof and record its actual result.

## What looks good

- Node and link selection use native labeled controls and include all elements; the UI presents the selected scenario and baseline criticality as distinct concepts.
- Failure responses are checked against the selected scenario and baseline topology before being used; analysis errors keep prior results visible and actionable.
- Restore aborts pending requests and immediately restores the baseline without reloading.
- Failed-node endpoint demands, other undeliverable demands, and all overloaded links are presented separately, with expandable demand details.
- Map overlay updates preserve the existing Leaflet instance, allowing the basemap pan/zoom state to remain in place.
- The frontend test suite (16 tests), lint, type-check, and production build passed during review.

## Questions for the author

None.

## Suggested tests

- Add an interaction test that starts failure A, starts failure B before A resolves, resolves A last, and asserts only B is displayed.
- Add an interaction test that restores while a failure request is pending and asserts a late response cannot leave the page in the failed state.
- Add an interaction test for failed analysis followed by a successful retry or restore.

## Remediated Actions Taken

Implementation follow-up:

- **F1 addressed:** Removed the trailing whitespace in `README.md`; `git diff --check` passes.
- **G1 considered; deferred:** The existing Node/static-markup suite does not mount React in a browser/DOM environment. Fail/restore, HTTP error recovery, and delayed responses ignoring abort were exercised through the real browser, but those checks are not repeatable automated regression tests. Retain this explicit gap rather than equating static-markup tests with interaction coverage. A DOM/browser test harness is deferred to keep the initial assignment scope small and avoid introducing unrequested test dependencies.
- **G2 open:** The locally built production image was verified through Compose and the browser. The frontend is not published yet; repeat the documented published-image startup after publication before marking this acceptance item complete.
