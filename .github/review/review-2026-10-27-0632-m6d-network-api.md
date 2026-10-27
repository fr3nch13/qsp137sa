---
title: Code review - M6d network API
date: 2026-10-27 06:32
verdict: Approve with minor fixes
scope: M6d Django network/analysis API, tests, routes, image smoke checks, and related documentation
status: addressed
---

## Summary

M6d adds read-only topology and analysis endpoints, with request-local failure simulations and explicit handling for invalid queries, input errors, and NetworkX failures. The response contents match the M6d acceptance needs, and tests cover baseline data, selected failures, restore/isolation, invalid requests, and error responses. No runtime correctness or security defects were found; the declared typed JSON contract does not cover the complete topology response.

## Findings

### F1 - Low - linkscope/network_api.py:16
- Problem: The declared `TypedDict` contract covers demands, loads, and analysis, but not node/link records, criticality entries, or the top-level network response. Those parts of `/api/network` are assembled as untyped dictionaries.
- Why it matters: The API is intended to be the frontend integration contract; the missing types leave key field names and shapes without static checking, making contract drift easier during M6e.
- Fix: Add `TypedDict` definitions for node, link, criticality, and network responses, and annotate the payload construction (including a more specific type for the failure descriptor).

## Gaps and edge cases

### G1 - .github/ci/test-images.sh:58
- Gap: The updated smoke checks for the new endpoints were not executed against built Docker images during this review; only shell syntax and whitespace were checked locally.
- Risk if it happens: A packaging or production-image issue could prevent `/api/network` or `/api/analysis` from working even though Django's in-process tests pass.
- Confidence: confirmed

## Action checklist for the implementing agent

- [x] F1: Complete the static response types for the full `/api/network` contract.
- [x] G1: Confirm the updated smoke checks pass against both development and production images in CI or on a Docker host.

## What looks good

- The API validates unknown, partial, repeated, and disallowed query parameters before loading the topology.
- Simulations do not persist state; baseline requests restore the unfailed topology for the same or another client.
- Read-only methods are explicitly limited to GET and HEAD, with unsafe methods rejected before analysis and an appropriate `Allow` header.
- Input and NetworkX failures return JSON errors with server-side logging, while unknown element IDs return 404.
- Focused API tests, all 45 backend tests, Ruff lint/format checks, shell syntax validation, and `git diff --check` passed.

## Questions for the author

None.

## Suggested tests

- Add static type coverage for the full network response shapes; no additional runtime test is needed for F1.
- Keep the new image endpoint smoke checks in the hosted CI validation for both image targets.

## Remediated Actions Taken

- **F1 addressed:** Added `NodeJSON`, `LinkJSON`, `FailureJSON`, `CriticalityJSON`, and `NetworkJSON`. Failure kinds use `Literal["node", "link"]`; load and criticality types extend their shared record types. The complete network payload and criticality list are annotated, and explicit field construction replaces untyped dataclass serialization. JSON field names and runtime behavior are unchanged.
- **G1 addressed (2026-10-27):** After the user enabled host Docker access, both targets were built explicitly for Linux AMD64 and the complete image smoke script exited successfully. HTTP checks verified frontend/assets, greeting, real topology (37/55/391), criticality (43 critical elements), and L12 failure overloading L26 through both development Django and production Gunicorn. Tests used separate laptop loopback ports 22158/22159 and the host workspace bind source; the existing devcontainer/port 2158 was left running. Test containers were removed by the cleanup trap. The script now supports host-workspace/address/port overrides while preserving CI defaults and explicitly selects AMD64.
