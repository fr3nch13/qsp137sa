---
marp: true
theme: default
paginate: true
size: 16:9
title: LinkScope - Network Resilience Review
style: |
  section.dense { font-size: 23px; }
  section.dense h1 { font-size: 1.6em; }
  header { font-size: 17px; color: #586574; }
  section { font-size: 28px; }
  h1 { font-size: 1.55em; }
  li { margin-bottom: 0.45em; }
  section.dense table { font-size: 21px; }
  table { width: 100%; }
  th, td { padding: 0.35em 0.5em; }
---
<!--
LinkScope panel presentation (Marp Markdown). About 10 slides for a 15-minute
slot that includes a live demo. Export PDF and PPTX with:
  docs/slideshow/regenerate-presentation.sh
Export needs a local Chrome, Chromium, or Edge.
-->

<!-- _header: LinkScope -->

# I built LinkScope to make outage risks visible.

- I answer three operational questions, then show a short live outage.
- I explain the decisions I owned, not just the code the tool generated.
- I distinguish a verified local demo from a service ready to share.

<!--
I will spend about 15 minutes on this presentation, including the live demonstration, leaving the implementation and full history for questions.
My focus is engineering judgment: choosing scope, steering the tool, checking its work, and owning the remaining risks.
-->

---

<!-- _header: Findings -->
<!-- _class: dense -->

# I would investigate Berlin–Hamburg first.

- **Q1. “Where does the network have single points of failure?”**
  I evaluated all **92** single failures: **37 nodes and 6 links** meet the literal criticality rule. Every node loses its own traffic; that alone does not mean it harms others (Paris).
- I found wider impacts: losing **L12 Berlin–Hamburg** puts L26 at **128.30%**; losing **HUB-EAST** cuts off OPS-EAST-1 and loses **20 units**.
- **Q2. “Which links does the traffic depend on most?”**
  I found L12 busiest: **390.55 of 550 units, 71.01%**. Next is L3 Amsterdam–Hamburg: **376.23 units, 68.40%**.

<!--
The remaining baseline top five are L26 Frankfurt–Munich at 341.69 units and 62.13%, L30 Milan–Munich at 323.48 units and 58.81%, and L13 Berlin–Munich at 278.46 units and 50.63%; each has capacity 550.
The six critical links are L12, L26, the single access links from OPS-WEST to Dublin, OPS-SOUTHEAST to Athens, OPS-EAST-1 to HUB-EAST, and HUB-EAST to Warsaw; losing L26 puts L12 at 112.36%.
Hamburg and Berlin failures put L26 at 117.06% and 113.30%; Athens and Dublin each cut off a site with 20 units, while Warsaw loses 20 units even though OPS-EAST-2 remains physically connected because it cannot relay.
Every other node failure loses only its own traffic, so I distinguish that from harm to other demands rather than treating all critical labels as equally actionable.
-->

---

<!-- _header: Findings -->
<!-- _class: dense -->

# I can show why a connected site may still lose traffic.

- **Q3. “What happens when a given link or site goes down?”**
  I show one failure at a time, separating the failed node’s own traffic from other undeliverable traffic.
- I fail **Link L12**: L26 rises to **128.30%**.
- I fail **Node Hamburg**: **27 endpoint demands, 162 units** lost; L26 reaches **117.06%**.
- I fail **Link HUB-EAST–Warsaw**: **20 units** undeliverable, without disconnection.
- I choose **Restore baseline**: L12 returns to **71.01%**, without reloading.

<!--
Before presenting, I run `docker compose up -d` and open http://localhost:2158; I keep this demonstration to about two minutes.
I choose Link in the Node/Link selector, choose L12 in the Element selector, click Fail selected, and point to L26 at 128.30%.
I choose Node, select Hamburg in the Element selector, click Fail selected, and read the separate endpoint loss and overload figures; then I choose Link, select HUB-EAST–Warsaw, and click Fail selected to show loss without disconnection.
I click Restore baseline and point to L12 at 71.01%, explaining that a physically connected operations site cannot forward other traffic.
-->

---

<!-- _header: Structure and design -->
<!-- _class: dense -->

# I kept the model independent of the screen.

| Part | Organization and reason |
| --- | --- |
| Inputs and model | `data/`: unchanged backbone and sites; nodes, links, demands and relay roles. |
| Backend calculations | `topology.py` loads and validates; `routing.py` routes; `failures.py` explains failures. Pure functions isolate each request. |
| Routing rule | Fewest hops; equal shares across tied paths. Sites and data centres never relay. No database or baseline mutation. |
| Web interface | `network_api.py`: `GET /api/network` returns topology, baseline, top five and criticality. `GET /api/analysis?kind=link&id=L12` returns failure impacts. |
| Browser and delivery | `api.ts`, `NetworkWorkspace`, `NetworkMap`, `FailureControls`. I chose Django and React with TypeScript in one image, and a real geographic map. |

<!--
The merged model has 37 nodes, 55 links, 391 demands and 2,068 units, matching the brief; the source backbone has 28 nodes, 41 links and 378 demands, with 14 access links added.
The analysis interface also accepts kind=node and separates undeliverable demands, failed endpoint demands, disconnection and overload; Gunicorn serves the React page and the interface from the same origin, keeping startup to one command.
I chose the stack, single image, Leaflet with OpenStreetMap, friendly public errors and restoration of the validated baseline; I accepted the tool’s equal-split path-counting algorithm, test fixtures and stale-response guards after review: confirm this split before presenting.
The boundaries let me test network rules without a browser, while per-request calculations avoid one user’s simulation changing another’s baseline.
-->

---

<!-- _header: Setting up the AI -->
<!-- _class: dense -->

# I gave the tool boundaries and a gate before coding.

- I supplied `AGENTS.md` and `.github/copilot-instructions.md`: small reviewable changes, existing conventions, no secrets.
- I supplied project context and a **plan, execute, verify** workflow before implementation.
- I used milestones with acceptance gates; I reviewed each milestone and addressed findings from **6 review-agent reports**.
- I required **45 Django tests, 16 frontend tests**, continuous integration helper tests, TypeScript type checks, Ruff and Biome lint checks.
- I required development and production image builds and container web checks. **No local Git hooks**: branch protection requires the continuous integration `test` check before merging to main.

<!--
The context and workflow live in .github/project-context.md and .github/workflow-orchestration.md, with milestone gates in .github/tasks/todo.md.
The review agent is defined in .github/agents/Review.agent.md and its six reports are in .github/review/; automated review supported, rather than replaced, my milestone reviews.
TypeScript uses tsc, Ruff checks Python lint and formatting, and Biome checks TypeScript; I accepted this tooling and the image smoke-test scripts after review, but confirm this attribution before presenting.
The enforced merge gate is branch protection, not an invented local hook or a promise that every tool suggestion is correct.
-->

---

<!-- _header: Verification -->
<!-- _class: dense -->

# I checked the numbers against evidence outside the tool.

- I checked the brief’s totals: **37 nodes, 55 links, 391 demands, 2,068 units**.
- I used tests with hand-calculated expected values: a **6-node** merge with **5 links, 4 demands, 77 units**, plus fractional equal splits.
- I checked overload boundaries: **12 units** rerouted onto **10-unit** links; exactly **100%** is not overloaded, above it is.
- I checked traffic conservation, endpoints never relaying and input-order independence; all **92 failures** ran twice with matching results.
- I used independent evidence: an external validator reproduced failures and restore from the public image; I rebuilt the development container and started the downloaded Compose file.

<!--
The acceptance totals come from the brief, while the small-network expectations come from arithmetic rather than generated real-network snapshots.
The external validator pulled the image anonymously and reproduced L12, Hamburg, Warsaw, Dublin and restore in a browser; my separate startup check used docker compose up -d.
I must confirm which of these I specified before presenting; I am not claiming personal authorship of every test.
These checks support the stated routing model, not a claim that fewest-hop routing predicts every real network’s behaviour.
-->

---

<!-- _header: Production concerns -->
<!-- _class: dense -->

# I would not expose this demo as a service.

| Concern | Now and scope decision | First internal release |
| --- | --- | --- |
| Input validation and error handling | **Done well:** file and row checks, friendly errors, private log details, bad-input tests. | Keep these; add alerting. |
| Dependency and security checks | **Done well:** locked dependencies, lint, tests, image checks, non-root container, merge gate. | Add static security analysis, dependency and image vulnerability scans. |
| Authentication and access control | None; local demo only. | Single sign-on and role-based authorization. |
| Logging | Request and error logs to standard output; local visibility only. | Central collection, retention and alerts. |
| API versioning | None; browser and backend ship together. | Version and deprecation policy before other clients. |
| Configuration and secrets | Runtime secret key required; public key for local demo only. | Secret manager, rotation and encrypted web connections. |

<!--
I concentrated on rejecting bad data safely and making the build repeatable, rather than claiming six production concerns were fully solved.
The security foundation is useful but incomplete: lint and image smoke tests are not vulnerability scanning, and a non-root container is not access control.
The remaining controls were deferred for this local demonstration; shared access, external clients and retained operational evidence change those requirements.
I would require identity, private runtime secrets and encrypted connections before sharing the service, then centralize logs and add the listed security checks.
-->

---

<!-- _header: Steering -->
<!-- _class: dense -->

# I redirected effort toward the operational question.

| What the tool produced | What I changed | Why |
| --- | --- | --- |
| Eleven requirements squeezed into three checklist items; most effort on infrastructure. | Milestones M6a–M6f, each with an acceptance gate. | The application is the assignment; keep it simple. |
| A proposed vector diagram. | A real Leaflet map with OpenStreetMap. | Operations needs geographic context. |
| CI on every development push. | Only main pushes, pull requests and version tags; forks blocked. | Limited automation budget. |
| Extra Docker stages; the app folder as the user's home. | Base, development and production stages; a separate home. | Less to maintain; no tool clutter in the source. |
| Multi-platform image builds. | Linux AMD64 only, emulated on my Mac. | No ARM requirement; simpler builds. |

<!--
These are interventions where I changed the tool’s direction, not a list of features it generated.
The milestone split restored attention to input validation, routing, failure analysis and the usable screen instead of letting container work dominate.
The budget and platform decisions have costs: fork contributions cannot use that pipeline, and my Mac needs emulation.
I can discuss those trade-offs against the full commit history rather than presenting them as universal best practices.
-->

---

<!-- _header: Unclear -->
<!-- _class: dense -->

# I made ambiguous requirements explicit.

| What was unclear | How I resolved it |
| --- | --- |
| The official SNDlib download was unavailable. | I asked Quantum Sky and used an approved mirror; kept the file unchanged with checksum and attribution recorded. |
| The literal criticality rule marks every node critical. | I kept that rule and separated own endpoint losses from other undeliverable traffic. I would ask the panel whether that is the intended operational meaning. |
| Who should see bad-input file and row details? | I kept those details in server logs; the public interface and screen return a friendly generic error. |

<!--
The approved mirror resolved a blocked dependency without silently substituting invented data.
For criticality I preserved the acceptance rule, but made the impact categories useful for an operator instead of quietly redefining the requirement.
For errors I treated file and row diagnostics as operator information; I would make that interpretation explicit because the brief asks for those details without naming the audience.
-->

---

<!-- _header: Time spent -->

# I still need to record the hours honestly.

- **Time spent: TBD.** I will fill this in before presenting.
- My history spans **October 23–27, 2026**, with **78 commits**; that is not an hours estimate.
- I would next prioritize access control, security scanning and central logging before shared use.

<!--
I have not recorded a defensible total yet, so I will not convert elapsed dates or commit counts into working hours.
I will replace TBD with my actual time record before the panel session.
I will stop here for questions about the results, decisions and full git history.
-->
