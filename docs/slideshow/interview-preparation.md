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

### Publication decision: rewritten history and retained PDF

On 2026-10-27, the assignment PDF was removed from every commit in the published `main`/`dev` branch histories, preserving all 70 development commits and the Markdown assignment. GitHub still served the PDF to an authenticated request using an old commit ID after the rewrite. Old PR references or cached objects may retain access after publication; the rewrite is not a complete server-side purge.

The author explicitly accepted this residual exposure of PDF author-name metadata to proceed with publication without waiting for Support or replacing the repository. Both the GitHub repository and GHCR image package became public on 2026-10-27. Anonymous Compose-file download and `main`/`dev` image-manifest access returned HTTP 200; this verifies distribution access, not a new full image pull or application smoke test. The `main` branch still requires PRs and the `test` check, enforces protections for administrators, and blocks force-pushes. See [Git-specific decisions](../descision-notes.md#git-specific-choices) and [GitHub's removal guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository). Do not present an expiration deadline or complete-erasure guarantee.

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

### R2: File-and-row diagnostics and logging

Requirement: **"The application shall reject bad input with an error that names the file and the row."**

- **Implemented:** The local input loader rejects invalid backbone/CSV data with `InputError`, formatted as `<file path>: row <physical row>: <reason>`. The API logs the exception with its traceback and returns a generic JSON HTTP 503 (`{"error": "Network data could not be loaded."}`); file paths and rows are never exposed to clients.
- **Log locations:** Devcontainer startup appends combined server output to `$HOME/.cache/linkscope/runserver.log` and container output. Production sends errors to container stderr, available through `docker compose logs`; there is no dedicated persistent production application log file or application-managed retention.
- **Verification (2026-10-27):** All eight topology tests passed using `.venv/bin/python manage.py test linkscope.test_topology --verbosity 1`, including invalid backbone/CSV cases asserting the filename and exact physical row.
- **Browser message (decision, 2026-10-27):** The frontend shows a generic, user-friendly message for input failures ("The server could not read its network data files. Check the server logs for details.") rather than raw file paths or HTTP codes. Other server errors, client errors, and unreachable-server failures have their own plain-language messages. The file-and-row diagnostic is written only to the server logs, so internal paths are not exposed through the public API. If asked, explain that R2's file/row error is delivered to the operator through the logs.
- **Live error demo (devcontainer, rehearsed 2026-10-27):** The loader reads the data files on every request, so no restart is needed.
  1. Open `http://127.0.0.1:2158/` and show the working baseline.
  2. Break one value, e.g. set the OPS-WEST access capacity to `-1`: `sed -i '4s/,40$/,-1/' data/sites.csv`
  3. Refresh the browser: it shows "Could not load the network. The server could not read its network data files. Check the server logs for details. Refresh to try again."
  4. Show the API hides internals: `curl -s -w ' %{http_code}\n' http://127.0.0.1:2158/api/network` returns `{"error": "Network data could not be loaded."} 503`.
  5. Show the operator diagnostic: `grep InputError ~/.cache/linkscope/runserver.log | tail -1` shows `/app/data/sites.csv: row 4: invalid numeric value '-1'`.
  6. Restore and refresh: `git checkout -- data/sites.csv`; the baseline returns.
  - To show the failure-analysis path instead, load the page first, then break the file and press **Fail selected**: the previous results stay displayed with the same generic message.
  - The published production image bakes the data files in; this demo is not rehearsed against the production container.

### Application delivery status

Current functionality includes a Leaflet network map with utilization and criticality findings fetched from Django, interactive single-node/link fail/restore, separate R8 impact categories, loading/error states, and startup/request logs. M6d exposes topology, baseline/criticality and single-failure reports through read-only JSON endpoints. The application is local-only and unauthenticated.

Dataset loading/validation and the merged model are implemented in M6a; baseline routing and utilization rankings in M6b; single failures and criticality in M6c; network/analysis JSON endpoints in M6d; the baseline map and findings in M6e; interactive fail/restore in M6f. Baseline and single-failure results are now shown by the frontend. Published-image acceptance passed on 2026-10-27: an external validator ran the unmodified public `compose.yaml` anonymously against `main` at `7b3701b` (digest `sha256:b2c8afa7…4ffd`, CI run 40585604261) and reproduced the baseline, L12, Hamburg, HUB-EAST–Warsaw, OPS-WEST–Dublin, and restore results in the browser without reload. Limits: Chrome headless only; browser-visible R2 diagnostics remain open.

M6f keeps one request-local failure active using native labeled selectors/buttons. Failed-node endpoint demands and other undeliverable demands are separately counted/listed with units; every overloaded link shows its load/capacity/utilization. Scenario ranks and map overlays change, while baseline criticality stays explicitly labeled. Abort and response guards reject stale successes/errors; restore reuses the initial validated baseline, without another request. Previous successful results remain explicitly labeled during pending/error states. No new dependency or backend change was needed.

Visual steering clarified the difference between baseline risk predictions and current scenario impacts. The settled desktop layout is 25% sidebar/75% map: collapsed criticality lists above the simulation form on the left, map above side-by-side impact/utilization on the right. Totals are neutral rather than alarm-red because they describe baseline risks. The form groups its buttons below aligned selectors and includes its scope note as a footer. Map instructions remain screen-reader-accessible but visually hidden. Viewport pinch suppression was explicitly requested; keyboard/browser-menu zoom remains available, and browser support/accessibility overrides limit any guarantee of pinch blocking.

M6f verification: 16 frontend tests, lint/type-check/build, production AMD64 build and complete development/production image smoke checks passed. Browser checks measured L12 failure -> L26 128.30%; Hamburg failure -> 27 endpoint demands/162 units and L26 117.06%; HUB-EAST–Warsaw failure -> 20 other undeliverable units without physical disconnection; OPS-WEST–Dublin failure -> disconnection plus 20 units. Restore returned L12 to 71.01%. Injected HTTP 503 recovered; an old delayed L12 success ignoring abort could replace neither a newer L26 result nor baseline restoration. Restore kept the page time origin and map positions unchanged; 390px controls had no page overflow. The local production image repeated L12/Hamburg/restore through Gunicorn and a temporary Compose override on port 22159. Repeat the documented unmodified Compose startup using the published frontend image before final delivery; no publication is implied by these local checks.

M6e uses Leaflet directly and the user-approved standard OpenStreetMap background, retaining the existing shell. All 37 coordinate-based node markers and 55 links appear, with distinct node symbols, criticality asterisks/dashes, five numbered thick links, and textual findings. Attribution remains visible. Eleven frontend tests cover contracts, semantic findings, empty data, builds/watch, and bundled map-image assets; real-browser checks covered 1440px/390px layouts, actual API values, blocked tiles (warning with working overlays/findings), HTTP 503 and recovery. Online tiles are a best-effort external dependency, not required for local analysis; no tile downloading/prefetch or API key. Nearby labels may require zoom. No failure controls or backend changes were included.

M6d uses GET `/api/network` for the complete topology/baseline/criticality and GET `/api/analysis` for baseline or one `kind`/`id` simulation. Restoring is another baseline request, not a server-side mutation. Six API tests verify real response shapes/values, both failure types, restore and independent clients, invalid queries, read-only methods with CSRF enforcement, and logged JSON input/analysis errors. All 45 backend tests passed. No frontend code or dependency was changed; backend M6a-M6d is intended for one PR, followed by a separate frontend PR. Docker smoke tests include the new endpoints but still require hosted execution of the updated script.

M6d Docker follow-up (2026-10-27): after host Docker access was enabled, both AMD64 targets built successfully and the complete image smoke script passed on the laptop engine. Both development Django and production Gunicorn served the real network, baseline/criticality, and the L12 failure report correctly. Alternate loopback ports 22158/22159 preserved the running devcontainer; temporary containers were cleaned up. This closes the M6d review's image-execution gap; frontend integration remains separate.

Delivery-plan correction: the core application was previously compressed into three M6 checklist items despite covering R1-R11. It is now split into M6a-M6f with independent acceptance gates for data, routing, failure analysis, API, map, and interactive delivery. Prioritize these over optional infrastructure; derive presentation findings from measured application results and hand-checked test expectations, not scaffold CI.

M2 now serves React at `/`, greeting JSON at `/api`, and static assets through WhiteNoise with debug disabled. The responsive header/footer share the dark slate palette, with one `logo.svg` used in the header and as the favicon; the main workspace remains open for later functionality. Eight frontend tests, 11 Django tests, 31 CI-helper tests, lint, type checks, and builds passed locally at M2. Browser verification confirmed the same-origin greeting, visible HTTP/network/invalid-response errors, recovery, logo loading, and desktop/mobile layout without horizontal overflow. Review F1's unsupported-method/CSRF mismatch is addressed, with CSRF-enforced regression coverage. The Gunicorn entry point separately served HTML/JS/CSS/JSON successfully. CI Docker builds and HTTP smoke checks subsequently passed; production-image Compose/browser verification remains pending.

The loader now measures **37 nodes, 55 links, and 391 demands totaling 2,068 units**, matching the assignment acceptance targets. Eight loader tests verify real-input totals, checksum and unchanged separate source files, generated demands, backbone capacity 550, endpoint/transit roles, CSV row-order independence, and file/row validation errors. A small synthetic merge has independently calculated expectations (6 nodes, 5 links, 4 demands, 77 units). All 19 backend tests and Ruff checks/format passed at M6a. Quantum Sky approved the mirrored snapshot for this assignment on 2026-10-27; metadata is recorded under `data/`.

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

M3 workspace verification on 2026-10-27 demonstrated frontend edits through both an explicit build and watch mode, followed by ordinary browser refresh on port 2158 without an image push or second frontend server. Intentional syntax errors produced clear build/watch diagnostics, and the watcher recovered after correction. Repeated post-start hooks preserved the working greeting API. All nine frontend and 11 Django tests passed, including new logo-watch and build-error/recovery coverage. Temporary edits were restored. Fresh devcontainer creation and actual container restart remain unverified here because Docker is unavailable; dependencies were not reinstalled. Follow-up (2026-10-27): the user rebuilt the devcontainer on their Docker host and confirmed it runs as expected.

M4/M5 evidence review on 2026-10-27: Actions run 40455416000 passed both image builds, the complete container/HTTP smoke checks, and production-image export/upload. This verifies non-root production permissions, runtime-key startup, generated frontend assets, and absence of Node/npm in the production runtime. A separate local Gunicorn browser check displayed the fetched greeting; the temporary process was stopped. This is not a production-image browser check. Publication failed at `download-artifact@v8.0.2` because its bundled ZIP extractor still emits `DEP0005`; the Node-warning guard correctly failed the action. The version pin did not fix it, and no warning bypass or custom extractor was added. All 32 CI-helper tests passed locally. Published-image Compose/browser checks remain pending on a Docker host, so M4's final browser gate and M5 are not complete.

Subsequent user decision: remove the fatal third-party Node-warning guard to keep warnings visible without blocking jobs. Both workflows now use default Node warning logging; actual action failures and frontend checked-command validation remain enforced. The guard-specific test was removed. Hosted publication after this change remains unverified.

User verification follow-up (2026-10-27): the user confirmed the remaining M4/M5 checks by running `docker compose up -d` from their laptop terminal and marked the published-image/browser acceptance items complete. This supersedes the earlier pending Compose/browser limitations. The user ran the default `:main` tag; that run's digest was not recorded. Hosted publication after the warning-policy change was later verified by CI run 40585604261 and the published-image acceptance of digest `sha256:b2c8afa7…4ffd`.

| Concern | Implemented now | Why incomplete/deferred | First internal-release work |
|---|---|---|---|
| Authentication and access control | No authentication; local host restrictions and loopback-only demonstration. | Account-management scope deferred for the local demonstration. | Add authentication, protected endpoints, least-privilege authorization, and access-control tests before shared use. |
| Logging | Basic server/request stdout/stderr logs; development log file. | Centralized observability deferred; basic diagnostics retained. | Define redaction, collection, retention, operational alerts, and appropriate audit events. |
| Input validation and error handling | Local backbone/CSV validation, tested merged invariants, analysis query validation, and explicit JSON errors with server-side logging are implemented. | Frontend presentation of analysis errors remains pending. | Retain invalid-input/API tests and keep internal tracebacks out of client responses. |
| API versioning | No analysis API or compatibility policy yet. | One jointly delivered frontend/backend; no independent clients. | Define the contract; establish versioning/deprecation policy before supporting independent clients. |
| Configuration and secrets | Runtime secret key required; local allowed hosts; private configuration excluded from images. Demo key is public and not suitable for shared use. | Deployment provisioning and managed secrets deferred. | Private random keys, approved secret delivery and rotation, HTTPS, deployment-specific host/cookie settings. |
| Dependency and security checks | Locked dependencies, lint, unit tests, container smoke tests, and HTTP checks. | Dedicated SAST, DAST, secret scanning, dependency vulnerability, and container scanning jobs are not implemented. | Add the security scanning jobs proposed below, triage findings, and establish remediation and dependency/base-image update ownership. |

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

- **Security scanning jobs:** Add static application security testing (SAST) for Python/TypeScript, secret scanning, software composition analysis (SCA) for dependency vulnerabilities, and production-container OS/package vulnerability scanning to CI. Add dynamic application security testing (DAST) against a running application in an isolated test environment with synthetic data; scan only authorized targets and include authenticated coverage once authentication exists. Produce an SBOM (software bill of materials) for releases. Select tools later, define risk-based release gates and scheduled rescans, assign remediation owners, and document time-limited exceptions. These complement tests and manual review rather than proving the application secure.
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
| How should unavailable official SNDlib inputs be obtained? | Original endpoints failed; a third-party mirror was identified and checked against expected counts. | Resolved 2026-10-27: Quantum Sky approved proceeding with the mirror workaround. It is still not an official SNDlib distribution. |

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
