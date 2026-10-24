# LinkScope — Project Context

This document describes the software product and its functional requirements. The original assignment, including presentation and submission expectations, is retained in [the assignment brief](../docs/Quantum_Sky_Project_137_Software%20Engineering%20Assignment.md).

LinkScope is an application within Project 137, a division of Quantum Sky.

## Product Goal

Build a small network-operations application that helps a team understand a European backbone and its connected operations sites and data centers. The application must answer:

1. Where are the network's single points of failure?
2. Which links carry the most traffic?
3. What happens to traffic when a node or link fails?

## Input Data and Network Model

The application combines two inputs:

1. **Backbone:** The public `nobel-eu` network from the [Survivable Network Design Library (SNDlib)](https://sndlib.put.poznan.pl/), available as [XML](https://sndlib.put.poznan.pl/download/sndlib-networks-xml/nobel-eu.xml) or [native text](https://sndlib.put.poznan.pl/download/sndlib-networks-native/nobel-eu.txt). It contains 28 European city nodes with coordinates, 41 links, and 378 traffic demands. Cite SNDlib in the user-facing README.
2. **Sites:** The site table and attachment data in the [assignment brief](../docs/Quantum_Sky_Project_137_Software%20Engineering%20Assignment.md). Each row adds a site node. Its `attaches_to` field contains one or more semicolon-separated node IDs; each attachment creates an access link with the row's `access_capacity`.

The merged baseline is expected to contain **37 nodes, 55 links, and 391 demands totaling 2,068 units**. Treat these values as input/model verification invariants.

### Site inventory

| Site | Type | Attaches to | Access capacity |
|---|---|---|---:|
| DC-NORTH | data center | Hamburg; Copenhagen | 200 |
| DC-SOUTH | data center | Milan; Zurich | 200 |
| OPS-WEST | operations site | Dublin | 40 |
| OPS-CENTRAL | operations site | Paris; Brussels | 40 |
| OPS-SOUTHEAST | operations site | Athens | 40 |
| HUB-EAST | aggregation hub | Warsaw | 80 |
| OPS-EAST-1 | operations site | HUB-EAST | 40 |
| OPS-EAST-2 | operations site | HUB-EAST; Budapest | 40 |
| OPS-IBERIA | operations site | Madrid; Barcelona | 40 |

### Data semantics

- All links and demands are undirected.
- Assign a capacity of 550 units to every backbone link; ignore the capacity modules supplied in the backbone input.
- Add 10 units of demand from each of the six operations sites to each of the two data centers.
- Add a 50-unit demand between the two data centers.
- Reject malformed or inconsistent input with an explicit error identifying the input file and row.

## Routing and Failure Analysis

- Route every demand along all paths having the minimum number of hops. Split demand equally among tied shortest paths.
- Operations sites and data centers are endpoints, not transit nodes. Only backbone cities and the aggregation hub may forward traffic.
- A node or link is **critical** if its loss causes any of the following:
  - The network becomes disconnected.
  - Any demand cannot be delivered.
  - Any remaining link exceeds 100% utilization.
- For a simulated single-node or single-link failure, report:
  - Demands that can no longer be delivered.
  - Demands that start or end at a failed node, separately from other undeliverable demands.
  - Every remaining link whose utilization exceeds 100%.
- Users must be able to fail and restore any node or link and see the updated failure analysis without reloading the page.

## User Interface

- Display the network as a map based on the backbone city coordinates.
- Place each site near the node or nodes to which it attaches.
- Make critical nodes and links and the five most utilized links visible.
- Do not communicate criticality or utilization using color alone; provide another visual cue or textual indicator.
- Support interactive failure and restoration of nodes and links, with results shown in the current page.

## Technology and Runtime Constraints

- Backend: Python or Go.
- Frontend: TypeScript; React is optional.
- Libraries may be used as appropriate.
- No database is required.
- Provide one documented command to start the application.

## Scope Boundaries

The deliverable is a first, small working network-analysis application. Keep implementation choices (including framework, internal architecture, and algorithms beyond the specified behavior) aligned with the requirements and avoid adding unrequested product scope. Assignment-specific presentation, AI workflow, repository submission, and follow-up session expectations are documented in the [assignment brief](../docs/Quantum_Sky_Project_137_Software%20Engineering%20Assignment.md).

## Repository Scope and README

Outside `./docs/` and `./.github/`, all project files—including the root `README.md`—are part of the production-level application scope. Treat application code and user-facing materials as production-quality deliverables, not scratch work or assignment-only artifacts.

The README is for end users. Keep it focused on the product overview, implemented capabilities, and supported user-facing options. Describe options at a high level; do not put internal architecture, source file paths, environment variable names, development commands, or CI/CD implementation details there. Be accurate about what is and is not available, and document how to use the application once it is runnable. Keep development setup, architecture, exact configuration, validation commands, and release mechanics in `.github/project-context.md` and `.github/tasks/*.md`.

## Known Issues

Verified on 2026-10-23:

- **SNDlib download links return 404.** GET requests to both the [nobel-eu XML URL](https://sndlib.put.poznan.pl/download/sndlib-networks-xml/nobel-eu.xml) and [nobel-eu native-text URL](https://sndlib.put.poznan.pl/download/sndlib-networks-native/nobel-eu.txt) returned HTTP 404. The same paths on `ventus.put.poznan.pl` also returned HTTP 404. These checks do not establish whether the missing files are intentional.
- **SNDlib hostname certificate mismatch.** The TLS certificate served for `sndlib.put.poznan.pl` has `ventus.put.poznan.pl` as its Common Name and its only Subject Alternative Name. Hostname verification therefore fails for `sndlib.put.poznan.pl`; the HTTP 404 responses above were obtained only with certificate verification disabled for diagnosis. Whether the mismatch is intentional is unknown.
- Candidate mirrors and the follow-up validation work are documented in [the dataset resource-gathering task](tasks/todo.md#gather-and-validate-the-nobel-eu-dataset-source).
