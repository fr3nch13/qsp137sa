---
title: Code review - M2 same-origin serving
date: 2026-10-27 04:59
verdict: Approve with minor fixes
scope: Uncommitted changes for M2 same-origin Django serving and frontend/API proof
status: addressed
---

## Summary

The changes serve the built frontend and static assets through Django and implement a same-origin JSON greeting API consumed by the React homepage. The review found one medium-severity mismatch in the API's unsupported-method response: CSRF middleware can reject a POST before the view returns its documented JSON 405. Other reviewed M2 behavior is covered by the reported passing Django and frontend tests.

## Findings

### F1 - Medium - linkscope/views.py:28
- Problem: The view intends to return a JSON 405 for unsupported methods, but `CsrfViewMiddleware` runs before the view and rejects a browser POST without a CSRF token first.
- Why it matters: Such a request returns Django's HTML 403 rather than the API's JSON 405 contract. The current test client does not expose this because CSRF checks are disabled by default.
- Fix: Decide whether unsupported methods should return the API's JSON 405 or a CSRF 403. If the JSON 405 is the contract, ensure this read-only endpoint reaches its method check and test it with `Client(enforce_csrf_checks=True)`.

## Gaps and edge cases

None beyond F1.

## Action checklist for the implementing agent

- [x] F1: Define and test the response for an unsupported API method when CSRF checks are enabled.

## What looks good

- The React app uses the relative API path and handles loading, HTTP/network failures, and invalid responses explicitly.
- Django tests cover the serving, content-type, cache, missing-resource, and API response behaviors relevant to this milestone.

## Questions for the author

Resolved: retain the view's JSON 405 contract for this strictly read-only endpoint. Other views retain CSRF protection.

## Suggested tests

- Add a test using `Client(enforce_csrf_checks=True)` for `POST /api`; assert the chosen status, content type, and response body.

## Remediated Actions Taken

- **F1 addressed:** Applied `csrf_exempt` only to the greeting endpoint so unsupported methods reach its explicit rejection before any work is performed. GET/HEAD remain the only allowed methods. This exemption must not be carried forward to state-changing functionality.
- Added `Client(enforce_csrf_checks=True)` coverage for POST, PUT, PATCH, DELETE, and OPTIONS on both `/api` and `/api/`, asserting HTTP 405, JSON content type/body, `Allow: GET, HEAD`, and no-store caching.
- Added a regression test confirming CSRF middleware still rejects an unprotected POST to the homepage with HTTP 403.
- **Validation:** All 11 Django tests passed; focused Ruff lint/format and whitespace checks passed. This remediation does not constitute Docker/Compose verification.
