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

Current functionality includes a React homepage displaying a greeting fetched from the Django JSON API, loading/error states, and startup/request logs. The application is local-only and unauthenticated.

Dataset loading/validation and the merged model are implemented in M6a; baseline routing and utilization rankings in M6b; single failures and criticality in M6c. The map and interactive failure/restore controls remain unimplemented. Results below are backend measurements, not features exposed by the current greeting API/UI.

Delivery-plan correction: the core application was previously compressed into three M6 checklist items despite covering R1-R11. It is now split into M6a-M6f with independent acceptance gates for data, routing, failure analysis, API, map, and interactive delivery. Prioritize these over optional infrastructure; derive presentation findings from measured application results and hand-checked test expectations, not scaffold CI.

M2 now serves React at `/`, greeting JSON at `/api`, and static assets through WhiteNoise with debug disabled. The responsive header/footer share the dark slate palette, with one `logo.svg` used in the header and as the favicon; the main workspace remains open for later functionality. Eight frontend tests, 11 Django tests, 31 CI-helper tests, lint, type checks, and builds passed locally at M2. Browser verification confirmed the same-origin greeting, visible HTTP/network/invalid-response errors, recovery, logo loading, and desktop/mobile layout without horizontal overflow. Review F1's unsupported-method/CSRF mismatch is addressed, with CSRF-enforced regression coverage. The Gunicorn entry point separately served HTML/JS/CSS/JSON successfully. CI Docker builds and HTTP smoke checks subsequently passed; production-image Compose/browser verification remains pending.

The loader now measures **37 nodes, 55 links, and 391 demands totaling 2,068 units**, matching the assignment acceptance targets. Eight loader tests verify real-input totals, checksum and unchanged separate source files, generated demands, backbone capacity 550, endpoint/transit roles, CSV row-order independence, and file/row validation errors. A small synthetic merge has independently calculated expectations (6 nodes, 5 links, 4 demands, 77 units). All 19 backend tests and Ruff checks/format passed at M6a. The local snapshot's provenance/permitted-use confirmation remains open; metadata is recorded under `data/`.

M6b adds eight routing tests, for 27 passing backend tests at that stage. Hand-calculated examples verify equal complete-path splitting (including unequal downstream path counts and fractional shares), endpoint/transit restrictions, undirected loads, conservation, and unreachable reporting. The real baseline has no undeliverable demands; reversing record order produces identical results.

Measured baseline top five (values rounded for presentation; capacities are 550 units):

| Link | Endpoints | Load units | Utilization |
|---|---|---:|---:|
| L12 | Berlin–Hamburg | 390.546867 | 71.008521% |
| L3 | Amsterdam–Hamburg | 376.225021 | 68.404549% |
| L26 | Frankfurt–Munich | 341.693484 | 62.126088% |
| L30 | Milan–Munich | 323.482456 | 58.814992% |
| L13 | Berlin–Munich | 278.462531 | 50.629551% |

M6c evaluates all **92 single failures** and reports **37 critical nodes and six critical links**. Under R7's “any demand undeliverable” definition, losing a node's own endpoint demands counts toward criticality; this does not mean every node is a physical articulation point. Failed-endpoint demands are reported separately from other unreachable demands, as required by R8. Only surviving nodes count when checking physical disconnection.

| Failed link | Reason and measured effect |
|---|---|
| L12 Berlin–Hamburg | Rerouting overloads L26 Frankfurt–Munich: 705.624242 / 550 units, 128.295317%. |
| L26 Frankfurt–Munich | Rerouting overloads L12 Berlin–Hamburg: 617.973626 / 550 units, 112.358841%. |
| HUB-EAST–Warsaw | 20 units undeliverable. Physical connectivity remains via OPS-EAST-2, but an operations site cannot carry transit traffic. |
| OPS-EAST-1–HUB-EAST | Disconnection and 20 units undeliverable. |
| OPS-SOUTHEAST–Athens | Disconnection and 20 units undeliverable. |
| OPS-WEST–Dublin | Disconnection and 20 units undeliverable. |

Representative node failures: losing HUB-EAST disconnects OPS-EAST-1 and leaves 20 units undeliverable (the hub has no endpoint demand). Losing Hamburg separates 162 units of failed-endpoint demand, with no other undeliverable demand, and overloads L26 to 117.057222%.

Twelve M6c tests bring the backend suite to **39 passing tests**, with Ruff lint/format passing. Independent small networks verify demand separation, disconnection without demands, legal-route loss in a connected graph, 12-unit rerouting onto 10-unit links, exactly-100% versus greater-than-100% overload, multiple criticality reasons, invalid IDs, and restoration without mutation. Real-network checks evaluate every node/link twice for reproducibility. These are local backend findings; they are not yet API/UI or published-image application proof.

M3 workspace verification on 2026-10-27 demonstrated frontend edits through both an explicit build and watch mode, followed by ordinary browser refresh on port 2158 without an image push or second frontend server. Intentional syntax errors produced clear build/watch diagnostics, and the watcher recovered after correction. Repeated post-start hooks preserved the working greeting API. All nine frontend and 11 Django tests passed, including new logo-watch and build-error/recovery coverage. Temporary edits were restored. Fresh devcontainer creation and actual container restart remain unverified here because Docker is unavailable; dependencies were not reinstalled.

