# Project Tasks

## Open

### Third-party Action warnings

- **Decision (2026-10-27):** Keep Node warnings visible in job logs without turning them into failures. Removed the workflow-level fatal warning guard and its dedicated test from both workflows at the user's request. Actual action failures still fail jobs; frontend checked-command validation is unchanged.
- **Evidence:** Run `40455416000` passed image tests but failed publication because the former guard threw on `download-artifact@v8.0.2`'s upstream `DEP0005` warning. Removing the guard restores Node's default log-only warning behavior; hosted publication must be verified after deployment.

### Deleted-ref package lookup failure

- [x] Remove account-wide package enumeration; query the known package's versions using the existing workflow token.
- [x] Preserve pagination, protected tags, and shared-version guards; report API response bodies and fail on missing/inaccessible packages.
- [x] Validate CI-helper tests and focused Python lint/format checks.
- [ ] Verify the direct versions request and a disposable-version deletion inside Actions; local CLI credentials do not prove workflow-token access.
- **Local review:** All 31 CI-helper tests, focused Ruff lint/format checks, and whitespace checks passed. No live package versions were deleted and no workflow was rerun.
- **Authentication correction:** Package-side Actions admin access is already configured, per the user. Do not infer a PAT requirement from a generic HTTP 400; GitHub supports workflow-token deletion for granular-permission registries.
- **Deferred recovery gap (2026-10-27):** A failed branch-deletion run can leave a tagged image behind after its source branch is gone. Post-publish cleanup only removes untagged versions; it does not reconcile tags against existing Git refs, and deploying a fix does not replay old deletion events. Version `1451948720`, tagged `ci-ghcr-untagged-cleanup`, remained after [deletion run 40446804179](https://github.com/fr3nch13/qsp137sa/actions/runs/40446804179) failed. The user chose manual deletion for this instance; completion has not been verified. Further implementation is deferred for time.
- [ ] If an image tag remains after another source-branch deletion, investigate the deletion run and address the recovery/reconciliation gap rather than repeatedly relying on manual deletion. Preserve protected-tag and shared-version safeguards.

### GHCR untagged image cleanup

- **Scope:** Separate from the stashed M2 work; preserve all tagged images and delete untagged versions last updated at least 24 hours ago.
- [x] Add paginated cleanup with a tag recheck before each deletion and explicit API failure handling.
- [x] Run cleanup after successful CI publication, serialized across refs.
- [x] Validate helper tests, Python lint/format, and workflow syntax.
- [ ] Verify the eligible existing untagged backlog is removed by the first successful CI cleanup after these changes are published.
- **Review:** All 27 CI-helper tests, focused Ruff lint/format checks, actionlint, and whitespace checks passed. The initial live attempt failed before deletion because package read permission was missing. The user subsequently authorized the CLI and chose to leave the backlog for CI rather than delete it locally. CI deletion uses its own `GITHUB_TOKEN`, which needs package admin access independently of CLI authorization.
- **24-hour buffer follow-up:** All 31 CI-helper tests and focused Ruff checks passed after adding last-update retention, including the exact cutoff boundary and a recent update discovered during the pre-deletion recheck.

### Bundled frontend and API milestones

- **Status:** M1 and M2 implemented and locally validated on 2026-10-27; M3-M7 still have pending integration/delivery checks.
- **Scope:** One shipped image and one origin on port 2158, React at `/`, Django REST API under `/api`, Gunicorn retained. No Vite/HMR, extra server, service split, or CI path filters.
- [x] Record architecture, source-control policy, local rebuild workflow, trade-offs, and future evolution in the handoff, project context, and interview notes.

#### M1: Frontend source and build foundation

- **Status:** Complete; locally validated with Node 24.

- [x] Establish React/TypeScript source layout and minimal build tooling without Vite; include npm manifests, lockfile, build configuration, and authored assets for source control.
- [x] Add `npm run build` and a build-watch command, plus lint, type-check, and focused frontend tests. Document exact directories and commands.
- [x] Ignore dependencies, compiled bundles, and collected static output in Git; ensure clean builds do not rely on existing generated files.
- **Review:** `npm ci`, Biome lint/format checks, TypeScript checks, all three tests, and production frontend build passed. Tests verify shell semantics, source-only build output, and watch rebuilds for TSX, CSS, and HTML. Docker/CI npm wiring was added following review rather than leaving validation local-only. Serving the frontend remains M2.
- **CI log follow-up:** Job `121974036972` passed. Added version-specific approval for esbuild's required install script and upgraded setup-node to v7. Job `121984240923` then failed because the checked Docker install detected bundled npm's upgrade notice. Final agreed policy: retain Node 24's bundled npm, disable only its newer-version notification through the frontend `.npmrc`, and continue failing checked validation on other warnings/notices. Docker copies `.npmrc` before dependency installation; no standalone npm upgrade is performed.

#### M2: Same-origin Django serving and frontend/API proof

- **Status:** Complete; local browser and Gunicorn proof passed. Updated Docker/Compose execution remains M4-M5.
- **Review F1 addressed:** The read-only greeting endpoint consistently returns JSON 405 for unsupported methods with CSRF enforcement enabled. Its narrowly scoped CSRF exemption must not apply to future state-changing functionality. All 11 Django tests passed, including method-contract and retained middleware-protection regressions; see the [M2 review](../review/review-2026-10-27-0459-m2-same-origin.md).
- **Prerequisite:** M1 for generated frontend assets.
- **Goal:** Prove the smallest working browser-to-API round trip before building the network application.
- [x] Wire Django routing and static-file serving for `/` and `/api`; retain Gunicorn for production without Apache/nginx or CORS.
- [x] Add `GET /api` returning HTTP 200 and `application/json` with `{"message": "Hello, world!"}` using Django's native JSON response support.
- [x] Have the React homepage fetch the relative `/api` URL and display the returned message, not a hardcoded success message. Show loading and explicit network, HTTP, or invalid-response errors.
- [x] Define/test the initial API response/error contract. Keep unknown API routes and missing assets out of the frontend HTML fallback.
- [x] Test frontend HTML/assets and API responses with debug disabled, correct content types, and appropriate development versus production caching.
- [x] Verify in a real browser at `http://127.0.0.1:2158/` that React loads, requests `/api` on the same origin, and displays the actual returned message. Verify a failed API request produces a visible error, not success-shaped fallback content.
- **Review:** 11 Django and eight frontend tests passed, including content types, unknown paths, methods with CSRF enforcement, missing build logging/503, shared logo/favicon routing, asset rebuild visibility, and invalid API responses. Real browser verification showed the backend greeting, explicit HTTP/network/invalid-response errors, and recovery. The responsive header/open-body/footer layout uses the documented palette and a shared `logo.svg`; desktop/mobile checks found no horizontal overflow. Gunicorn separately served HTML/JS/CSS/JSON with debug disabled. WhiteNoise 6.12.0 is pinned; fixed-name assets revalidate in both development and production, with no immutable-cache claim. Ruff, frontend lint/type checks/build, all 31 CI-helper tests, and whitespace checks passed.
- **Acceptance gate:** Do not start M6 application integration until this browser round trip passes. Carry the same minimal proof through M3-M5 to verify rebuilds, Gunicorn, and the published container rather than assuming development success proves production packaging.

#### M3: Devcontainer rebuild workflow

- **Prerequisites:** M1 and M2 for end-to-end verification.
- **Status:** Workspace build/watch/browser workflow verified on 2026-10-27; fresh container creation/restart verification remains pending on a Docker host.
- [x] Provide Node/npm in the development target; preserve workspace mounts, lifecycle hooks, Python reload, and existing startup/error reporting. Post-create installs locked npm dependencies and builds assets; image-installed Node 24.22.1 and bundled npm 11.19.1 were used for this verification.
- [x] Support initial build and explicit rebuild/watch inside the devcontainer, serving changed assets on port 2158 without an image push or a second frontend server.
- [x] Verify a source edit, rebuild, and manual browser refresh show the change without stale assets; verify repeat startup and clear build-failure reporting.
- [x] Recreate/restart the devcontainer on a Docker host to verify actual lifecycle execution, including the post-create dependency install and initial build.
- **Review:** Explicit build and watch edits appeared in the live browser after normal refresh on port 2158, without cache clearing. An intentional syntax error made the explicit build exit 1 with a file/line diagnostic; watch reported the error, stayed running, and recovered after correction. Repeated post-start hooks left the API working. Added automated logo-watch and syntax-error/recovery coverage; all nine frontend and 11 Django tests passed. Temporary edits were restored and the watcher stopped. Docker is unavailable here; this does not claim a fresh devcontainer recreation or actual container restart, and existing dependencies were not reinstalled.

#### M4: Single production image

- **Prerequisites:** M1 and M2.
- **Status:** Complete; CI packaging checks passed and the user confirmed the remaining production-image checks from their laptop.
- [x] Add the Node application-build stage using locked `npm ci` and the frontend build; copy only required build output into the Python production runtime.
- [x] Preserve development/production target separation, non-root permissions, runtime secrets, loopback-only Compose publishing, and explicit AMD64 selection.
- [x] Verify a clean build without local bundles, frontend/API HTTP responses through Gunicorn, and absence of Node/npm in the production runtime.
- [x] Verify the React homepage displays the message fetched from `/api` through the production Gunicorn entry point.
- **Review (2026-10-27):** [Run 40455416000](https://github.com/fr3nch13/qsp137sa/actions/runs/40455416000) passed development/production image builds and image/HTTP tests. The smoke script checks UID 10001, a non-writable application directory, absent `.env`/`.git`, no Node/npm, generated assets, and the greeting API. `.dockerignore` excludes local bundles/dependencies; production builds its frontend from source. Compose preserves loopback-only binding and explicit AMD64 selection. A separate local Gunicorn process served HTML/JS/CSS/logo and displayed the API greeting in a real browser on port 2160, then was stopped. This verifies the entry point, not the production container in a browser; that final checkbox remains open. No Dockerfile change was necessary.

#### M5: CI and bundled-image verification

- **Prerequisites:** M3 and M4.
- **Status:** Acceptance checklist complete; the user confirmed the remaining published-image Compose/browser checks on their laptop on 2026-10-27 using `docker compose up -d`. This supersedes the earlier local-environment verification limitations below. The selected image tag/digest was not recorded.
- [x] Extend the existing single CI flow with frontend lint, type-check, tests, and reproducible build checks; preserve triggers, required checks, artifact publication, and no path filtering.
- [x] Extend image smoke tests to verify frontend HTML/assets, API success/error behavior, and development rebuild support while retaining existing checks.
- [x] Validate Compose startup and browser requests on a Docker host, record actual evidence, and distinguish environment-blocked checks from passed checks.
- [x] Repeat the homepage-to-`/api` message proof using the published image through Compose before proceeding with full network-application integration.
- **Review (2026-10-27):** Development smoke tests run Node/npm and locked frontend validation (including source-only build/watch tests) in a writable copy; both images are checked for HTML/assets/API success and missing-route errors. [Run 40455416000](https://github.com/fr3nch13/qsp137sa/actions/runs/40455416000) passed the complete test job, including image builds, smoke tests, and production-image export/upload. Publication then failed: `download-artifact@v8.0.2` still emits `DEP0005` from its bundled ZIP extractor, and the required Node-warning guard correctly fails it. The version pin did not fix the upstream warning. No suppression or custom extraction workaround was added. All 32 CI-helper tests passed again locally. Actual post-create execution, fresh container recreation, and published-image Compose/browser verification remain unverified here because Docker is unavailable. M5 is not complete.
- **Policy follow-up:** Removed the fatal third-party Node-warning guard at the user's request; warnings remain in logs and no custom extraction is needed. Publication after this change still requires hosted validation.
- **User verification follow-up (M4/M5):** The user checked off the remaining items after verifying the published application through Compose from their laptop terminal. This closes the production-image/browser acceptance gates; it does not establish that a new CI run has published the warning-policy change.

#### M6: Network application delivery

- **Priority:** This is the core assignment, not a follow-up feature. M1-M5 establish the delivery foundation; remaining implementation effort should focus on R1-R11 below, not optional infrastructure.
- **Status:** M6a-M6f implemented and locally validated; M6f published-image acceptance remains pending publication. Backend M6a-M6d belongs in one PR; frontend M6e-M6f belongs in a separate PR. Stop after each milestone for user review. Keep one application/container, the existing frontend shell, and no database.
- **Prerequisites:** M1/M2 provide frontend/API integration. The dataset-source and loader sections below retain their detailed research/implementation checklists; M6a is their application acceptance gate, not a second implementation.

##### M6a: Load and validate the real network (R1-R4)

- [x] Preserve the selected local backbone snapshot with source revision, retrieval date, checksum, and attribution; add the exact assignment table as `sites.csv`. Keep unresolved official-source/permitted-use questions explicit.
- [x] Complete the existing TopoHub local-loader checklist below: preserve IDs/coordinates, merge both inputs, use undirected links/demands, force backbone capacity 550, retain site access capacities, and assign endpoint/transit roles.
- [x] Add twelve 10-unit operations-site/data-center demands and one 50-unit data-center demand.
- [x] Reject malformed inputs with file-and-row errors; test duplicate IDs, missing/unknown attachments, invalid values, and row-order-independent site references.
- **Acceptance:** Tests load the real inputs and independently assert 37 nodes, 55 links, 391 demands, and 2,068 demand units, plus capacities, roles, coordinates, and generated demand endpoints. Synthetic invalid-input tests must not depend on network access.
- **Review (2026-10-27):** `load_topology()` reads separate `data/nobel-eu.txt` and `data/sites.csv` files, validates them, and merges only in memory. Tests verify both inputs remain unchanged. The real snapshot yields exactly 37 nodes, 55 links, 391 demands, and 2,068 units. Eight loader tests (including invalid-input subcases, an independently calculated small merge, row reordering, and input immutability) plus 11 existing Django tests passed. Ruff checks/format passed. Dataset source revision/checksum are recorded in `data/README.md`; official provenance/permitted-use confirmation remains open. Routing and API/UI exposure are intentionally deferred to M6b-M6f.

##### M6b: Route traffic and rank link utilization (R5-R6, calculation for R10)

- **Prerequisite:** M6a for real-data acceptance; hand-calculated synthetic tests can start earlier.
- [x] Route each demand along all minimum-hop paths and split equally among complete tied paths, not merely equally among next hops.
- [x] Permit only backbone cities and the aggregation hub as intermediate nodes; operations sites/data centers remain valid source/destination endpoints.
- [x] Sum undirected link loads, calculate utilization against capacity, and return the five most utilized links with deterministic tie ordering.
- [x] Test a unique route, equal shortest paths, unequal numbers of downstream shortest paths, prohibited endpoint transit, unreachable demands, and traffic/load conservation against hand-calculated expectations.
- **Acceptance:** Independently checked synthetic results pass; the real baseline produces reproducible loads and top-five values. Record measured values rather than inventing expected network findings.
- **Review (2026-10-27):** `route_traffic()` uses the existing NetworkX dependency with equal shares across complete shortest paths. Eight routing tests cover hand-calculated loads, fractional shares/conservation, reverse-direction aggregation, transit restrictions, disconnected demands, percentage-based ranking/ties, and real-input order-independent reproducibility without mutation. All 27 backend tests and Ruff lint/format checks passed. All 391 baseline demands are deliverable. Top five: L12 Berlin–Hamburg 71.008521%, L3 Amsterdam–Hamburg 68.404549%, L26 Frankfurt–Munich 62.126088%, L30 Milan–Munich 58.814992%, L13 Berlin–Munich 50.629551%. API/UI and failure analysis remain later milestones.

##### M6c: Analyze single failures and criticality (R7-R8)

- **Prerequisite:** M6b.
- [x] Simulate one failed node or link without mutating the baseline; node failure also removes its incident links.
- [x] Report failed-node endpoint demands separately from other undeliverable demands, including demand identities and units; list every remaining link above 100% utilization.
- [x] Evaluate every single-node and single-link failure. Mark an element critical when its loss disconnects the remaining network, makes any demand undeliverable, or overloads a remaining link; include the applicable reasons.
- [x] Test disconnection, failed endpoints, rerouting, overload, exactly-100% boundaries, and restoration against small independently calculated networks.
- **Acceptance:** Baseline and each real-network single failure can be analyzed reproducibly; restoring an element returns the original results. Record the team's single-point-of-failure findings with their reasons.
- **Review (2026-10-27):** `linkscope/failures.py` reuses baseline routing on filtered, immutable topology records. Twelve failure tests plus existing tests pass (39 backend tests total); Ruff lint/format and whitespace checks pass. All 92 real single failures were evaluated reproducibly: 37 critical nodes and six critical links. Failed-node endpoint demands count toward criticality but are reported separately. Failing L12 overloads L26 to 128.295317%; failing L26 overloads L12 to 112.358841%. Four access links lose 20 demand units each: HUB-EAST–Warsaw, OPS-EAST-1–HUB-EAST, OPS-SOUTHEAST–Athens, and OPS-WEST–Dublin. HUB-EAST–Warsaw remains physically connected via OPS-EAST-2, but the endpoint transit restriction prevents delivery. Full findings and interpretation are recorded in interview notes. API/UI exposure remains M6d-M6f.

##### M6d: Expose the network and analysis through the API

- **Prerequisites:** M6a-M6c and M2.
- [x] Define a concise typed JSON contract for topology, baseline/top-five/criticality results, and one selected node/link failure with R8 results; keep frontend/backend field names consistent.
- [x] Validate failure type and identity explicitly; reject unknown or invalid selections with JSON errors and appropriate HTTP status codes. Surface data-loading/analysis failures without success-shaped fallbacks.
- [x] Keep simulations request-local; one browser's failure selection must not change another browser's baseline. Retain appropriate CSRF handling if unsafe HTTP methods are used.
- [x] Add API tests for baseline, node/link failure, restore/baseline equivalence, invalid requests, and independent requests.
- **Acceptance:** Real topology and analysis flow through Django JSON endpoints with tested output shapes; no hardcoded frontend results or separate service is needed.
- **Review (2026-10-27):** Read-only `/api/network` exposes topology, baseline and all criticality reasons; `/api/analysis` exposes baseline or one `kind=node|link&id=...` failure. No shared simulation state or cache. Invalid/repeated/unknown query parameters return JSON 400, unknown elements 404, unsupported methods 405, input failures logged JSON 503, and NetworkX failures logged JSON 500. Greeting endpoints/frontend remain unchanged. Six real-data API tests plus prior tests pass (45 backend tests total); image smoke checks now request the new endpoints as well. Docker image execution of these new checks remains hosted validation, not a local pass. Stop here before M6e.
- **Docker follow-up:** Both AMD64 image targets subsequently built and the complete image smoke script passed using host Docker Desktop, with alternate ports 22158/22159 to preserve the running devcontainer. New network/analysis endpoints passed through both images, including production Gunicorn. Review F1 (complete response types) and G1 (image execution) are addressed; temporary containers were cleaned up. M6e has not started.

##### M6e: Show the network map and baseline findings (R9-R10)

- **Acceptance (2026-10-27):** User accepted the initial M6e version and requested its commit. Follow-up refinements include tighter network framing, quarter-level zoom steps, findings left/map right at widths >=768px, critical elements before utilization, and right-aligned header totals with bold red critical counts. Below 768px the layout stacks. Final frontend suite: 12 passing tests; lint and type-check/build pass. M6f remains pending.

- **Prerequisite:** M6d.
- [x] Replace the greeting-demo body with a coordinate-based network map; place sites near their attachments, including the hub-attached operations sites, with readable labels.
- [x] Display critical nodes/links and reasons, plus the five most utilized links with load/capacity/utilization values.
- [x] Use labels, shapes, line styles, or badges as well as color; retain the existing header/footer and palette, with accessible loading, empty, and error states.
- **Acceptance:** The real 37-node/55-link network is visible in the browser, results match the API, and users can identify critical elements and top-five links without relying on color alone.
- **Review (2026-10-27):** Leaflet 1.9.4 and TypeScript types 1.9.22 are locked; React draws the actual API coordinates over standard OpenStreetMap tiles (user-approved provider). The page displays 37 nodes/55 links, five numbered thick link overlays, different node symbols, critical asterisks/dashed lines, utilization table, and criticality reasons in expandable lists. Existing branding remains. Runtime API validation rejects malformed contracts; loading, empty-network, API-error, map-init-error and tile-error states are explicit. Eleven frontend tests, lint and type-check/build pass, including contract/presentation and packaged Leaflet image checks. Desktop (1440px) and narrow (390px) browser checks found no horizontal overflow and retained visible attribution. Blocking tiles preserved overlays/findings with a warning; HTTP 503 and malformed contracts showed errors instead of findings, then normal fetching recovered. The AMD64 production image builds, and existing development/production image smokes pass on alternate ports 22158/22159 without disturbing the devcontainer; temporary containers were removed. Nearby labels can require zoom. M6f controls are not implemented; no backend changes were needed.

##### M6f: Fail/restore interactively and verify the complete application (R11; end-to-end R1-R10)

- **Prerequisite:** M6e.
- [x] Provide keyboard-accessible node/link selection and fail/restore controls for any element, with at most one simulated failure active.
- [x] Update the map and R8 report without a full-page reload; clearly distinguish failed-endpoint demands, other undeliverable demands, and overloaded links.
- [x] Handle request failures and rapid selection changes explicitly so stale responses cannot overwrite the current selection; restoring returns the baseline.
- [x] Add focused frontend tests and real-browser checks covering node failure, link failure, restore, accessible indicators, and visible API errors.
- [ ] Repeat the application proof using the published image through the documented Compose startup command; update the README's actual capabilities and remaining limitations.
- **Acceptance:** A user can start the app with one command, see the baseline findings, fail/restore any node or link, and receive correct updated results without reloading. Record the team's three answers with measured numbers for M7.
- **Review (2026-10-27):** Native labeled selectors cover all 37 nodes/55 links. Fail selected replaces the single active failure; Restore baseline aborts pending requests and restores the validated initial result immediately. Analysis shape/scenario/link/demand validation is shared with the existing API fetch path. R8 reports expose separate demand counts/units and expandable complete demand lists, every overload, connectivity, and scenario-aware utilization. The map updates overlays without rebuilding its basemap or resetting pan/zoom, with explicit failed/overloaded labels. Baseline criticality remains labeled as baseline.
- **Verification:** 16 frontend tests, lint, type-check/build, AMD64 production build and complete development/production image smokes pass. Browser checks verified L12 -> L26 at 128.30%, Hamburg -> 27 failed-endpoint demands/162 units and L26 at 117.06%, HUB-EAST–Warsaw -> 20 undeliverable units despite physical connectivity, OPS-WEST–Dublin -> disconnection plus 20 units, and restore -> L12 at 71.01%. Forced HTTP 503 recovered without sample-result fallbacks. An artificially delayed L12 response (ignoring abort) could overwrite neither a newer L26 result nor a restore; restore preserved page time origin and map positions. A 390px viewport retained controls/markers without page overflow.
- **Delivery proof:** Local production image also started through `compose.yaml` with a temporary local-image/no-pull/alternate-port override. Its Gunicorn-served UI reproduced L12 and Hamburg failures and baseline restore without reloading (37 markers/55 links). This is not a published-image claim: repeat the documented unmodified Compose command after frontend publication. No backend changes, dependency additions, commit, push or release were required for this step.
- **Settled visual design:** 25%/75% sidebar/map grid at >=768px; collapsed baseline criticality lists above the simulation form, aligned selectors and grouped buttons, with the scope note inside the form footer. Status/impact and utilization share two columns directly beneath the map; mobile stacks. Header totals are neutral, right-aligned above the map. Map instructions are screen-reader-only. User requested suppression of viewport pinch gestures while retaining ordinary scrolling and keyboard/browser-menu zoom. Final checks are recorded in project context; published-image acceptance remains unchecked.
- **Pre-review rerun (2026-10-27):** Final documentation synchronized; 16 frontend tests, lint, type-check/build, rebuilt AMD64 production image and full development/production image smokes passed. Final browser checks at 1440/768/390px found no horizontal overflow and confirmed collapsed lists, footer placement, L12 overload and restore. Ready for the user's review agent; changes remain uncommitted/unpushed.

#### M7: Delivery documentation and evidence

- **Prerequisites:** M5 and M6 for completed-application claims.
- [ ] Update user instructions only as features become available; keep exact development commands in project context.
- [ ] Record measured results, remaining limitations, and end-to-end evidence in interview notes; retain future image/repository splits and CI filtering as conditional proposals.
- **Review:** Frontend tooling, Docker/CI integration, and the published greeting demonstration are verified. The actual network application remains M6a-M6f; use its measured results and verification evidence for final delivery.

### Docker Compose startup

- **Status:** Implemented; configuration validated, user confirmed startup on macOS
- [x] Add a single-service Compose file using the published image, loopback-only port publishing, and configurable image tag and secret key.
- [x] Document Compose startup, logs, shutdown, and configuration while retaining the Docker run alternative.
- [x] Validate configuration and review the diff; record any environment limitations.
- **Review:** Standalone Docker Compose v2.40.3 successfully rendered the default `main`, overridden `dev`, and versioned-release configurations. Assertions verified image selection, secret values, always-pull behavior, loopback-only port 2158, and absence of builds or volumes. Whitespace checks passed.
- **User verification:** Compose pulled the image, created the network, and started the container on an ARM64 Mac. Container status remained up and Gunicorn booted successfully, using AMD64 emulation. Browser HTTP readiness and shutdown were not reported.
- **Architecture decision:** Explicitly select Linux AMD64 in Compose and the Docker run alternative. Retain single-platform CI and use host-provided emulation on ARM64 for the local demo; record rationale and trade-offs in the interview preparation notes. The briefly proposed multi-platform CI edits were removed before publication.
- **Final validation:** Standalone Compose v2.40.3 rendered the explicit `linux/amd64` platform and loopback binding successfully. CI workflow and smoke-test script match their committed versions.

### Upgrade Actions runtimes after the first PR run

- **Status:** Implemented; repeat CI validation pending
- [x] Upgrade checkout, artifact transfer, and Docker actions to Node.js 24-native releases in both workflows.
- [x] Preserve existing triggers, permissions, image tags, and artifact transfer behavior.
- [ ] Validate workflows locally and confirm the pushed PR run passes without deprecated-runtime warnings.

### Review F1: Fresh-checkout devcontainer environment

- **Status:** Complete; host initialization validated
- [x] Create the private environment file before Docker starts without overwriting existing values.
- [x] Verify fresh-checkout permissions and preservation of existing configuration.
- **Review:** All 20 CI-helper tests passed, including new-file mode `0600`, workspace paths containing spaces, repeated initialization, and preservation of existing file contents and permissions. Ruff and whitespace checks passed.
- **Limitation:** Full devcontainer startup requires Docker; host initialization is tested independently.

### GitHub Actions checks, publishing, and image cleanup

- **Status:** Implemented; local validation passed, Docker/GHCR validation pending
- [x] Scope CI to same-repository PRs into main/dev, main pushes, and tag pushes; skip forks.
- [x] Restrict release triggers and validation to SemVer tags.
- [x] Treat `dev` as a persistent branch: publish `dev` only from PRs sourced from `dev`, test-only `main`-sourced PRs, reserve and protect `main`/`dev` tags.
- [x] Add locked Ruff, Python/shell lint checks, CI helper tests, and Django tests.
- [x] Build both images and require HTTP 200 and in-container tests before publication.
- [x] Publish the tested production artifact to GHCR with validated branch/main/release tags.
- [x] Add ref-deletion cleanup with shared-version protection and explicit API errors.
- [x] Complete locally available checks: Ruff lint/format, ShellCheck, actionlint, lockfile validation, 18 CI-helper tests, and three Django tests.
- **Limitation:** Docker builds and GitHub/GHCR operations cannot be exercised in this environment; verify them on the first Actions run. Package deletion requires repository Actions admin access to the package.

### Django scaffold and container startup

- **Status:** Complete; Docker image validation remains environment-blocked
- [x] Scaffold Django without authentication or database setup.
- [x] Add locked Gunicorn dependency and replace the production placeholder with the WSGI server on port 2158.
- [x] Require the secret key at runtime and restrict allowed hosts to local addresses.
- [x] Document local startup and loopback-only container publishing.
- [x] Verify system checks, all three route tests, and an HTTP request through the exact Docker Gunicorn command on port 2158.
- **Review:** Lockfile and whitespace checks passed. Missing runtime secret key produces an explicit configuration error. Gunicorn starts, serves HTTP 200, and shuts down cleanly; its unused control socket is disabled for compatibility with root-owned application files.
- **Limitation:** Docker is unavailable in the current environment; image build and container smoke tests must run where Docker is available.

### Gather and validate the Nobel-EU dataset source

- **Status:** In progress; provisional mirror selected, official-source confirmation pending
- **Goal:** Select a reliable source for the required `nobel-eu` backbone data and make its use reproducible.
- **Decision (2026-10-23):** Use a local `nobel-eu.txt` from the [sikorski-as/sndlib native-text mirror](https://raw.githubusercontent.com/sikorski-as/sndlib/master/native/nobel-eu/nobel-eu.txt) provisionally. The project owner will contact Quantum Sky about the original source failures. This does not resolve provenance or permitted-use checks.
- **Remaining work:**
  - [ ] Obtain clarification from Quantum Sky and locate or confirm the official dataset.
  - [x] Preserve the provisional native file unchanged, recording its source revision, retrieval date, and checksum.
  - [ ] Confirm provenance, permitted use, and attribution; compare or replace the provisional copy when an official file becomes available.
- **Acceptance criteria:**
  - Confirm the selected source's provenance and permitted use.
  - Validate that the data represents 28 nodes, 41 links, and 378 demands, including node coordinates and demand values.
  - Record the source citation and preserve the dataset in a reproducible, appropriately attributed form.
  - Do not bypass TLS certificate validation to retrieve data.

#### Source findings (checked 2026-10-23)

The assignment's original download endpoints are currently unusable:

- [SNDlib XML download](https://sndlib.put.poznan.pl/download/sndlib-networks-xml/nobel-eu.xml) returned HTTP 404.
- [SNDlib native-text download](https://sndlib.put.poznan.pl/download/sndlib-networks-native/nobel-eu.txt) returned HTTP 404.
- The `sndlib.put.poznan.pl` TLS certificate names `ventus.put.poznan.pl` as its Common Name and only Subject Alternative Name. Normal hostname verification therefore fails. The 404 checks were diagnostic requests with certificate validation disabled; do not use that as a retrieval workaround.
- Requests to the corresponding paths on `ventus.put.poznan.pl` also returned HTTP 404.
- The `sndlib.zib.de` download URLs redirect to `sndlib.put.poznan.pl`, so they do not provide a working independent official source.

Potential alternatives found and checked:

1. **SNDlib native-text and XML mirrors in the same repository:**
   - [Native text](https://github.com/sikorski-as/sndlib/blob/master/native/nobel-eu/nobel-eu.txt) ([raw file](https://raw.githubusercontent.com/sikorski-as/sndlib/master/native/nobel-eu/nobel-eu.txt)) identifies itself as SNDlib native format, network `nobel-eu`, version 1.0.
   - [XML, identified by the project owner](https://github.com/sikorski-as/sndlib/blob/master/xml/nobel-eu/nobel-eu.xml) ([raw file](https://raw.githubusercontent.com/sikorski-as/sndlib/master/xml/nobel-eu/nobel-eu.xml)) is also available with normal TLS validation.
   - Both files were parsed and counted: each contains 28 nodes, 41 links, and 378 demands totaling 1,898 units. All 28 XML nodes have coordinates. Adding the assignment's sites and demands yields the expected 37 nodes, 55 links, and 391 demands totaling 2,068 units.
   - Counts and demand totals match, but a complete record-by-record comparison has not been performed. This is a third-party GitHub repository, not verified as an official SNDlib source; provenance and permitted use remain to be confirmed before adoption.
2. **TopoHub JSON conversion:** [TopoHub — `data/sndlib/nobel-eu.json`](https://github.com/piotrjurkiewicz/topohub/blob/master/data/sndlib/nobel-eu.json) ([raw file](https://raw.githubusercontent.com/piotrjurkiewicz/topohub/master/data/sndlib/nobel-eu.json)). The raw file returned HTTP 200. Inspection found 28 nodes, 41 edges, and 378 demand entries. This is a converted JSON representation, not an original SNDlib file; verify coordinates, link endpoints, demand values, and provenance against the expected network before use.
3. **XML copy in a project repository:** [Ruayakh8/ICA-JH-Simulation — `data/topologies/sndlib/nobel-eu.xml`](https://github.com/Ruayakh8/ICA-JH-Simulation/blob/main/data/topologies/sndlib/nobel-eu.xml) ([raw file](https://raw.githubusercontent.com/Ruayakh8/ICA-JH-Simulation/main/data/topologies/sndlib/nobel-eu.xml)). The raw file returned HTTP 200 and appears to be XML, but its provenance and contents have not been independently validated. Treat as a fallback candidate only.

These candidates are not equivalent in provenance or format. Verify a candidate against known network counts and content before relying on it, and cite both SNDlib and any mirror or conversion used.

### Implement local backbone and site loading with TopoHub

- **Status:** Implemented and locally verified (M6a); provenance/permitted-use confirmation remains open.
- **Design:** Follow the [local data loading design](../project-context.md#data-loading-design). Use TopoHub's native parser through `LocalSNDlibGenerator`, with local backbone input and CSV merging rather than bundled JSON or runtime downloads.
- **Implementation checklist:**
  - [x] Verify the `SNDlibGenerator` subclass extension against the locked TopoHub version.
  - [x] Add the assignment's site table as `sites.csv`.
  - [x] Implement local backbone loading with file-and-row validation and preserved link identities.
  - [x] Validate and merge sites, access links, capacities, coordinates, transit roles, and additional demands into one topology.
  - [x] Test invalid input, including unknown attachments, duplicate IDs, bad capacities, and site references independent of CSV row order.
  - [x] Verify the merged totals of 37 nodes, 55 links, and 391 demands totaling 2,068 units.
- **Prerequisite for baseline integration tests:** A recorded local backbone snapshot from the resource-gathering task above. Loader implementation and synthetic-fixture tests need not wait for official-source confirmation.
- **Review:** Implemented in `linkscope/topology.py`, with separate unchanged backbone/CSV inputs under `data/` and eight loader tests. No runtime download, new dependency, routing, or API change.
