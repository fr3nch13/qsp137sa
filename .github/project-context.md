# LinkScope — Project Context

This document describes the software product and its functional requirements. The original assignment, including presentation and submission expectations, is retained in [the assignment brief](../docs/Quantum_Sky_Project_137_Software%20Engineering%20Assignment.md).

LinkScope is an application within Project 137, a division of Quantum Sky.

**Important: Keep it small. We scoped it to a few hours on purpose.**

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

## Data Loading Design

Decision recorded on 2026-10-23; implementation is pending.

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

## Backend Framework Decision

Decision recorded on 2026-10-23; the Django scaffold and a status page are implemented. Network analysis and the Web UI remain pending.

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
- Adapt the shared-base pattern with only three stages: `base`, `development`, and `production`. Separate devcontainer and application-build stages add no value yet; introduce a build stage only when actual compilation or dependency installation requires one.
- Configure the devcontainer to build the `development` target, mount the workspace at `/app`, and run as `app`; production builds select the `production` target and copy application files directly into the image. The devcontainer uses the Dockerfile's long-running development command and aligns the `app` UID/GID with the host where supported so the bind-mounted workspace remains writable.
- Keep devcontainer lifecycle hooks separate: `post_create.sh` handles setup after creation, while `post_start.sh` handles repeatable startup work. Adapt their contents to LinkScope rather than copying CakePHP-specific ownership, paths, or personal agent configuration.
- The reference illustrates the container structure, not a requirement to adopt its PHP/Apache runtime, optional tools, credential mounts, or installation scripts.
- Use `ghcr.io/astral-sh/uv:python3.13-bookworm-slim` directly as the common base, without a build argument or digest pin. The project owner accepts the mutable tag to keep the Dockerfile simple. This selects Python 3.13, Debian Bookworm slim, and uv. Manage exact direct dependency versions in `pyproject.toml`, with a committed `uv.lock`; the devcontainer syncs dependencies on creation and production installs locked runtime dependencies during its image build.
- Development adds only Git, curl, and CA certificates and stays running for workspace attachment. Both targets define the common `app` user (UID/GID 10001); the devcontainer may align that user's UID/GID with the host for writable workspace mounts. Development owns `/app`; production restores root ownership of its application directory and files so the runtime user cannot modify them. Production does not inherit development tools.
- The `app` user's home is `/home/app`, created and owned by that user, while the working directory and bind-mounted workspace remain `/app`. The devcontainer mounts a named volume (`linkscope-home-${devcontainerId}`) at `/home/app` so home-relative IDE files and tool caches persist across normal rebuilds. The host-mounted workspace also survives rebuilds; removing the named volume deletes its home data.
- The legacy `.cache`, `.copilot`, `.vscode-server`, `.dotnet`, and `.gitconfig` entries were migrated to the home volume and removed from `/app` after content verification. Sixteen differing or missing originals (runtime state and old session locks) are preserved under `/home/app/.workspace-home-backup` without replacing current home state. The one-time migration hook and obsolete workspace ignore entries have been removed. Project files, `.env`, and `.venv` remain in `/app`.
- Django 6.1.2 and TopoHub 1.5.1 are direct dependencies. TopoHub 1.5.1 does not declare NetworkX, which its SNDlib provider imports, so NetworkX 3.7 is also pinned directly. Gunicorn 26.2.0 serves `linkscope.wsgi:application` on `0.0.0.0:2158` in the production image, logging requests to stdout. Its unused control socket is disabled so it does not write under the root-owned application directory. The root page reports scaffold status only; network analysis and the frontend remain pending.
- `.dockerignore` excludes local environments, secrets, Git metadata, and assignment/agent documentation from the build context.
- Container orchestration remains to be selected. Container packaging does not itself select Kubernetes or a cloud platform.

### Django startup

Run `uv sync --locked` to install dependencies. The devcontainer loads `.env.default` first and `.env` second through Docker's ordered `--env-file` arguments; values in `.env` override defaults. The template contains a public development-only placeholder key; `.env` is private and ignored by Git, and both files are excluded from image builds.

Before Docker starts, the devcontainer's host-side `initializeCommand` uses a POSIX shell to create an empty `.env` with owner-only permissions if absent. Existing contents and permissions are preserved. Fresh checkouts therefore use the public development-only defaults without manual setup. To override them, put a randomly generated `DJANGO_SECRET_KEY` in the private `.env`. Rebuild the devcontainer after changing either file; this configuration does not update an already running container's environment. No dotenv package or Django settings changes are needed.

Outside the devcontainer, supply `DJANGO_SECRET_KEY` through the environment before using Django or Gunicorn; an absent or blank value raises an explicit configuration error. For a temporary local session, generate an ephemeral key:

```sh
export DJANGO_SECRET_KEY="$(uv run python -c 'import secrets; print(secrets.token_urlsafe(64))')"
uv run python manage.py runserver 0.0.0.0:2158
```

The devcontainer forwards port 2158 and keeps its existing keep-alive command. Its `post_start.sh` hook starts the auto-reloading Django development server in the background, using a lifetime `flock` lock to prevent duplicate starts. Combined server stdout/stderr is appended to `/home/app/.cache/linkscope/runserver.log` and mirrored through `/proc/1/fd/1` to the container's stdout using `tee`, making it available to `docker logs` and configured container log collectors. This requires the main process's stdout to be writable by `app`; the hook fails explicitly otherwise. The hook checks HTTP readiness for up to 30 seconds and reports startup failures; repeat calls leave an existing server running. Debug responses remain disabled. Only `localhost`, `127.0.0.1`, and `[::1]` are allowed hosts. Authentication, administration, database configuration, and static assets are deliberately not enabled yet.

For the production image, with `DJANGO_SECRET_KEY` exported in the host shell:

```sh
docker build --target production -t linkscope:production .
docker run --rm -p 127.0.0.1:2158:2158 -e DJANGO_SECRET_KEY linkscope:production
```

Visit `http://localhost:2158/` for the status page. The key is runtime configuration, not an image-build input; do not commit it. Although Gunicorn is a production server, this unauthenticated scaffold remains a local-only demonstration, not a production-ready release.

With the key exported, validate with `uv lock --check`, `uv run python manage.py check`, and `uv run python manage.py test linkscope`. To smoke-test the production entry point without Docker, run `uv run gunicorn --bind 0.0.0.0:2158 --access-logfile - --no-control-socket linkscope.wsgi:application` and request the status page.

### Container foundation validation

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

`.github/workflows/delete-image.yml` runs on branch/tag deletion and removes matching GHCR versions, if present. It uses trusted code from `main`, paginates package versions, and refuses to delete a version carrying any other tag. `main` and `dev` image tags are protected from automatic deletion. Missing packages/tags are no-ops; permission and API errors fail explicitly. Deletion cancels an in-progress workflow for the same ref, and publishing also verifies that the source Git ref still exists. Untagged historical versions are not garbage-collected by this workflow.

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
