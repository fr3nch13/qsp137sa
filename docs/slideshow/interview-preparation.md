# Slideshow and Interview Preparation

Working tracker for the assignment presentation, supporting evidence, panel questions, and live interview. This is preparation material, not the final PowerPoint/PDF deck. Update implementation claims and evidence before presenting.

Source: [assignment brief](../Quantum_Sky_Project_137_Software%20Engineering%20Assignment.md). See also the author's [decision notes](../descision-notes.md), [project context](../../.github/project-context.md), and [implementation tasks](../../.github/tasks/todo.md).

## Submission and meeting checklist

- [ ] Deliver a repository link the panel can read, or a zip, with full Git history; do not squash away the history.
- [ ] Include AI instructions and any edited AI-generated plans/specifications.
- [ ] Verify the README startup command and linked production limitations match the delivered application.
- [ ] Produce a PowerPoint or PDF deck of about 10 slides.
- [ ] Rehearse a roughly 15-minute presentation, including a short live demo.
- [ ] Prepare for roughly 25 minutes of questions about the deck and Git history.
- [ ] Reserve roughly 15 minutes for a small change made live with the usual tools.
- [ ] Prepare questions for the remaining time in the 60-minute meeting.
- [ ] Confirm only public data and open-source tools are used; no employer material or credentials are included.
- [ ] Record actual time spent; do not infer it from commit timestamps.

## Proposed slide coverage

Audience: an operations lead and engineers. Explain operational results first, then the engineering evidence. The assignment allows any order.

| Slide | Assignment topic | Content and evidence to prepare | Status |
|---|---|---|---|
| 1 | Goal and scope | Team's three questions, delivered capabilities, and demonstration boundaries. | Scaffold only |
| 2 | Findings: single points of failure | Critical nodes/links with numbers and the reason each is critical. | Analysis pending |
| 3 | Findings: traffic dependence and outages | Five most utilized links, one node/link outage, undeliverable demands, failed endpoints, and overloads; include live fail/restore demo. | Analysis/UI pending |
| 4 | Structure and design | Code organization, merged model, transit restrictions, and equal splitting across minimum-hop paths. Explain why. | Model/routing pending |
| 5 | Interface and decision ownership | Backend/frontend contract, TypeScript UI, and decisions made by the author versus accepted from AI. | Contract/UI pending |
| 6 | Setting up AI | Instructions provided before coding; demonstrate actual tests, linters, type checks, and hooks, distinguishing implemented checks from proposals. | Instructions, lint and tests available; inventory remaining checks |
| 7 | Verification | Independently justified expected values, tests specified/written by the author, and evidence beyond AI assertions. | Infrastructure tests available; analysis verification pending |
| 8 | Production concerns | All six concerns below: implemented/deferred, why, and first internal-release steps. | Track below |
| 9 | Steering and ambiguity | Three to five concrete interventions; unclear requirements, questions asked, and how resolved. | Candidates below; author to confirm |
| 10 | Delivery and time | Actual time spent, remaining limitations, next steps, and close for questions. | Time record pending |

## Implementation status and production concerns

Current functionality is limited to starting the server, viewing a status page, and observing startup/request logs. The application is local-only and unauthenticated.

Dataset loading and validation, the merged model, routing, criticality analysis, utilization rankings, map, and interactive failure/restore controls are not implemented. There are no application-generated network findings yet.

The expected merged baseline is **37 nodes, 55 links, and 391 demands totaling 2,068 units**. These are assignment acceptance targets, not measured outputs from the current application. Verification must also cover backbone capacity 550, undirected demands, endpoint/transit restrictions, equal shortest-path splitting, and failure reporting.

| Concern | Implemented now | Why incomplete/deferred | First internal-release work |
|---|---|---|---|
| Authentication and access control | No authentication; local host restrictions and loopback-only demonstration. | Account-management scope deferred for the local demonstration. | Add authentication, protected endpoints, least-privilege authorization, and access-control tests before shared use. |
| Logging | Basic server/request stdout/stderr logs; development log file. | Centralized observability deferred; basic diagnostics retained. | Define redaction, collection, retention, operational alerts, and appropriate audit events. |
| Input validation and error handling | Required dataset validation and file-and-row errors are not implemented. | Loader unfinished; this is priority work, not an optional production enhancement. | Validate both inputs and requests explicitly; test invalid rows and baseline invariants without exposing tracebacks. |
| API versioning | No analysis API or compatibility policy yet. | One jointly delivered frontend/backend; no independent clients. | Define the contract; establish versioning/deprecation policy before supporting independent clients. |
| Configuration and secrets | Runtime secret key required; local allowed hosts; private configuration excluded from images. Demo key is public and not suitable for shared use. | Deployment provisioning and managed secrets deferred. | Private random keys, approved secret delivery and rotation, HTTPS, deployment-specific host/cookie settings. |
| Dependency and security checks | Locked dependencies, lint, unit tests, container smoke tests, and HTTP checks. | Automated vulnerability and image scanning not implemented. | Add dependency/container scans, triage findings, and establish dependency/base-image update ownership. |

Passing scaffold CI does not prove network-analysis correctness or production readiness.

## Container architecture decision

Decision recorded on 2026-10-24: retain the published Linux AMD64 image and explicitly select `linux/amd64` in Compose and the README's Docker run command, rather than adding multi-platform publishing.

