---
marp: true
theme: default
paginate: true
size: 16:9
title: LinkScope - Project 137 Presentation
style: |
  section { font-size: 18px; justify-content: flex-start; }
  header {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    background: #17212b;
    color: #f5f7fa;
    border-bottom: 3px solid #7dd3fc;
    padding: 0.5em 1em;
    font-size: 1.5em;
    line-height: 1.15;
  }
  h1 { font-size: 1.2em; line-height: 1.15; }
  h2 { font-size: 1.1em; line-height: 1.15; }
  li { margin-bottom: 0.4em; }
  strong { color: #17212b; }
  table { width: 100%; }
  th, td { padding: 0.35em 0.5em; }
---
<!--
Focus: the project as a whole, not a tour of the app.
Slides stay headline only.
Notes are the spoken script, one short line at a time.
Git history is in the repo if the panel wants it.
Timing: about 15 minutes, including the demo.
-->

<!-- header: "LinkScope" -->

## The project behind the demo.

Project 137: a small network resilience tool for a European backbone ops team.

This is a pre-release prototype, not a production application. A production version is a later milestone, outside this assignment. What I can show is a project you can check, with my production suggestions documented later in this deck.

First, the ops answers. Then how the project was designed and built.

<!--
Copilot named the project LinkScope.
The panel wants structure, design, and checking.
They also want AI setup, steering, and git history.
This deck follows that order, after the findings.
The app itself is deliberately small.
No database, one start command, local only.
No authentication yet.
I will say where the project stops, not just where it works.
-->

---

<!-- header: "Answers" -->

# Three ops answers.

- **Where are the single points of failure?** Under the literal rule, all **37 nodes and 6 links** count as critical. The useful subset is smaller: HUB-EAST, single-homed sites, and the L12/L26 pair.
- **Which links does traffic depend on most?** **L12 Berlin-Hamburg, 390.5 of 550 units, 71.0%**, then L3 Amsterdam-Hamburg at 68.4%, then L26 Frankfurt-Munich at 62.1%.
- **What happens when something goes down?** Lose L12 and L26 jumps to **128.3%**. Lose Hamburg and 162 units at its endpoints are lost, with L26 at 117.1%. Lose HUB-EAST to Warsaw and 20 units are lost with no disconnection.

<!--
The merged network is the first check.
It starts with the SNDlib nobel-eu data set.
That gives 28 cities, 41 links, and 378 demands.
I added 9 sites from the brief.
That gives 37 nodes, 55 links, and 391 demands.
The total load is 2,068 units.
Those totals match the brief.
L12 is 71 percent, L3 is 68.4 percent.
L26 is 62.1 percent, L30 is 58.8 percent.
L13 Berlin to Munich is 50.6 percent.
All of those shares are out of 550 units.
The literal criticality point matters here.
Losing a node loses its own traffic.
So I report failed endpoint demands separately.
I do not treat every critical label as equal harm.
-->

---

<!-- header: "Live demo" -->

## Three failures, then restore.

1. Fail **link L12: Berlin - Hamburg**. Watch L26 go to **128.3%**.
2. Fail **node Hamburg**. 27 endpoint demands, **162 units** lost, L26 at **117.06%**.
3. Fail **link HUB-EAST to Warsaw**. **20 units** lost, with no disconnection.
4. Click **Restore baseline**. L12 is back to **71.0%**, with no reload.

<!--
Fail L12 first, then watch L26 overload.
Fail Hamburg next, and note the endpoint loss.
Fail HUB-EAST to Warsaw last.
Say the relay rule out loud for that step.
An ops site never forwards other traffic.
So Warsaw loses its route, even while connected.
That is a routing rule, not a map error.
Restore reuses the validated baseline.
It does not rerun a simulation.
It does not change another user's view.
Each simulation is local to the page.
-->

---

<!-- header: "Why this stack" -->

## Small project with a future plans.

- **Django, Python:** the job description names Django or a comparable framework. It gives auth, sessions, ORM, and admin in one place for later.
- **No second framework:** native Django views serve the API. No Django REST Framework, no FastAPI alongside it.
- **React with TypeScript, esbuild, no Vite:** no separate frontend server. Django serves the built assets from the same origin.
- **TopoHub 1.5.1, NetworkX 3.7, uv, Python 3.13, all locked.** Loads are recomputed, not taken from TopoHub.
- **Leaflet with OpenStreetMap:** a real map, not a diagram, so sites sit near what they attach to.

<!--
Django was anticipated for auth, then deferred.
Retaining Django is not a claim that auth is done.
It means future auth needs no framework change.
The frontend build uses Node 24.
It runs npm ci and npm run build from the lockfile.
It also runs Biome lint and a TypeScript check.
The bundle is built with esbuild.
Only the esbuild install script is approved.

- Found TopoHub while searching for nobel-eu.txt
- Unavailable: https://sndlib.put.poznan.pl/download/sndlib-networks-xml/nobel-eu.xml
- Used https://github.com/sikorski-as/sndlib

Loads are recomputed, not taken from TopoHub.
- Meaning: we run on local file (data/nobel-eu.txt data/sites.csv) committed to this project.
-->

---

<!-- header: "One Dockerfile, two jobs" -->

## The devopment and production image.

- **One multi-stage Dockerfile, one base.** Base is uv Python 3.13 on Debian Bookworm slim. Then a Node build stage, a development target, and a production target. No separate Dockerfiles to drift apart.
- **Development target:** Node and npm, git, GitHub CLI, curl, Chromium for Marp export, user `app` (UID 10001), writable workspace at `/app`, separate home volume.
- **Production target:** root-owned `/app`, no Node or npm, Gunicorn serving Django, WhiteNoise serving built frontend assets, same origin, port 2158.
- **Published run:** `docker compose up` pulls the published image, binds only to `127.0.0.1:2158`, uses `linux/amd64` explicitly, and takes the secret key at runtime. Nothing secret is baked into the image.
- **Why a container at all:** container-native for later platforms, and one documented start command for the demo.

<!--
The platform choice was deliberate.
Single platform CI stays simple.
My ARM Mac uses Docker Desktop emulation.
That is slower than native ARM performance.
I do not claim native ARM performance.
Production does not inherit development tools.
The development target is a sibling of base.
It is not the parent of production.
Production files are root owned.
So the runtime user cannot modify them.
The demo key in Compose is public.
It is for local use only.
A shared deployment needs a private key at runtime.
It must be randomly generated, not baked in.

- Base image is: ghcr.io/astral-sh/uv:python3.13-bookworm-slim
-->

---

<!-- header: "Devcontainer" -->

## The devcontainer is the working environment, committed as code.

- I work in VS Code. I came to it from Atom. I like devcontainers because the environment is isolated from the workstation, committed to the project, and rebuildable to a known state.
- The devcontainer builds the **development** target from the same Dockerfile, bind-mounts the workspace at `/app`, and mounts a named home volume so IDE and tool state survives a rebuild.
- **On create,** `post_create.sh` runs `uv sync --locked`, then frontend `npm ci` and `npm run build`.
- **On start,** `post_start.sh` starts the Django dev server with a lock so it cannot start twice, logs to the linkscope run log, and waits up to 30 seconds for HTTP readiness.
- **Docker outside of Docker** is enabled so the agent and I can build and smoke-test images from inside the devcontainer, without a second Docker setup.
- Result: a fresh checkout can reach the same environment from the files in the repo, not from notes about my laptop.

<!--
The devcontainer forwards port 2158.
It runs as user app.
It aligns user and group IDs with the host.
That keeps the bind mounted workspace writable.
Workspace edits are visible through the devcontainer.
They are not visible through the published image.
The image must be rebuilt and published first.
That distinction matters for the live change.
I will make the live change in the devcontainer.
I will not edit the published image.
-->

---

<!-- header: "GitHub Actions" -->

## A small pipeline, gated, and shaped by a real budget.

- **Triggers only:** PRs to main or dev, pushes to main, SemVer tags. No dev pushes, fork PRs skipped before a runner starts.
- **Why:** I do most work on dev, and Actions minutes are limited. A dev push is not a merge decision.
- **The `test` job is the gate:** locked deps, frontend lint, type check, tests, and build, Ruff, ShellCheck, Django checks and tests, then build both images and run smoke tests.
- **Branch protection requires that `test` check before merging to main.** No local git hooks. The gate is in GitHub.
- **Publish only what was tested:** the tested image goes as a one-day artifact to a separate publish job. Build is read-only, publish has package write.
- **Cleanup:** untagged GHCR versions 24 hours or older are deleted after a publish, and a separate workflow deletes the image when a tag or branch is deleted.
- **Lesson kept:** a Node warning guard failed CI on an upstream warning. I removed the fatal guard and kept warnings visible.

<!--
I kept this pipeline small on purpose.
It only runs when a merge decision is near.
Pull requests, pushes to main, and release tags.
I do most work on dev, so dev pushes do not run.
Fork pull requests are skipped before a runner starts.
That saves my limited Actions minutes.
The test job is the gate for every merge.
It checks lint, types, tests, and both images.
Branch protection requires that test check to pass.
There are no local git hooks. The gate is in GitHub.
Only a tested image can be published.
It moves as a one-day artifact to a separate job.
The build job can only read. Publishing can write.
Old untagged images are cleaned up after a publish.
A separate workflow deletes an image with its tag.
One lesson stayed with me from this pipeline.
A warning guard failed CI on an upstream warning.
I removed the fatal guard and kept warnings visible.
-->

---

<!-- header: "Validation" -->

## How I know the numbers are right: tests first, then CI, then an outside check.

- **Expected values come from outside the tool.** Brief totals first: 37 nodes, 55 links, 391 demands, 2,068 units. Then hand arithmetic on small networks.
- **Small-network tests:** a 6-node merge with 5 links, 4 demands, 77 units, plus fractional equal splits, including an 8/4 split at unequal branches for a 12-unit demand.
- **Boundary tests:** 12 units rerouted onto 10-unit links overloads. Exactly 100% does not. Endpoint nodes never relay. Row order does not change the result.
- **Full-network tests:** all **92 single failures evaluated twice**, with matching results.
- **Counts:** **45 Django tests and 16 frontend tests**, plus CI helper tests. The same tests run in CI from a clean checkout, then again inside the built images.
- **Outside check:** an external validator pulled the public image anonymously and reproduced L12, Hamburg, Warsaw, Dublin, and restore in a browser.
- **Honest limit:** green CI proves the build, tests, and packaged images pass. It does not prove fewest-hop routing predicts real traffic.

<!--
Expected values come from outside the tool.
I start with the brief totals, then hand arithmetic.
Small networks test fractional equal splits.
Boundary tests test overload and relay rules.
Full network tests cover all 92 single failures.
Each failure was evaluated twice, with matching results.
The same tests run in CI from a clean checkout.
They run again inside the built images.
Input validation tests cover bad backbone and CSV rows.
File and row details go to the logs, not the response.
I will not claim I wrote every test file.
I specified the expectations and milestone gates.
I reviewed each milestone as it was delivered.
Point to the milestone gates if the panel asks.
-->

---

<!-- header: "AI Agents" -->

## How the AI agents are set up: Copilot, with rules in the repo.

- **Copilot Pro, personal subscription, integrated into GitHub and VS Code.** No separate agent harness. Rules travel with the repo.
- **`AGENTS.md` is a pointer, not the rules.** It points to `.github/copilot-instructions.md`, and review agents also follow `.github/agents/Review.agent.md`.
- **`.github/copilot-instructions.md` is the starting point.** Safe, minimal, reviewable changes, existing conventions, no new tools or deps unless requested, no secrets.
- **Docs placement is a rule.** README is the front door. Dev detail goes in `.github/project-context.md`. Panel material goes in `docs/slideshow/interview-preparation.md`.
- **`.github/project-context.md` is project memory.** Goal, data rules, stack decisions, milestones, production priorities, container and CI decisions, reviewed by me.
- **`.github/workflow-orchestration.md` is how the agent works.** Plan, execute, verify, stop and replan if needed, verify before done, KISS and DRY.
- **`.github/tasks/todo.md` is the gate list.** M1 to M7 with acceptance criteria. Backend in one PR, frontend in a separate PR, reviewed after each milestone.
- **The Review agent is read-only.** It writes one review file with verdict, findings, gaps, and a checklist. It never edits source. I addressed all 6 reports.

<!--
That came after I gave it the company and purpose.
The first step turned the assignment into Markdown.
It also created the project context file.
The Review agent writes one file per review.
It gives a verdict, findings, gaps, and a checklist.
It never edits source code.
I addressed all six review reports.
Workflow orchestration came from a public document.
I tweaked that document for this project.
I will not present it as written from scratch.
Commits are mine.
I stopped the agent adding AI co-author trailers.
-->

---

<!-- header: "Steering" -->

## Five times I stopped, redirected, or overrode the tool.

| What the tool produced | What I changed | Why |
| --- | --- | --- |
| The app squeezed into three checklist items, infrastructure getting most attention | Split it into M6a to M6f, each with a gate, backend and frontend in separate PRs | The application is the assignment. Keep it simple. |
| A proposed SVG diagram for the map | A real Leaflet map with OpenStreetMap | Ops needs geographic context. |
| CI on every dev push | Only main pushes, PRs, and SemVer tags. Forks blocked. | Limited Actions budget, and dev work is not a merge decision. |
| Five Docker stages, and the app folder as the user's home | Base, development, and production only, with a separate home at /home/app | Less to maintain, and no tool clutter in the source. |
| File and row input errors returned to the browser | A generic public error, with file and row details in server logs only | The brief asks for file and row details without naming the audience. Logs are the operator channel. |

<!--
The table shows five steering decisions.
Two more are useful if the panel asks.
The Node warning workaround was rejected.
The README stayed as the user front door.
Status and production detail moved elsewhere.
The tool also proposed multi-platform builds.
I chose Linux AMD64 only.
That is a sixth example if you need one.
The table above is the five to present.
-->

---

<!-- header: "Initial Priorities" -->

## Production now, first internal release, and where the project goes next.

- **Done well, 1: input validation.** File and row checks in logs, generic public errors, API 400, 404, and 405 handling, bad-input tests.
- **Done well, 2: a repeatable build.** Locked deps, lint, type checks, tests, image smoke tests, non-root production, CI merge gate.
- **Deferred, with a reason:** auth, central logging, API versioning, secret manager, vulnerability scanning. Local demo only.
- **First internal release, app:** protected auth views, central logs, versioned API, managed secrets with HTTPS, and security scanning with an SBOM.
- **Next, project:** two images in the same repo and Compose, frontend with nginx plus Django API only, with per-image CI only then.
- **Later, project:** two repos plus a third IaC repo pinning versions per environment, with promotion by pull request. Contract changes then need versioning discipline.
- **Not a commitment yet:** a database only when accounts need it, and an MCP sidecar only if a future requirement justifies it.

<!--
The brief prefers two things done well.
It prefers that to six things done badly.
That is why validation and build are the two.
The rest are explicitly deferred, with reasons.
Do not add parallel API versions speculatively.
Define the contract and deprecation policy first.
That comes before independent clients or breaks.
No database service is needed now.
Topology comes from local files.
A future release selects a relational database.
That happens when accounts and sessions arrive.
Scanning priorities are documented in the repo.
-->

---

<!-- header: "Unclear" -->

## Items, time, and questions for you.

- **SNDlib source:** the official download endpoints returned 404, and the site TLS name did not match. I asked Quantum Sky and used an approved mirror, file unchanged, checksum and attribution recorded. It is still not an official SNDlib distribution.
- **Criticality meaning:** I kept the literal rule and separated own-traffic loss from harm to others. Is that the operational meaning you intended?
- **Error audience:** file and row details go to server logs, not to the public API. Is that the channel you want for operators?
- **Time spent: about 10 to 12 hours** on the build through Oct 27, plus deck and rehearsal time I still need to total.I will not turn commit dates or commit counts into an hours estimate.
- **Questions for the panel:** which failure or live-change area should I prioritize, who would be the first internal users, and what access boundary should apply before anyone beyond localhost uses it?
- Next: your questions on the deck and git history, then the live change in the devcontainer.

<!--
Before the repo went public, an audit found a name.
That name was in the assignment PDF metadata.
The PDF was removed from main and dev history.
Development commits and the Markdown version stayed.
That rewrite changed commit hashes.
GitHub may still serve the old PDF from an old ID.
Old references or cached views may retain access.
I will not claim the PDF was completely erased.
I will not give an expiration date for that access.
A public repo does not make the app safe to expose.
The loopback only binding remains.
-->