M4/M5 evidence review on 2026-10-27: Actions run 40455416000 passed both image builds, the complete container/HTTP smoke checks, and production-image export/upload. This verifies non-root production permissions, runtime-key startup, generated frontend assets, and absence of Node/npm in the production runtime. A separate local Gunicorn browser check displayed the fetched greeting; the temporary process was stopped. This is not a production-image browser check. Publication failed at `download-artifact@v8.0.2` because its bundled ZIP extractor still emits `DEP0005`; the Node-warning guard correctly failed the action. The version pin did not fix it, and no warning bypass or custom extractor was added. All 32 CI-helper tests passed locally. Published-image Compose/browser checks remain pending on a Docker host, so M4's final browser gate and M5 are not complete.

Subsequent user decision: remove the fatal third-party Node-warning guard to keep warnings visible without blocking jobs. Both workflows now use default Node warning logging; actual action failures and frontend checked-command validation remain enforced. The guard-specific test was removed. Hosted publication after this change remains unverified.

User verification follow-up (2026-10-27): the user confirmed the remaining M4/M5 checks by running `docker compose up -d` from their laptop terminal and marked the published-image/browser acceptance items complete. This supersedes the earlier pending Compose/browser limitations. The selected image tag/digest was not recorded, and this does not verify a new hosted publication after the warning-policy change.

| Concern | Implemented now | Why incomplete/deferred | First internal-release work |
|---|---|---|---|
| Authentication and access control | No authentication; local host restrictions and loopback-only demonstration. | Account-management scope deferred for the local demonstration. | Add authentication, protected endpoints, least-privilege authorization, and access-control tests before shared use. |
| Logging | Basic server/request stdout/stderr logs; development log file. | Centralized observability deferred; basic diagnostics retained. | Define redaction, collection, retention, operational alerts, and appropriate audit events. |
| Input validation and error handling | Local backbone/CSV validation with file-and-row errors and tested merged invariants is implemented. | Analysis API request validation and presentation of loader errors remain pending. | Retain invalid-input tests; validate analysis requests and expose useful errors without tracebacks. |
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

## Bundled frontend and API rationale

Decision clarified on 2026-10-27; M1 build tooling and M2 bundled serving are implemented locally, while the updated production image still needs Docker/Compose verification. Keep React/TypeScript and Django in one shipped image, one repository, and one Dockerfile. Gunicorn with Django routing and WhiteNoise serves React at `/` and the REST API under `/api` on the same origin at port 2158. Retain the API contract without a separate frontend deployment, proxy, or CORS configuration.

The Node build stage produces static frontend assets; the browser executes the JavaScript. Node/npm will also be available in the devcontainer for builds and build-watch, followed by manual browser refresh. Do not add Vite or another frontend server/HMR. Commit source, lockfiles, and build configuration, not generated bundles or `node_modules`. Production receives the compiled assets without the Node runtime.

**Why:** Keep startup, release coordination, and the local demo small. The cost is coupled frontend/backend releases and a whole-image rebuild for frontend-only edits. A separate static-file serving mechanism must be wired into Django/Gunicorn; Gunicorn alone is not sufficient. Verification must cover both workspace rebuilds and a clean source-only production build.

**Evolution path:** If independent releases or scaling justify it, use separate frontend and backend images in the same project/Compose file, with separate Dockerfiles/build contexts and per-image CI filtering. A further split into frontend/backend repositories and a third IaC/orchestration repository can support independent teams and environment promotion, at the cost of cross-repository API compatibility and release coordination. None of these splits is current implementation scope.

## Future / proposed changes

These are proposals for evaluation, not implemented capabilities or additions to the initial assignment scope.

- **Docker Compose rationale and future devcontainer integration:** Compose provides repeatable startup configuration today and a straightforward way to define companion services later. These extension points are reasons for choosing Compose, not commitments to add services:
  - Wire Compose into the devcontainer in the future while retaining development-specific tooling, workspace mounts, lifecycle hooks, and separation from production configuration.
  - Allow an optional Model Context Protocol (MCP) sidecar for development and production if needed, with environment-appropriate access controls, credentials, and network exposure.
  - Allow Memcached or another caching sidecar and a database sidecar if future requirements justify them, with appropriate cache invalidation, persistence, backups, and service readiness.
  - The current setup remains single-service; Compose alone does not establish production readiness.
- **Authentication and perimeter protection:** Confirm the intended users and deployment exposure. Add authentication and authorization if shared access requires them; evaluate a Web Application Firewall (WAF), request rate limits, and denial-of-service (DoS/DDoS) protection if justified by the hosting environment and project scope. Rate limiting can reduce abusive requests and expensive analysis workloads; volumetric DDoS protection generally requires upstream hosting/CDN support. These controls supplement application protection but do not replace authentication or authorization.
- **Per-image CI filtering after a service split:** Consider granular CI only with the future separate frontend/backend images described above, so each image builds when its inputs change. Keep the current bundled-image pipeline unfiltered. Any later filtering must cover shared dependencies/configuration, preserve release builds, and ensure the required `test` check reports a result rather than leaving branch protection waiting.

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