- **Why:** Keep build, test, and publishing complexity proportionate to the small assignment. AMD64 Linux hosts run the image natively; the author's Apple Silicon Mac can use Docker Desktop's AMD64 emulation for the local demonstration. No ARM64 production requirement has been established.
- **What prompted it:** Compose showed a platform-mismatch warning on the ARM64 Mac. It was not a startup failure: the user supplied output showing the container remained up and Gunicorn successfully started. Docker run and Compose use the same Docker engine and emulation support; explicitly selecting the platform declares the intended architecture rather than adding emulation.
- **Trade-off:** ARM64 execution requires emulation support and can be slower. This is not evidence of native ARM64 compatibility or production performance. Linux ARM64 servers need emulation configured separately; the Compose setting alone does not provide it.
- **When to revisit:** If native ARM64 deployment or measured performance requirements justify it, build and test both architectures and publish them under one multi-platform tag.
- **Evidence boundary:** Local configuration validation and the user's startup logs support this decision. HTTP readiness, full application functionality, and production suitability must be verified separately.

## Future / proposed changes

These are proposals for evaluation, not implemented capabilities or additions to the initial assignment scope.

- **Authentication and perimeter protection:** Confirm the intended users and deployment exposure. Add authentication and authorization if shared access requires them; evaluate a Web Application Firewall (WAF), request rate limits, and denial-of-service (DoS/DDoS) protection if justified by the hosting environment and project scope. Rate limiting can reduce abusive requests and expensive analysis workloads; volumetric DDoS protection generally requires upstream hosting/CDN support. These controls supplement application protection but do not replace authentication or authorization.
- **More granular CI execution:** Avoid unnecessary image rebuilds and publication for documentation-only changes, such as `.github/*.md`. Keep lightweight checks where appropriate, and build/test images when application, dependency, container, or relevant CI inputs change. Preserve release-tag builds and ensure the required `test` check still reports a result for documentation-only PRs rather than leaving branch protection waiting on a skipped workflow.

## Steering examples to substantiate

Confirm these against conversation history and commits before presenting. For each, show what AI proposed, what the author changed, why, and the resulting evidence.

| Candidate | AI output or initial behavior | Author direction and rationale | Evidence to collect |
|---|---|---|---|
| Container complexity | Proposed more stages than needed. | Reduce to base, development, and production; keep scope small. | Decision notes and Dockerfile history |
| Home-directory layout | Workspace also used as the app user's home. | Separate persistent home from source workspace to avoid tool-state clutter. | Container configuration and migration history |
| CI cost and branching | Included CI on pushes to dev. | Main pushes, PRs, and release tags only; skip fork runners to control budget. | Workflow changes and successful runs |
| Release naming | Broad tag trigger. | Restrict releases to SemVer, with strict validation before builds. | Tag helper tests and workflow history |
| Documentation audience | README included detailed implementation/production tracking. | Move interview detail here; keep README focused on use and link limitations. | Documentation diff |

Do not attribute AI-written tests or decisions to the author without confirmation.

## Questions, ambiguities, and answers

### Assignment questions and unresolved inputs

| Question / issue | Current answer or evidence | Status / next action |
|---|---|---|
| Where are single points of failure? | No analysis results yet. | Implement and verify numerical findings. |
| Which links does traffic depend on most? | No utilization results yet. | Calculate and independently verify top five. |
| What happens when a link or site fails? | No simulation results yet. | Verify undeliverable, failed-endpoint, and overload reports. |
| How should unavailable official SNDlib inputs be obtained? | Original endpoints failed; a third-party mirror was identified provisionally. | Author plans to contact Quantum Sky; official provenance and permitted use remain unresolved. Do not claim clarification received. |

### Practice questions (not questions already asked by the panel)

- Why Django and TopoHub, and what extra validation/adaptation is needed?
- How do tests prove equal splitting and prevent endpoint nodes from forwarding transit traffic?
- Where did expected values come from, and which were independently calculated?
- What does green CI prove, and what does it not prove?
- Which decisions did the author make, and which AI suggestions were accepted or rejected?
- What would change before admitting internal users or deploying outside localhost?

### Questions to ask the panel

- Confirm the approved backbone source if official downloads remain unavailable.
- Clarify intended first internal-release users and deployment/access boundaries.
- Ask which operational workflows or failure cases they would prioritize next.

### Meeting question log

Record actual questions separately from preparation prompts.

| Asked by / date | Question | Answer or decision | Follow-up |
|---|---|---|---|
| Pending meeting | No panel questions recorded yet. | Pending | Pending |

## Demo and live-change preparation

- [ ] Confirm the panel has repository/package access and the documented command works on the demonstration machine.
- [ ] Prepare a short script showing only implemented behavior; do not present the status page as a completed network tool.
- [ ] Once implemented, rehearse the baseline, critical indicators without color alone, top-five links, and fail/restore without reload.
- [ ] Keep expected numerical results and their verification evidence accessible.
- [ ] Verify the editor, AI sign-in, dependencies, and targeted tests before the live-change segment.
- [ ] Have a local image available and screenshots/results as a fallback; describe any fallback honestly.
- [ ] Be ready to explain meaningful code and navigate the full Git history.

## Time record

Record actual effort and explain any missing tracking honestly.

| Activity | Time spent | Notes / evidence |
|---|---|---|
| Research and design | Not recorded yet | Author to supply |
| AI setup and steering | Not recorded yet | Author to supply |
| Implementation and infrastructure | Not recorded yet | Author to supply |
| Verification and corrections | Not recorded yet | Author to supply |
| Slides and rehearsal | Not recorded yet | Author to supply |
