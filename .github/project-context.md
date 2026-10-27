# LinkScope — Project Context

This document describes the software product and its functional requirements. The original assignment, including presentation and submission expectations, is retained in [the assignment brief](../docs/Quantum_Sky_Project_137_Software%20Engineering%20Assignment.md).

Presentation and interview preparation is tracked in [the interview preparation notes](../docs/slideshow/interview-preparation.md). Read and update that tracker when implementation status, production limitations, verification evidence, steering examples, or assignment clarifications change. It also contains the slide outline, panel-question log, demo checklist, and time record; it is not the final slide deck. Keep detailed interview material there rather than in the end-user README, and leave unverified findings or unrecorded time explicitly pending.

LinkScope is an application within Project 137, a division of Quantum Sky.

**Important: Keep it small. We scoped it to a few hours on purpose.**

## Product Goal

Build a small network-operations application that helps a team understand a European backbone and its connected operations sites and data centers. The application must answer:

1. Where are the network's single points of failure?
2. Which links carry the most traffic?
3. What happens to traffic when a node or link fails?

### Application delivery priority

The network application is the main deliverable; container/frontend scaffolding is supporting work. The [M6 application milestones](tasks/todo.md#m6-network-application-delivery) divide implementation into validated data (R1-R4), routing/utilization (R5-R6), failure analysis (R7-R8), the JSON API, the coordinate-based map (R9-R10), and interactive fail/restore plus published-image verification (R11). Follow these acceptance gates before claiming application completion. Prefer the existing stack and small tested increments over further optional infrastructure work.

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

### Baseline routing implementation (M6b)

`linkscope/routing.py` exposes `route_traffic(topology)`. It builds an undirected NetworkX graph and restricts each demand's paths to transit-capable nodes plus that demand's endpoints. It enumerates complete unweighted shortest paths and assigns each `demand.units / path_count`; this is deliberately simple for the small assignment network, not an optimized large-network routing engine. No capacity weighting or equal-next-hop approximation is used.

The immutable result contains every link's load, computed utilization percentage, and explicit undeliverable demand records. `top_five` ranks by descending utilization with link ID as the deterministic tie-breaker, returning up to five links (including zero-load links if needed). Contributions are summed with `math.fsum`; retain full floating-point precision internally and round only for display. Routing does not mutate the input or perform failure simulation.

Run `uv run --locked python manage.py test linkscope.test_routing` for eight routing tests with hand-calculated expectations and real-network reproducibility. A three-path fixture proves an 8/4 split at unequal next-hop branches for a 12-unit demand, and a 10-unit variant checks fractional conservation. Real-input checks also verify the single-attached OPS-WEST carries exactly 20 units and DC-NORTH's access links carry 110 units in total.

Measured baseline: all 391 demands are deliverable. Top-five values and verification evidence are recorded in the interview notes. API exposure, map rendering, and failure analysis are not implemented by M6b.

### Single failures and criticality (M6c)

`linkscope/failures.py` exposes `analyze_failure(topology, Failure("node" | "link", id))` and `analyze_all_failures(topology)`. Invalid kinds/identities raise `ValueError`. A node failure removes that node and its incident links; its endpoint demands are retained separately in `failed_endpoint_demands`. The remaining demands are routed with M6b's transit restrictions, with other undeliverable demands in `routing.undeliverable` and every overloaded remaining link in `overloaded`.

Criticality reasons are `disconnected`, `undeliverable`, and `overloaded`; any one makes the element critical. Failed-endpoint demands count as undeliverable for criticality, not just transit losses. Disconnection means more than one component among surviving nodes, including isolated nodes; zero/one surviving node is not disconnected. Physical connectivity is distinct from legal routing connectivity because endpoints cannot carry transit traffic. Overload is strictly load greater than capacity; exactly 100% is not overloaded.

The original topology is never mutated. Restoration means routing the original topology again, not updating shared server state. All-failure evaluation returns all 37 node and 55 link reports in deterministic node-then-link ID order. No caching, background service, new dependency, or API endpoint was added.

Run `uv run --locked python manage.py test linkscope.test_failures` for twelve tests covering hand-calculated disconnection, separate failed endpoints, rerouting/overloads, strict capacity thresholds, legal-route loss despite physical connectivity, combined criticality reasons, invalid IDs, restoration, and reproducible evaluation of all 92 real failures. Measured criticality: 37 nodes and six links; detailed findings and the failed-endpoint interpretation are recorded in the interview notes. API exposure is implemented in M6d below; UI exposure remains pending.

### Network JSON API (M6d)

Backend M6a-M6d is intended for one PR; frontend M6e-M6f follows in a separate PR. Complete one milestone at a time and pause for user review.

`linkscope/network_api.py` adds two read-only endpoints without changing the existing `/api` greeting:

| Request | Response |
|---|---|
| `GET /api/network` | `nodes`, `links`, `demands`, `baseline`, `criticality`. No query parameters accepted. |
| `GET /api/analysis` | Baseline analysis; also serves as restore (no stored failure state). |
| `GET /api/analysis?kind=node&id=Hamburg` | Analysis with Hamburg removed, including its incident links. |
| `GET /api/analysis?kind=link&id=L12` | Analysis with just L12 removed. |

JSON contract (field names are the frontend integration contract):

- Node: `id: string`, `kind: string`, `longitude: number`, `latitude: number`, `transit: boolean`.
- Link: `id: string`, `source: string`, `target: string`, `capacity: number`.
- Demand: `id: string`, `source: string`, `target: string`, `units: number`.
- Link load: all link fields plus `load: number`, `utilization_percent: number` (0-100 percentage scale, not a fraction; values may exceed 100).
- Analysis: `failure: null | {kind: "node" | "link", id: string}`, `links: LinkLoad[]`, `top_five: LinkLoad[]`, `undeliverable: Demand[]`, `failed_endpoint_demands: Demand[]`, `overloaded: LinkLoad[]`, `disconnected: boolean`. Baseline has a null failure and no failed-endpoint demands; failed elements/incident links are absent from failure load results, while `/api/network` retains the full baseline topology for drawing.
- Criticality entry: `kind: "node" | "link"`, `id: string`, `critical: boolean`, `reasons: string[]` using the M6c reason codes. `/api/network` includes all 92 entries, including noncritical elements with empty reasons.

Python `TypedDict` definitions cover nodes, links, demands, loads, failure descriptors, criticality entries, analysis, and the complete network payload. Payloads use explicit field construction and failure kinds use literal node/link types. Six API tests check field shapes and real values. `HEAD` is supported; other methods are rejected before work with JSON 405 and `Allow: GET, HEAD`. The strictly read-only views have the same narrow CSRF exemption as the greeting; other views retain middleware protection. All responses are non-cacheable.

Errors use `{"error": "..."}`: malformed/partial/unknown/repeated query parameters return 400, unknown element IDs 404, local `InputError` 503 (including file/row details), and NetworkX errors 500 with a generic client message. Input/analysis failures are logged with traceback; no broad exception catch or success-shaped fallback is used. This is a local-only unauthenticated API, not safe for public exposure.

Each request loads the local inputs and computes its own result; no per-user state, database, cache, or additional dependency is introduced. `/api/network` computes criticality on demand for the small network; it is intended for initial page loading, not every selection change. `/api/analysis` computes only the requested baseline/failure. Test with `uv run --locked python manage.py test linkscope.test_network_api`.

M6d image verification (2026-10-27): both Linux AMD64 targets built successfully using the laptop's Docker Desktop engine, and the complete image smoke script passed, including the new topology/criticality and L12 failure HTTP checks through production Gunicorn. Temporary containers were removed; the running devcontainer was not stopped.

For Docker-outside-of-Docker, `.github/ci/test-images.sh` accepts `LINKSCOPE_TEST_WORKSPACE` (the workspace path on the Docker host), `LINKSCOPE_TEST_HOST` (for example `host.docker.internal`), `LINKSCOPE_TEST_DEVELOPMENT_PORT`, and `LINKSCOPE_TEST_PRODUCTION_PORT`. Defaults remain the current working directory, `127.0.0.1`, 2158 and 2159 for CI. Use unused ports such as 22158/22159 to avoid the running application. HTTP probes send `Host: localhost` to preserve Django's local host restrictions, and published ports remain loopback-only. Both test containers explicitly select Linux AMD64.

## User Interface

- **M6e implementation:** `frontend/src/NetworkWorkspace.tsx` displays the baseline `/api/network` response; `NetworkMap.tsx` uses Leaflet 1.9.4 directly (no React map wrapper), with locked `@types/leaflet` 1.9.22. The backend and greeting endpoint are unchanged. Leaflet loads inside an effect for browser-only initialization, with teardown for StrictMode/unmount and size observation to refit on responsive layout changes. No failure/restore controls yet (M6f).
- React validates the network response shape, finite coordinates/numbers, IDs/references, load records and complete criticality entries before rendering. Aborted/unmounted requests cannot update state. Invalid contracts/HTTP errors are visible; no hardcoded results or fallback success. The findings and empty-network states can render without initializing the map.
- The basemap uses `https://tile.openstreetmap.org/{z}/{x}/{y}.png`, with visible linked attribution, browser-default tile caching, no prefetch/offline download and no key. Tile images explicitly use `referrerPolicy: "strict-origin-when-cross-origin"` so the browser sends an origin referrer despite Django's same-origin response policy. This is a local-demo choice, subject to the [OSM tile policy](https://operations.osmfoundation.org/policies/tiles/), not a guaranteed production tile service. Ordinary browser tile requests go to a third party; topology and analysis remain on the same-origin API. A tile error shows a warning while preserving overlays and findings.
- Nodes use API latitude/longitude and distinct symbols; critical nodes have `*`, critical links dashed lines, top-five links thicker strokes plus numbered labels. The legend and HTML findings give non-color equivalents. Lists explain failed-endpoint criticality rather than implying all 37 critical nodes disconnect the graph. Site positions are approximate backend offsets; use map zoom for dense labels. The map fits node bounds with 24px padding and quarter-level zoom snapping/steps, avoiding whole-level rounding that leaves excess surrounding geography. Each normal +/− click changes scale by about 19%, rather than doubling/halving it.
- At viewport widths of 768px and above, stacked findings occupy the left column and the map the wider right column; below 768px, panels stack with the map first. Critical elements precede the informational utilization table in both document and visual order. The workspace heading/subtitle align over the left column, with right-aligned network and criticality totals over the map in the same header row. Below 768px, the header stacks and totals align left. Totals render only after the network loads. The shell uses up to 96rem of width with compact introductory spacing and a viewport-aware map height. Browser checks at 1440, 1024, 768, 767 and 390px verify the breakpoint and no page-level horizontal overflow; Leaflet refits when the map size changes. The separate header-summary regression brings the frontend suite to 12 passing tests.
- Leaflet CSS is bundled through `main.tsx`; esbuild's `.png` file loader emits its referenced images into `dist/assets`. The clean-build test verifies those images exist. Tests use Node's existing runner and server rendering; no new DOM-testing dependency.
- Verification: 11 frontend tests, lint, type-check/build, plus real-browser desktop/narrow checks, 37 markers/55 line overlays, five rank labels and API-aligned values. Blocked tiles left results usable; forced HTTP 503 and malformed JSON contracts displayed explicit errors and recovered after restoring the route. The AMD64 production image builds with the new bundle, and `.github/ci/test-images.sh` passes for development/production using the host-Docker workspace override and ports 22158/22159 (leaving the active devcontainer's 2158 alone); temporary smoke containers are removed. No frontend simulation or published-image M6f claim.

- Display the network as a map based on the backbone city coordinates.
- Place each site near the node or nodes to which it attaches.
- Make critical nodes and links and the five most utilized links visible.
- Do not communicate criticality or utilization using color alone; provide another visual cue or textual indicator.
- Support interactive failure and restoration of nodes and links, with results shown in the current page.

### Visual palette

Retain the initial frontend/favicon palette for visual consistency:

| Color | Hex | Role |
|---|---|---|
| Dark slate | `#17212b` | Primary text on light backgrounds; favicon background. |
| Off-white | `#f5f7fa` | Page background; favicon network nodes. |
| Light blue | `#7dd3fc` | Network/accent strokes on dark backgrounds; favicon links. |
| Muted white | `#cbd5e1` | Footer text on the same dark slate background as the header. |

The palette is defined by the current [frontend stylesheet](../frontend/src/styles.css) and shared [logo](../frontend/src/logo.svg). The same SVG is used for the header logo and browser favicon; `/favicon.ico` redirects to `/assets/logo.svg`. The responsive shell has a dark branded header, open main workspace, and footer with local-demo context. Keep the API greeting visible until its integration-proof role is replaced by application functionality. Light blue is an accent, not body text on the off-white background; verify contrast for any new foreground/background pairing. Future criticality, utilization, and error colors must remain distinguishable and accessible, with labels or shapes as well as color. Semantic status colors have not yet been selected.

## Data Loading Design

Decision recorded on 2026-10-23; M6a loader implemented and verified on 2026-10-27.

- Use TopoHub 1.5.1, pinned in `pyproject.toml` and `uv.lock`. This selects Python for the backend.
- Provisionally use a local `nobel-eu.txt` obtained from the [sikorski-as/sndlib native-text mirror](https://raw.githubusercontent.com/sikorski-as/sndlib/master/native/nobel-eu/nobel-eu.txt). This is a temporary source choice while the project owner contacts Quantum Sky about the unavailable official inputs. Official provenance and permitted use remain unresolved.
- Preserve the downloaded file unchanged and record its source, retrieval date, source revision, and checksum. Do not fetch it at application startup or silently fall back to another dataset.
- Do not use TopoHub's bundled JSON as the application's input. Use an application-owned `LocalSNDlibGenerator` subclass of `topohub.providers.sndlib.SNDlibGenerator` to read our local native-text file instead of downloading it.
- The loader must accept both the backbone file and `sites.csv`, returning a single merged topology object. Extend the earlier local-file prototype with CSV validation and merging; overriding `download_topo()` alone is not sufficient.

### Local loader responsibilities

1. Validate the backbone input before delegating to TopoHub's native-text parser. Invalid data must produce an error identifying the file and row; raw parser exceptions are not sufficient.
2. Retain backbone link identities and assign each backbone link a capacity of 550 units. TopoHub's parser does not retain link IDs or capacities, so the application adapter must preserve and associate these with the parsed edges.
3. Read `sites.csv` with the columns `site_id`, `site_type`, `attaches_to`, and `access_capacity`. Validate required values, supported site types, unique node IDs, and positive numeric capacities.
4. Register all site nodes before resolving attachments, allowing a site to reference another CSV row regardless of row order. Resolve each semicolon-separated attachment to a backbone city or site; reject unknown references, self-links, and duplicate attachments with file-and-row errors.
5. Create one undirected access link per attachment with the row's capacity. Preserve site types and mark only backbone cities and aggregation hubs as transit-capable. Assign site positions near their attachments for display.
6. Add 10 units between each operations site and each data center, plus 50 units between the two data centers, recording each undirected demand once.
7. Return the merged topology with nodes, links, coordinates, capacities, site types, transit eligibility, and demands. Keep node identifiers consistent across all records so city-name attachments resolve correctly even though TopoHub initially assigns integer node IDs.
8. Verify the baseline totals: 37 nodes, 55 links, and 391 demands totaling 2,068 units. Test backbone parsing, CSV merging, validation errors, and those exact totals.

Keep this adapter separate from routing and failure analysis. Recompute utilization from the merged network using the application's required routing rules; do not rely on TopoHub's precomputed loads.

Implementation: `linkscope/topology.py` exposes `load_topology(backbone: Path, sites: Path)` with defaults pointing to the two separate files under `data/`. It returns frozen `Topology`, `Node`, `Link`, and `Demand` records. Links/demands are undirected records stored once; original backbone IDs are retained and generated access/demand IDs are namespaced. Site coordinates are deterministic offsets near the nearest reachable backbone anchors, independent of CSV row order. No input is rewritten.

Native-format records are validated before the pinned TopoHub parser receives a normalized in-memory copy; this preserves precise source-file/physical-row diagnostics while accommodating the parser's formatting assumptions. The loader currently supports the supplied native format with `UNLIMITED` demand path lengths, not XML or arbitrary SNDlib extensions. Unsupported records fail explicitly. Missing/unreadable files report row 1. `InputError` is raised to the caller, never converted into an empty topology.

Verify from the repository root:

```sh
uv run --locked python manage.py test linkscope.test_topology
uv run --locked python -c 'from linkscope.topology import load_topology; t = load_topology(); print(len(t.nodes), len(t.links), len(t.demands), sum(d.units for d in t.demands))'
```

Measured output: `37 55 391 2068.0`. Eight loader tests cover real totals/checksum, explicit expected generated demand endpoints, capacities/transit roles, synthetic merge arithmetic, file/row diagnostics, CSV reordering, and byte-for-byte input preservation. The snapshot revision/retrieval/checksum and unresolved provenance/permitted-use status are recorded in [data documentation](../data/README.md). This is a callable backend loader; API integration and routing remain later milestones.

## Backend Framework Decision

Decision recorded on 2026-10-23; Django now serves a React/API greeting demonstration. Network analysis and the map remain pending.

Use native Django for the Python backend and serve the application's JSON endpoints through Django views. Its built-in authentication, sessions, ORM, migrations, and administrative interface remain available for future needs, but are not required features of the initial version. FastAPI is not part of the selected stack, and no additional API framework (such as Django REST Framework or Django Ninja) has been selected.

### Why Django rather than FastAPI

- The original decision anticipated database-backed user authentication and protected API access. Django supplies that infrastructure together, reducing integration work compared with assembling equivalent components. Authentication has since been deferred for the initial version; retain the selected framework rather than spending the limited implementation time revisiting it.
- FastAPI is a valid alternative, with strong typed validation and automatic OpenAPI support, but it would require additional choices and integration for equivalent local user management, database models, migrations, and administration.
- Combining Django and FastAPI would introduce a second request-handling framework and explicit authentication integration without a current requirement that justifies the extra complexity.
- The [job description](../docs/job-description.md) names Django, FastAPI, or a comparable framework; Django therefore aligns with the role without needing to demonstrate both frameworks.
- This is a simplicity and delivery-scope decision, not a claim that FastAPI is less secure or incapable of meeting the requirements.

### Authentication and persistence scope

The decision below supersedes the earlier plan to include user accounts and database-backed sessions in the initial version. Defer authentication and application database persistence for the local-only demonstration. Network topology continues to come from local backbone and site files. No database service is needed for the initial application; a future internal release can select a relational database when introducing accounts and sessions.

The initial API is unauthenticated and must not be exposed to shared or public networks. Publish container ports on host loopback only. Before an internal release, protect network-analysis API endpoints with explicit authentication and authorization checks. Native Django authentication does not make every view private automatically. Browser session authentication must retain CSRF protection for unsafe requests, including login. Authentication restricts access but does not replace rate limiting or other abuse controls.

## Production Concern Priorities

Decision recorded on 2026-10-23. These are implementation commitments, not claims of completed functionality. The assignment asks what was implemented, why anything was deferred, and what a first internal release would require, explicitly preferring "two done well to six done badly."

Focus on **input validation and error handling** and **dependency and security checks**. Validation directly supports R2 and the credibility of the network results. Supply-chain checks address the third-party package, provisional dataset source, frontend dependencies, and container image without expanding the application into a larger platform.

| Concern | Initial version and rationale | First internal release |
|---|---|---|
| Input validation and error handling | **Priority.** Validate backbone and CSV inputs with file-and-row errors, IDs and references, positive capacities, and valid demand values. Validate API requests and failure selections; return clear errors without partial success or exposed tracebacks. Test invalid inputs and the exact baseline totals. | Retain those tests and review error responses and validation against the actual deployment and input sources. |
| Dependency and security checks | **Priority.** Pin dependencies, record the dataset source revision and checksum, automate Python and frontend dependency vulnerability checks, and scan the production container. Review actionable findings and document justified exceptions; adding a scanner alone is not completion. Specific tools remain to be selected. | Run checks in the release pipeline, assign responsibility for remediation, and establish recurring dependency and base-image updates. Confirm dataset provenance and permitted use. |
| Authentication and access control | **Deferred.** Not an R1-R11 requirement. Local-only demonstration access avoids account-management scope within the few-hour budget; this is not suitable for shared or public deployment. | Add Django authentication, explicitly protected API views, least-privilege authorization, session/CSRF controls, and access-control tests before admitting shared users. Select account provisioning or company identity integration and the required persistence then. |
| Logging | **Basic diagnostics only; production observability deferred.** Preserve explicit error reporting and useful server diagnostics, but do not build centralized logging or an audit system for the local demonstration. | Add structured request/error logs, correlation identifiers, appropriate redaction, authentication/security events, and a documented collection and retention policy. |
| API versioning | **Formal compatibility policy deferred.** One frontend and backend are developed and delivered together, with no established external clients. Do not add parallel API versions or compatibility machinery speculatively. | Define and document a stable versioned API contract and deprecation policy before supporting independent clients or breaking changes. |
| Configuration and secrets | **Basic safety retained; production secret management deferred.** Do not commit credentials or bake secrets into images. Keep configuration explicit, report invalid configuration, and avoid production credentials for a local demonstration. A managed secret service and environment provisioning are outside the initial scope. | Supply secrets through the deployment's approved mechanism, validate required settings, disable debug responses, configure allowed hosts and HTTPS/cookie settings, and document rotation and environment separation. |

Document the actual implementation status and remaining deployment limitations when delivering the application. Deferring a production concern does not waive basic safe defaults or the requirement for maintainable code.

## Container Infrastructure Decision

Decision recorded on 2026-10-23; the Dockerfile and devcontainer foundations package the initial Django scaffold.

- Package the application as a Docker image for production.
- Use a devcontainer for development, built from an image defined by the project's Dockerfile.
- Define development and production build targets in the same multi-stage Dockerfile. Both targets derive from a common base stage, sharing the runtime foundation and common dependencies rather than maintaining separate Dockerfiles.
- Add development-only tools in the development target; do not include them in the production target. Production is a sibling of the development target, not downstream of it.
- The current scaffold has `base`, `development`, and `production` stages. The approved bundled frontend design below adds a Node build stage for actual compilation while preserving the existing development and production targets.
- Configure the devcontainer to build the `development` target, mount the workspace at `/app`, and run as `app`; production builds select the `production` target and copy application files directly into the image. The devcontainer uses the Dockerfile's long-running development command and aligns the `app` UID/GID with the host where supported so the bind-mounted workspace remains writable.
- Keep devcontainer lifecycle hooks separate: `post_create.sh` handles setup after creation, while `post_start.sh` handles repeatable startup work. Adapt their contents to LinkScope rather than copying CakePHP-specific ownership, paths, or personal agent configuration.
- The reference illustrates the container structure, not a requirement to adopt its PHP/Apache runtime, optional tools, credential mounts, or installation scripts.
- Use `ghcr.io/astral-sh/uv:python3.13-bookworm-slim` directly as the common base, without a build argument or digest pin. The project owner accepts the mutable tag to keep the Dockerfile simple. This selects Python 3.13, Debian Bookworm slim, and uv. Manage exact direct dependency versions in `pyproject.toml`, with a committed `uv.lock`; the devcontainer syncs dependencies on creation and production installs locked runtime dependencies during its image build.
- Development adds Git, GitHub CLI (`gh`), curl, and CA certificates through Debian packages and stays running for workspace attachment. Both targets define the common `app` user (UID/GID 10001); the devcontainer may align that user's UID/GID with the host for writable workspace mounts. Development owns `/app`; production restores root ownership of its application directory and files so the runtime user cannot modify them. Production does not inherit development tools. The image smoke test checks `gh --version` in the development target. GitHub CLI authentication is separate from VS Code sign-in; use `gh auth login` interactively when required, and never bake credentials into the image.
- The `app` user's home is `/home/app`, created and owned by that user, while the working directory and bind-mounted workspace remain `/app`. The devcontainer mounts a named volume (`linkscope-home-${devcontainerId}`) at `/home/app` so home-relative IDE files and tool caches persist across normal rebuilds. The host-mounted workspace also survives rebuilds; removing the named volume deletes its home data.
- The legacy `.cache`, `.copilot`, `.vscode-server`, `.dotnet`, and `.gitconfig` entries were migrated to the home volume and removed from `/app` after content verification. Sixteen differing or missing originals (runtime state and old session locks) are preserved under `/home/app/.workspace-home-backup` without replacing current home state. The one-time migration hook and obsolete workspace ignore entries have been removed. Project files, `.env`, and `.venv` remain in `/app`.
- Django 6.1.2 and TopoHub 1.5.1 are direct dependencies. TopoHub 1.5.1 does not declare NetworkX, which its SNDlib provider imports, so NetworkX 3.7 is also pinned directly. Gunicorn 26.2.0 serves `linkscope.wsgi:application` on `0.0.0.0:2158` in the production image, logging requests to stdout. Its unused control socket is disabled so it does not write under the root-owned application directory. WhiteNoise 6.12.0 serves bundled frontend assets; the homepage fetches a greeting from the JSON API. Network analysis remains pending.
- `.dockerignore` excludes local environments, secrets, Git metadata, and assignment/agent documentation from the build context.
- The shared Docker stage overrides the base image's OCI title, description, URL, documentation, and source with LinkScope metadata. Image smoke tests verify the title and description on both targets; publishing a new image supplies the corrected description to GHCR.
- Compose is the local published-image run path. Production orchestration is not selected; container packaging does not itself select Kubernetes or a cloud platform.

### Bundled frontend and API decision

Approved on 2026-10-27; M1 build tooling and M2 same-origin serving/browser proof are implemented. CI Docker builds and container HTTP checks have passed; published-image Compose/browser verification remains pending. See the [implementation milestones](tasks/todo.md#bundled-frontend-and-api-milestones).

- Keep one repository, one Dockerfile, and one deployed application container. React/TypeScript runs in the browser; its compiled HTML, JavaScript, CSS, and other assets are static files shipped with the Python application.
- Retain Gunicorn in production with Django routing and an appropriate static-file mechanism; Gunicorn alone does not serve static files. No Apache, nginx, reverse proxy, CORS configuration, or separate frontend deployment is needed.
- Serve React at `/` and the REST API at `/api` and its subpaths on port 2158. Use relative API URLs. Preserve explicit API errors and missing-asset responses rather than routing them into the frontend HTML fallback.
- M2 must first prove the minimal integration: `GET /api` returns `{"message": "Hello, world!"}` as JSON, and React fetches and displays that message at `/` with loading and explicit failure states. Verify the actual browser round trip before network-application integration; repeat the proof through the production Gunicorn image and Compose in M4-M5.
- Add a Node frontend build stage and Node/npm tooling in the development target. The production runtime receives the compiled assets, not Node/npm. Preserve the workspace mount, development lifecycle hooks, runtime secret handling, and non-root production permissions.
- Support `npm run build` and a build-watch command inside the devcontainer. Rebuilt assets are served by Django on `http://127.0.0.1:2158/`; manually refresh the browser. Do not add Vite, a separate frontend development server, or HMR. Select minimal build tooling and record exact working directories and commands when implemented; avoid stale asset caching in development.
- Commit authored frontend source/assets, dependency manifests, the npm lockfile, and build configuration. Ignore `node_modules`, compiled bundles, and collected static output in Git. Docker/CI must build from source without relying on ignored workspace artifacts.
- Keep the existing single application CI flow with no path filters, adding frontend lint, type checks, tests, and builds. Frontend-only edits rebuild the bundled image. Preserve existing branch/tag publishing rules and the Linux AMD64/emulation decision.
- Compose continues to pull the published image; workspace edits are visible through the devcontainer, not through published-image Compose without rebuilding and publishing.
- Future evolution, not current work: separate frontend (Node build/nginx runtime) and Django API images in the same repository/Compose project when independent releases or scaling justify it. Only then consider per-image path-filtered CI. If team ownership and release cadences diverge further, consider separate frontend/backend repositories plus an IaC/orchestration repository pinning environment image versions. Cross-repository API changes require explicit compatibility discipline.

### Frontend build and validation

Third-party Actions use Node's default warning behavior: warnings remain visible in job logs without failing otherwise successful actions. At the user's request, the workflow-level fatal Node-warning guard was removed on 2026-10-27. Do not suppress warning output or bypass actual action failures with `continue-on-error`. The frontend checked-command diagnostic policy is unchanged.

Run 40453771963 successfully built/tested both Docker targets, checked frontend/assets/API HTTP responses, published `:dev`, and completed cleanup. However, `download-artifact@v8` emitted Node's `Buffer()` deprecation warning. Run 40455416000 subsequently passed the full test job, including both image builds, container HTTP/permission/tooling checks, and production-image export/upload. Its publication failed because the former guard threw on `download-artifact@v8.0.2`'s `DEP0005` warning. Pinning v8.0.2 did not fix that upstream warning. The guard is now removed, leaving warnings logged without a custom extraction workaround; hosted publication still needs verification. Published-image browser testing through Compose remains unverified.

The `frontend/` directory contains the React/TypeScript shell, authored HTML/CSS, and locked npm dependencies. Use Node.js 24 LTS and npm. esbuild bundles assets, TypeScript checks types, Biome checks lint/format, and Node's test runner with `tsx` runs component and build tests. No Vite or frontend web server is used.

The npm `allowScripts` policy approves only the locked `esbuild@0.28.2` install script, which sets up and validates its platform-specific executable. Review that approval when upgrading esbuild; do not approve all dependency scripts. Use Node 24's bundled npm without a separate npm upgrade or version pin. The frontend `.npmrc` disables only npm's newer-version notification (`update-notifier=false`), an explicitly accepted exception to diagnostic enforcement. Docker copies this configuration before `npm ci`; CI runs from the frontend directory. Other Node/npm warnings and notices still fail checked validation, and audit output remains enabled.

From the repository root:

```sh
cd frontend
npm ci
npm run build
```

Output is `frontend/dist/index.html`, `frontend/dist/assets/app.js`, and `frontend/dist/assets/app.css`. The HTML references `/assets/` URLs for later same-origin Django serving. Generated output, `node_modules`, and the reserved root `staticfiles/` collection directory are ignored by Git and excluded from Docker's source context. Production must regenerate frontend output in its build stage rather than copying local output.

For iterative builds, run `npm run watch` from `frontend/`. It builds immediately and watches imported TSX/CSS plus the HTML entry and shared logo, writing development bundles and printing build errors. It starts no HTTP server and does not type-check continuously; run `npm run typecheck` separately. Django serves these assets: manually refresh `http://127.0.0.1:2158/` after a successful rebuild.

The devcontainer's post-create hook installs locked dependencies and runs the initial type-checked build; its post-start hook starts the Python auto-reloading server. For day-to-day frontend edits, use these commands from the repository root:

```sh
# One-off, type-checked rebuild.
npm --prefix frontend run build

# Alternatively, keep this running while editing; stop with Ctrl+C.
npm --prefix frontend run watch
```

No image push, container rebuild, or second frontend server is needed for workspace edits. Watch mode remains running after a syntax error and rebuilds when it is corrected. Errors identify the source file and line; a failed watch build removes generated JS/CSS, so wait for an error-free rebuild before refreshing. A one-off build exits nonzero on type/syntax errors. After stopping watch mode, run the one-off build to restore production-mode bundles.

M3 verification on 2026-10-27 used image-installed Node 24.22.1 and bundled npm 11.19.1. A temporary heading edit appeared in the browser after an explicit build and manual refresh; a second edit appeared after a watch rebuild on the same port 2158, with no cache clearing. Intentional invalid syntax produced a nonzero explicit-build result and visible watch diagnostics; correcting it recovered automatically. Repeated post-start hooks preserved the working API. Temporary source edits were restored and the watcher stopped. Fresh devcontainer creation and an actual container restart remain unverified in this session because Docker is unavailable; existing dependencies were not reinstalled.

Validate from `frontend/` with `npm run lint`, `npm run typecheck`, `npm test`, and `npm run build`. `npm run format` applies Biome formatting and safe fixes. Tests cover server-rendered shell semantics, isolated source-only build output, watch rebuilds after component/CSS/HTML/logo edits, and watch failure/recovery. The automated build tests alone do not prove browser mounting, API integration, or Django static-file serving; the separate browser checks above cover the live development workflow.

The Dockerfile now uses `node:24-bookworm-slim` as its Node toolchain source. Development copies Node/npm from that stage; `post_create.sh` runs `npm --prefix frontend ci` and `npm --prefix frontend run build` after Python setup. The separate `application-build` stage runs locked `npm ci` and builds from source; production copies its `dist` output without Node/npm. Rebuild the devcontainer to obtain image-provided tools. The working container also has a separately provisioned Node 24 installation for local validation.

CI uses `actions/setup-node@v7` with Node 24 and lockfile-based npm caching, then runs `npm ci`, lint, type checks, tests, and build before image builds. Development smoke tests repeat these commands in a writable temporary copy because the workspace mount is read-only. Production smoke tests require the built HTML/JS/CSS and absence of Node/npm. Both targets have HTTP checks for frontend HTML, assets, greeting JSON, and missing API/asset 404s. These image checks passed on Actions in runs 40453771963 and 40455416000.

M4 verification on 2026-10-27 confirmed separate development/production targets, a clean frontend build excluding workspace bundles/dependencies, runtime-supplied secrets, UID 10001, non-writable production application files, and no Node/npm in production through the successful CI smoke tests. Compose configuration retains loopback-only publishing and explicit `linux/amd64`. A separate local Gunicorn process on port 2160 served HTML/JS/CSS/logo and displayed the fetched API greeting in a real browser, then was stopped. This local browser proof is not a production-image or Compose browser check; those remain pending on a Docker host. M5 also requires hosted publication validation after removing the fatal warning guard.

### Same-origin frontend/API serving

Django serves `frontend/dist/index.html` at `/` through a `FileResponse`. A missing HTML build is logged and returns HTTP 503; run `npm --prefix frontend run build` to generate it. WhiteNoise middleware serves `frontend/dist/assets/` at `/assets/` with debug disabled, including under Gunicorn. No general SPA fallback is currently needed: unknown page/asset paths return 404, and `/api/unknown` returns a JSON 404 rather than frontend HTML.

`GET /api` (also `/api/`) returns HTTP 200, `Content-Type: application/json`, and `{"message": "Hello, world!"}`; HEAD is supported and other methods return JSON 405 with `Allow: GET, HEAD`. Only this strictly read-only endpoint is CSRF-exempt so method rejection is consistent without a token; do not extend the exemption to state-changing functionality. CSRF middleware remains enabled for other views. Tests enforce CSRF checks explicitly. The React component fetches relative `/api`, validates the JSON message, and displays loading, success, or an accessible error. Unmounting aborts the request; failed requests do not show fallback success content.

HTML/API responses use `never_cache`. Unhashed JS/CSS use WhiteNoise `max-age=0` (revalidation), with file auto-refresh enabled in both environments for this local-only demo. This deliberately avoids long-lived production caching of fixed asset names and lets workspace builds appear without server restarts. Immutable hashed assets/optimized production caching are not implemented. Unit tests use isolated built-asset fixtures; frontend build tests separately verify actual output.

M2 verification on 2026-10-27: 11 Django tests, eight frontend tests, 31 CI-helper tests, lint/type checks, and builds passed. A real browser displayed the message from same-origin `/api`, showed errors for HTTP 503, invalid JSON contract, and network failure, and recovered after restoring the route. Desktop/mobile layout checks found no horizontal overflow; the shared logo loaded successfully. The footer reads "Quantum Sky · Project 137 · LinkScope" and "Local demonstration", using dark slate with muted white text. Gunicorn was separately started on loopback port 2160 and served HTML/JS/CSS/JSON successfully, then stopped. Review F1's CSRF/method-contract mismatch was addressed and regression-tested. This is not a Docker/Compose production-image verification.

### Django startup

Verification update (2026-10-27): the user confirmed the remaining M4/M5 checks on their laptop using `docker compose up -d` and marked the published-image/browser acceptance items complete. This supersedes the pending Compose/browser status recorded above. The selected image tag/digest was not recorded. A new hosted publication after removal of the fatal warning guard remains a separate, unverified check.

Run `uv sync --locked` to install dependencies. The devcontainer loads `.env.default` first and `.env` second through Docker's ordered `--env-file` arguments; values in `.env` override defaults. The template contains a public development-only placeholder key; `.env` is private and ignored by Git, and both files are excluded from image builds.

Before Docker starts, the devcontainer's host-side `initializeCommand` uses a POSIX shell to create an empty `.env` with owner-only permissions if absent. Existing contents and permissions are preserved. Fresh checkouts therefore use the public development-only defaults without manual setup. To override them, put a randomly generated `DJANGO_SECRET_KEY` in the private `.env`. Rebuild the devcontainer after changing either file; this configuration does not update an already running container's environment. No dotenv package or Django settings changes are needed.

Outside the devcontainer, supply `DJANGO_SECRET_KEY` through the environment before using Django or Gunicorn; an absent or blank value raises an explicit configuration error. For a temporary local session, generate an ephemeral key:

```sh
export DJANGO_SECRET_KEY="$(uv run python -c 'import secrets; print(secrets.token_urlsafe(64))')"
uv run python manage.py runserver 0.0.0.0:2158
```

The devcontainer forwards port 2158 and keeps its existing keep-alive command. Its `post_start.sh` hook starts the auto-reloading Django development server in the background, using a lifetime `flock` lock to prevent duplicate starts. Combined server stdout/stderr is appended to `/home/app/.cache/linkscope/runserver.log` and mirrored through `/proc/1/fd/1` to the container's stdout using `tee`, making it available to `docker logs` and configured container log collectors. This requires the main process's stdout to be writable by `app`; the hook fails explicitly otherwise. The hook checks HTTP readiness for up to 30 seconds and reports startup failures; repeat calls leave an existing server running. Debug responses remain disabled. Only `localhost`, `127.0.0.1`, and `[::1]` are allowed hosts. Authentication, administration, and database configuration are deliberately not enabled yet.

For the production image, with `DJANGO_SECRET_KEY` exported in the host shell:

```sh
docker build --target production -t linkscope:production .
docker run --rm -p 127.0.0.1:2158:2158 -e DJANGO_SECRET_KEY linkscope:production
```

Visit `http://localhost:2158/` for the React/API greeting demonstration. The key is runtime configuration, not an image-build input; do not commit it. Although Gunicorn is a production server, this unauthenticated scaffold remains a local-only demonstration, not a production-ready release.

With the key exported, validate with `uv lock --check`, `uv run python manage.py check`, and `uv run python manage.py test linkscope`. To smoke-test the production entry point without Docker, build the frontend, run `uv run gunicorn --bind 0.0.0.0:2158 --access-logfile - --no-control-socket linkscope.wsgi:application`, and request `/`, `/assets/app.js`, and `/api`.

### Container foundation validation

Published images currently target Linux AMD64. Compose explicitly selects `platform: linux/amd64`, and the README's Docker run alternative uses `--platform linux/amd64`. AMD64 hosts run natively; ARM64 hosts need AMD64 emulation (available in Docker Desktop). This keeps CI single-platform; it does not configure emulation on arbitrary ARM64 Linux hosts. The rationale, trade-offs, and revisit criteria are recorded in the interview preparation notes under "Container architecture decision".

The root `compose.yaml` runs the published production image, not a local build, with `pull_policy: always` and host port `127.0.0.1:2158:2158`. It adds no database, volumes, or development services and does not change the devcontainer. `LINKSCOPE_IMAGE_TAG` defaults to `main`; `DJANGO_SECRET_KEY` defaults to the public local-demonstration key. Compose reads overrides from the shell or the ignored root `.env`; it does not load `.env.default`. Start with `docker compose up -d`, follow logs with `docker compose logs -f`, and remove the container with `docker compose down`. Validate interpolation with `docker compose config --quiet` and `LINKSCOPE_IMAGE_TAG=dev DJANGO_SECRET_KEY=compose-validation-only docker compose config`; do not share rendered configuration containing real keys. On a Docker host, verify startup and HTTP 200 at `http://localhost:2158/`, then shut down with `docker compose down`.

Build targets with `docker build --target development -t linkscope:development .` and `docker build --target production -t linkscope:production .`. Smoke-test Python and uv using explicit commands, for example `docker run --rm linkscope:production uv --version`. Verify both images define UID 10001, with `/app` writable in development and non-writable in production. The devcontainer may adjust the effective development UID/GID to match the host workspace. These checks validate the image foundation, not application behavior. Also verify the devcontainer opens the workspace at `/app` and runs both lifecycle hooks.

## GitHub Actions and Image Publishing

Branching model: `dev` is the persistent development branch, `main` is the persistent stable branch, and Git tags are production releases. Feature branches open PRs into `dev`, or directly into `main` for hotfixes; `dev` is promoted to `main` through a PR.

`.github/workflows/ci.yml` runs for same-repository pull requests targeting `main` or `dev`, pushes to `main`, and tag pushes. Pushes to `dev` or any other branch run nothing; work there is validated only through PRs. A PR sourced from `dev` (normally `dev` → `main`) publishes `dev`. PRs sourced from `main` (for example syncing a hotfix into `dev`) are test-only because `main` publishes from its own pushes. Fork PRs are skipped by a job-level condition before any runner starts, so they consume no Actions minutes. Published releases reuse their tag-push image rather than triggering duplicate builds.

The test job installs locked dependencies with Python 3.13 and uv 0.9.30, runs Ruff lint/format checks, ShellCheck, CI-helper unit tests, Django checks and application tests, and builds both Docker targets. `.github/ci/test-images.sh` tests the development startup hook (including repeated invocation), verifies HTTP **200** for development and production, runs Django checks/tests inside both containers, and checks production identity, file permissions, and exclusion of local secrets/Git metadata. Both HTTP endpoints are published on runner loopback only. A random ephemeral secret key is supplied at runtime; no deployment secrets are needed.

Only after those checks pass is the tested production image transferred as a one-day workflow artifact to a separate publishing job. That job uses `GITHUB_TOKEN` with package write permission; the build job has read-only repository permission and no publishing credentials. Production tags are:

- Feature PR into `dev` or `main`: `ghcr.io/fr3nch13/qsp137sa:<source-branch>`.
- PR from `dev` (development environment): `ghcr.io/fr3nch13/qsp137sa:dev`.
- Push to `main` (stable): `ghcr.io/fr3nch13/qsp137sa:main`.
- Git tag: `ghcr.io/fr3nch13/qsp137sa:<tag>`.

Branch names are lowercased, invalid Docker tag characters become hyphens, and leading dots/hyphens are removed (`feature/web-ui` becomes `feature-web-ui`). Invalid/overlong tags fail instead of being silently truncated. Normalization collisions with existing branches, the reserved `main`/`dev` tags, or release tags fail explicitly; Git tags named `main` or `dev` are rejected. Release tags must be SemVer versions without a `v` prefix or `+build` metadata (for example `2.4.11` or `2.5.0-rc.1`); the workflow only triggers on SemVer-shaped tags and `image_tag.py` validates them strictly. They must not collide with branch image tags. OCI labels record the source repository, revision, ref, and unique workflow run so separate publications do not normally share an image version.

`.github/workflows/delete-image.yml` runs on branch/tag deletion and removes matching GHCR versions, if present. It uses trusted code from `main`, directly queries the known package's versions without listing the owner's package inventory, paginates package versions, and refuses to delete a version carrying any other tag. `main` and `dev` image tags are protected from automatic deletion. Missing tags are no-ops; missing/inaccessible packages and other API errors fail explicitly with the response body logged, since a 404 does not distinguish an absent package from insufficient access. The workflow retains `GITHUB_TOKEN` with `packages: write` and requires package-side Actions admin access. Deletion cancels an in-progress workflow for the same ref, and publishing also verifies that the source Git ref still exists.

After each successful publication, CI runs `.github/ci/cleanup_untagged_images.py` in a separate cleanup job. Cleanup runs are serialized across refs. The script collects all package-version pages before deleting anything, then rechecks each candidate and deletes versions still carrying zero tags whose GHCR `updated_at` timestamp is at least 24 hours old. The cutoff is fixed at cleanup start in UTC. This is a last-update age buffer, not a guarantee of 24 hours since a tag was removed; GHCR does not expose a separate untagged-since timestamp. Tagged branch/release images remain, but deleted images cannot subsequently be pulled by digest. Eligible versions wait until the next successful publish cleanup; there is no scheduled daily run. API and permission failures fail the job rather than reporting success. This policy assumes the current single-platform `docker push` publisher; revisit it before introducing image indexes or attestations with referenced untagged manifests.

For a one-time backlog cleanup, run `python .github/ci/cleanup_untagged_images.py` from the repository root with GitHub CLI credentials granting `read:packages` and `delete:packages` and package admin access. This deletes eligible untagged versions using the same 24-hour last-update buffer; it is not a dry run.

The repository must have Actions enabled and package creation/write permission in GHCR. The package must grant this repository's Actions token **admin** access for deletion; source labels link new packages to the repository, but existing package permissions may need adjusting. A first package publication can require owner/organization approval. The delete workflow must exist on the default branch (`main`). GitHub does not emit deletion events when more than three tags are deleted at once; delete tags individually when automatic cleanup is required.

For local validation, run `uv sync --locked`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run python -m unittest discover -s .github/ci -v`, and ShellCheck on `.devcontainer/*.sh` and `.github/ci/*.sh`. Validate workflows with actionlint. To reproduce image checks on a Docker host, build `linkscope:development` and `linkscope:production` from their matching targets, then run `bash .github/ci/test-images.sh` from the repository root. Docker image builds, GHCR publication, and deletion require validation on a suitable Docker/GitHub environment; static/local application checks alone do not prove them.

## Technology and Runtime Constraints

- Backend: Python with native Django and TopoHub (the assignment permits Python or Go).
- Frontend: TypeScript; React is optional. Use port `2158` for the Web UI and forward it through the devcontainer.
- Libraries may be used as appropriate.
- Database: Application persistence and a database service are deferred with authentication; local files supply the network inputs.
- Packaging: Docker, with development and production targets sharing a common base in one Dockerfile; development uses a devcontainer.
- Provide one documented command to start the application.

## Scope Boundaries

The assignment explicitly says: **"Keep it small. We scoped it to a few hours on purpose."** Treat this as an implementation constraint, not just background context.

- Prioritize a working end-to-end application satisfying R1-R11, with focused correctness tests, the two selected production concerns, and the agreed container setup.
- Use framework defaults and the simplest design that meets the requirements. Do not turn the selected stack into a broader platform: no speculative services, abstraction layers, optional integrations, or deployment infrastructure.
- Defer authentication and database persistence for the local-only demonstration; do not expand into an identity-management product.
- Apply the reference Dockerfile's structure without importing its unrelated tooling or complexity.
- Treat production quality as correctness, clear errors, safe defaults, and maintainable code within this small scope, not a requirement to implement every production concern. Explicitly document deferred concerns and limitations.

The deliverable is a first, small working network-analysis application. Keep implementation choices (including framework, internal architecture, and algorithms beyond the specified behavior) aligned with the requirements and avoid adding unrequested product scope. Assignment-specific presentation, AI workflow, repository submission, and follow-up session expectations are documented in the [assignment brief](../docs/Quantum_Sky_Project_137_Software%20Engineering%20Assignment.md).

## Repository Scope and README

Outside `./docs/` and `./.github/`, all project files—including the root `README.md`—are part of the production-level application scope. Treat application code and user-facing materials as production-quality deliverables, not scratch work or assignment-only artifacts.

The README is for end users. Keep it focused on the product overview, implemented capabilities, and supported user-facing options. Describe options at a high level; do not put internal architecture, source file paths, environment variable names, development commands, or CI/CD implementation details there. Be accurate about what is and is not available, and document how to use the application once it is runnable. Keep development setup, architecture, exact configuration, validation commands, and release mechanics in `.github/project-context.md` and `.github/tasks/*.md`.

## Assignment Clarifications and Resolutions

### Unavailable official backbone inputs

- **Unclear:** Whether the assignment's SNDlib download failures are intentional and which alternative source is acceptable. On 2026-10-23, normal requests failed TLS hostname verification; diagnostic requests bypassing that check returned HTTP 404 for both assigned files. Bypassing TLS verification therefore did not resolve the missing inputs.
- **Decision:** Proceed provisionally with a local `nobel-eu.txt` from the [sikorski-as/sndlib mirror](https://raw.githubusercontent.com/sikorski-as/sndlib/master/native/nobel-eu/nobel-eu.txt), fetched with TLS verification enabled. Use the agreed TopoHub local-file adapter rather than its bundled JSON or runtime downloads, and merge the assignment's `sites.csv` as described in the [data loading design](#data-loading-design).
- **Evidence:** Parsing the mirror produced 28 nodes, 41 links, and 378 demands totaling 1,898 units. With the assignment's additions, those figures yield 37 nodes, 55 links, and 391 demands totaling 2,068 units. Matching counts do not prove official provenance.
- **Open follow-up:** The project owner will contact Quantum Sky for clarification or an official source. Preserve source revision, retrieval date, checksum, and attribution when acquiring the local copy; compare or replace it when an official file becomes available. Source selection is recorded, but official provenance and permitted use remain unresolved. Track this in the [resource-gathering task](tasks/todo.md#gather-and-validate-the-nobel-eu-dataset-source).

Use this record when explaining the assignment's "Unclear" topic: distinguish the verified access failures, our provisional engineering decision, and the clarification still outstanding.

## Known Issues

Verified on 2026-10-23:

- **SNDlib download links return 404.** GET requests to both the [nobel-eu XML URL](https://sndlib.put.poznan.pl/download/sndlib-networks-xml/nobel-eu.xml) and [nobel-eu native-text URL](https://sndlib.put.poznan.pl/download/sndlib-networks-native/nobel-eu.txt) returned HTTP 404. The same paths on `ventus.put.poznan.pl` also returned HTTP 404. These checks do not establish whether the missing files are intentional.
- **SNDlib hostname certificate mismatch.** The TLS certificate served for `sndlib.put.poznan.pl` has `ventus.put.poznan.pl` as its Common Name and its only Subject Alternative Name. Hostname verification therefore fails for `sndlib.put.poznan.pl`; the HTTP 404 responses above were obtained only with certificate verification disabled for diagnosis. Whether the mismatch is intentional is unknown.
- Candidate mirrors and the follow-up validation work are documented in [the dataset resource-gathering task](tasks/todo.md#gather-and-validate-the-nobel-eu-dataset-source).
