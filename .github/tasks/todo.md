# Project Tasks

## Open

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
- [x] Provide Node/npm in the development target; preserve workspace mounts, lifecycle hooks, Python reload, and existing startup/error reporting. Post-create installs locked npm dependencies and builds assets; image execution validation remains pending.
- [ ] Support initial build and explicit rebuild/watch inside the devcontainer, serving changed assets on port 2158 without an image push or a second frontend server.
- [ ] Verify a source edit, rebuild, and manual browser refresh show the change without stale assets; verify repeat startup and clear build-failure reporting.

#### M4: Single production image

- **Prerequisites:** M1 and M2.
- [x] Add the Node application-build stage using locked `npm ci` and the frontend build; copy only required build output into the Python production runtime.
- [ ] Preserve development/production target separation, non-root permissions, runtime secrets, loopback-only Compose publishing, and explicit AMD64 selection.
- [ ] Verify a clean build without local bundles, frontend/API HTTP responses through Gunicorn, and absence of Node/npm in the production runtime.
- [ ] Verify the React homepage displays the message fetched from `/api` through the production Gunicorn entry point.

#### M5: CI and bundled-image verification

- **Prerequisites:** M3 and M4.
- [x] Extend the existing single CI flow with frontend lint, type-check, tests, and reproducible build checks; preserve triggers, required checks, artifact publication, and no path filtering.
- [ ] Extend image smoke tests to verify frontend HTML/assets, API success/error behavior, and development rebuild support while retaining existing checks.
- [ ] Validate Compose startup and browser requests on a Docker host, record actual evidence, and distinguish environment-blocked checks from passed checks.
- [ ] Repeat the homepage-to-`/api` message proof using the published image through Compose before proceeding with full network-application integration.
- **Partial implementation review:** Development smoke tests now run Node/npm and locked frontend validation in a writable source copy; production checks require generated assets and no Node/npm. Actionlint, shell syntax, all 20 CI-helper tests, and local frontend checks passed. Docker is unavailable locally, so actual image builds, post-create execution, and container checks remain unverified.

#### M6: Network application delivery

- **Prerequisites:** Existing dataset/loader tasks for real topology; M2 for API wiring; M1 for UI work. Synthetic model tests can proceed independently.
- [ ] Complete the local input/merged-model tasks below and verify 37 nodes, 55 links, 391 demands, and 2,068 demand units.
- [ ] Implement and independently test minimum-hop equal-split routing, transit restrictions, utilization/top-five ranking, criticality, and failed-node/link reporting.
- [ ] Connect analysis to the REST API and React map/controls; test fail/restore without page reload, accessible non-color indicators, and explicit invalid-input errors.

#### M7: Delivery documentation and evidence

- **Prerequisites:** M5 and M6 for completed-application claims.
- [ ] Update user instructions only as features become available; keep exact development commands in project context.
- [ ] Record measured results, remaining limitations, and end-to-end evidence in interview notes; retain future image/repository splits and CI filtering as conditional proposals.
- **Review:** Frontend tooling, Docker/CI npm wiring, and same-origin greeting integration are implemented. Network analysis and end-to-end container validation remain pending.

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
  - [ ] Preserve the provisional native file unchanged, recording its source revision, retrieval date, and checksum.
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

- **Status:** Pending
- **Design:** Follow the [local data loading design](../project-context.md#data-loading-design). Use TopoHub's native parser through `LocalSNDlibGenerator`, with local backbone input and CSV merging rather than bundled JSON or runtime downloads.
- **Implementation checklist:**
  - [ ] Verify the `SNDlibGenerator` subclass extension against the locked TopoHub version.
  - [ ] Add the assignment's site table as `sites.csv`.
  - [ ] Implement local backbone loading with file-and-row validation and preserved link identities.
  - [ ] Validate and merge sites, access links, capacities, coordinates, transit roles, and additional demands into one topology.
  - [ ] Test invalid input, including unknown attachments, duplicate IDs, bad capacities, and site references independent of CSV row order.
  - [ ] Verify the merged totals of 37 nodes, 55 links, and 391 demands totaling 2,068 units.
- **Prerequisite for baseline integration tests:** A recorded local backbone snapshot from the resource-gathering task above. Loader implementation and synthetic-fixture tests need not wait for official-source confirmation.
- **Review:** Dependencies are declared and locked; the loader and local input files have not yet been added.
