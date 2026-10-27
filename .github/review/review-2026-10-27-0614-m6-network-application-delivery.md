---
title: Code review - M6 network application delivery
date: 2026-10-27 06:14
verdict: Approve with minor fixes
scope: M6a-M6c changes for topology loading, routing, failure analysis, tests, and related project documentation
status: partially-addressed
---

## Summary

M6a-M6c implement the required local topology merge, minimum-hop equal-path routing, and single-node/link failure analysis. The reviewed implementation is deterministic, preserves the input topology, and reports failed-node endpoint demands separately from other undeliverable demands. Focused tests and Ruff checks pass; the provisional dataset source still needs provenance and permitted-use confirmation, and the real-network headline results could be protected with stronger regression assertions.

## Findings

No confirmed correctness, security, or reliability defects found in the reviewed M6a-M6c implementation.

## Gaps and edge cases

### G1 - data/README.md:17
- Gap: The backbone snapshot comes from a third-party mirror whose official provenance and permitted use are not confirmed.
- Risk if it happens: The application may ship with data whose source or reuse terms have not been established, despite the assignment requiring public data and attribution.
- Confidence: confirmed

### G2 - linkscope/test_routing.py:132; linkscope/test_failures.py:149
- Gap: Real-network tests verify reproducibility and selected invariants, but do not assert the recorded top-five utilization values or the reported critical-node/link totals.
- Risk if it happens: A deterministic regression in the real-network analysis could change the findings while these integration checks still pass.
- Confidence: worth checking

The JSON API and map/interactive UI requirements (R9-R11) are not implemented in M6a-M6c; they are explicitly assigned to M6d-M6f and are outside this review's implementation scope.

## Action checklist for the implementing agent

- [ ] G1: Confirm the backbone snapshot's provenance and permitted use before final delivery.
- [x] G2: Assert independently verified baseline top-five values and real-network criticality identities in regression tests.

## What looks good

- Input validation reports file and row details, and the loader keeps the backbone and site files unchanged.
- Routing splits traffic across complete equal-hop paths rather than approximating equal shares across first hops.
- Failure simulation uses immutable topology records, evaluates all 92 failures deterministically, and has focused tests for endpoint loss, physical disconnection, legal-route loss, overload boundaries, and restoration.
- The recorded real-network criticality counts were independently reproduced during review: 37 critical nodes and six critical links.

## Questions for the author

- Has the project owner confirmed the mirror's provenance and permitted use? The repository currently records this as unresolved.

## Suggested tests

- Add reference assertions for the baseline top-five links/utilization and the number or identities of critical nodes and links, using values verified independently of the implementation.

## Remediated Actions Taken

- **G2 addressed:** The real-network routing test now asserts ordered top-five link IDs, loads, and utilization percentages (absolute tolerance `0.000001` for rounded reference values). A separate reference calculation enumerated all simple paths bounded by the BFS minimum-hop count, without calling `route_traffic()`, and reproduced all five recorded values. Existing hand-calculated synthetic cases remain the primary independent correctness checks.
- **G2 addressed:** The all-failures test now asserts the complete set of 37 critical node IDs and the exact six critical link IDs, protecting the counts independently reproduced during this review.
- **G1 remains open:** The source revision, checksum, attribution, and provisional status are recorded in `data/README.md`. These do not establish provenance or reuse permission. Confirmation remains required before final delivery; no licensing claim was inferred or fabricated.
