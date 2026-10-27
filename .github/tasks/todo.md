# Project Tasks

## Open

### Bundled frontend and API milestones

- **Status:** Architecture documented on 2026-10-27; implementation pending.
- **Scope:** One shipped image and one origin on port 2158, React at `/`, Django REST API under `/api`, Gunicorn retained. No Vite/HMR, extra server, service split, or CI path filters.
- [x] Record architecture, source-control policy, local rebuild workflow, trade-offs, and future evolution in the handoff, project context, and interview notes.

#### M1: Frontend source and build foundation

- [ ] Establish React/TypeScript source layout and minimal build tooling without Vite; commit npm manifests, lockfile, build configuration, and authored assets.
- [ ] Add `npm run build` and a build-watch command, plus lint, type-check, and focused frontend tests. Document exact directories and commands.
- [ ] Ignore dependencies, compiled bundles, and collected static output in Git; ensure clean builds do not rely on existing generated files.

#### M2: Same-origin Django serving

- **Prerequisite:** M1 for generated frontend assets.
- [ ] Wire Django routing and static-file serving for `/` and `/api`; retain Gunicorn for production without Apache/nginx or CORS.
- [ ] Define/test the initial API response/error contract. Keep unknown API routes and missing assets out of the frontend HTML fallback.
- [ ] Test frontend HTML/assets and API responses with debug disabled, correct content types, and appropriate development versus production caching.

#### M3: Devcontainer rebuild workflow

- **Prerequisites:** M1 and M2 for end-to-end verification.
- [ ] Provide Node/npm in the development target; preserve workspace mounts, lifecycle hooks, Python reload, and existing startup/error reporting.
- [ ] Support initial build and explicit rebuild/watch inside the devcontainer, serving changed assets on port 2158 without an image push or a second frontend server.
- [ ] Verify a source edit, rebuild, and manual browser refresh show the change without stale assets; verify repeat startup and clear build-failure reporting.

#### M4: Single production image

- **Prerequisites:** M1 and M2.
- [ ] Add the Node application-build stage using locked `npm ci` and the frontend build; copy only required build output into the Python production runtime.
- [ ] Preserve development/production target separation, non-root permissions, runtime secrets, loopback-only Compose publishing, and explicit AMD64 selection.
- [ ] Verify a clean build without local bundles, frontend/API HTTP responses through Gunicorn, and absence of Node/npm in the production runtime.

#### M5: CI and bundled-image verification

- **Prerequisites:** M3 and M4.
- [ ] Extend the existing single CI flow with frontend lint, type-check, tests, and reproducible build checks; preserve triggers, required checks, artifact publication, and no path filtering.
- [ ] Extend image smoke tests to verify frontend HTML/assets, API success/error behavior, and development rebuild support while retaining existing checks.
- [ ] Validate Compose startup and browser requests on a Docker host, record actual evidence, and distinguish environment-blocked checks from passed checks.

#### M6: Network application delivery

- **Prerequisites:** Existing dataset/loader tasks for real topology; M2 for API wiring; M1 for UI work. Synthetic model tests can proceed independently.
- [ ] Complete the local input/merged-model tasks below and verify 37 nodes, 55 links, 391 demands, and 2,068 demand units.
- [ ] Implement and independently test minimum-hop equal-split routing, transit restrictions, utilization/top-five ranking, criticality, and failed-node/link reporting.
- [ ] Connect analysis to the REST API and React map/controls; test fail/restore without page reload, accessible non-color indicators, and explicit invalid-input errors.

#### M7: Delivery documentation and evidence

- **Prerequisites:** M5 and M6 for completed-application claims.
- [ ] Update user instructions only as features become available; keep exact development commands in project context.
- [ ] Record measured results, remaining limitations, and end-to-end evidence in interview notes; retain future image/repository splits and CI filtering as conditional proposals.
- **Review:** Documentation planning only in this change; no frontend, server, dependency, ignore-file, Dockerfile, or CI implementation has been performed.

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
