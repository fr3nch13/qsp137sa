# LinkScope git history: quiz notes for Brian

Companion to linkscope-presentation-v2.md. Use this to prepare for git-history
questions. Do not present this file. Check hashes again before the interview
if you push new commits, because a history rewrite on Oct 27 already changed
hashes once.

## How the history is organized

- All numbered PRs below merge into main. Almost all come from fr3nch13/dev.
  The exception is PR 7, from fr3nch13/ci/ghcr-untagged-cleanup.
- Workflow: work on dev, open a PR to main, the CI `test` check must pass,
  then merge. There are no local git hooks. Branch protection is the gate.
- Current main at the time of this draft: PR 18 merge d22f4b3, tag 0.0.1.
  Presentation skeleton: fd0bf42.
- Backend M6a to M6d went in one PR (PR 11). Frontend M6e to M6f went in a
  separate PR (PR 12). That split was deliberate, after your review at each
  milestone.

## PR map

- PR 1, merge 15092a9, Oct 24: early project setup, including Actions upgraded
  to Node 24 native releases (ac60b7e) and Docker image metadata plus gh in
  the development image (1cb188b).
- PR 2, merge 9071eac, Oct 24: README, project context, and interview
  preparation documentation.
- PR 3, merge cb47b77, Oct 24: Compose startup with explicit linux/amd64
  (6dfde04), plus Compose rationale and future devcontainer notes (46e491e).
- PR 4, merge 0f360e6, Oct 24: design decisions for current, future, and
  possible splits (2a64271). This is the commit to cite for the 1 image,
  then 2 images, then 2 repos plus IaC repo ladder.
- PR 5, merge 019ccff, Oct 26: M1 React TypeScript source and build
  foundation (a6b5501).
- PR 6, merge c863657, Oct 26: Node warning handling, first pass
  (b568adc), then bundled npm kept with update notice off (c3ccf58).
- PR 7, merge bd8b878, Oct 26: GHCR untagged image cleanup (9240326),
  from the ci/ghcr-untagged-cleanup branch.
- PR 8, merge 4d359a9, Oct 26: M2 same-origin Django serving and frontend
  API proof (27aa06c), deleted-ref cleanup fix (1618490), and a note on the
  deferred recovery gap for tagged images after branch deletion (56e4cc5).
- PR 9, merge b75ec5d, Oct 26: Node warning guard added (edc0805).
- PR 10, merge 875c595, Oct 26: fatal Node warning guard removed
  (74de28b, 71c80b3), frontend rebuild workflow verified (5727d7f).
  Say why: an upstream DEP0005 warning from download-artifact failed CI,
  and you rejected a custom extractor and an npm upgrade.
- PR 11, merge eb63cd7, Oct 27: the core application backend, plus review
  agent instruction (09a84cf), devcontainer Docker access (fb822e0), and
  the M6a to M6c delivery plan (35d306c).
  - M6a loader: d8b3e96
  - M6b routing: d2fbb65
  - M6c failures and criticality: 5aad627
  - M6d JSON API: c98bb13
- PR 12, merge c5ece50, Oct 27: frontend and error diagnostics.
  - M6e Leaflet map: 6908828
  - M6f interactive fail and restore: 0c9b835
  - R2 diagnostics and logging: e0cac8f
  - README clarification: 710303b
- PR 13, merge ef394cb, Oct 27: decision notes refined (aea4d40), IDE
  setup, agent steering, and Git-specific choices.
- PR 14, merge fb89e73, Oct 27: merge and sync step on the way to
  publication. Cite PR 13 and PR 15 for content, not PR 14, unless you
  check its diff before the interview.
- PR 15, merge 7b3701b, Oct 27: publication step.
  - Accepted publication limits after PDF history rewrite: b43d4b9
  - Future security scanning priorities: 3730a4d
  - Public repository status and access details: 5b16394
  - Published full-application acceptance recorded as main at 7b3701b,
    CI run 40585604261, digest sha256:b2c8afa7 as written in the docs.
    The docs truncate that digest. Do not invent the full value.
- PR 16, merge 63d8216, Oct 27: dataset provenance clarified (a14fafd).
- PR 17, merge e906d10, Oct 27: friendly API errors, input diagnostics
  in logs only (d90b0aa).
- PR 18, merge d22f4b3, Oct 27: presentation skeleton (fd0bf42),
  Marp deck, PDF, PPTX, and regenerate script. This v2 rewrite is not
  yet committed to the repo.

## Review reports in .github/review

- 2026-10-24 project code: Approve with minor fixes
- 2026-10-27 M1 frontend source and build foundation: Approve
- 2026-10-27 M2 same-origin serving: Approve with minor fixes
- 2026-10-27 M6 network application delivery: Approve with minor fixes
- 2026-10-27 M6d network API: Approve with minor fixes
- 2026-10-27 M6f interactive fail and restore: Approve with minor fixes

The Review agent is read-only. It writes one review file, with verdict,
severity-ranked findings, gaps, and an action checklist. It never edits
source. You addressed the findings and reviewed each milestone.

## Likely quiz questions, short answers

- Why Django and not FastAPI? Job description names Django, FastAPI, or
  comparable. Django gives auth, sessions, ORM, migrations, and admin
  together for later. Adding FastAPI alongside Django would add a second
  request framework with no current requirement. No DRF or Django Ninja.
- Why one image now? One repo, one Dockerfile, one container, one start
  command for a local demo with no database and no scaling story. A
  frontend-only change rebuilds the whole image. That cost is accepted
  now and documented as the reason to split later.
- Why devcontainer? VS Code, isolated from the workstation, environment
  committed as code, rebuildable to a known state. Same Dockerfile as
  production, different target.
- Why no CI on dev pushes? You do most work on dev, Actions budget is
  limited, and a dev push is not a merge decision. Triggers: PRs to main
  or dev, pushes to main, SemVer tags only. Fork PRs are skipped before
  a runner starts.
- Why no local git hooks? The gate is branch protection requiring the
  CI `test` check. Do not claim hooks exist.
- Why AMD64 only? Single-platform CI stays simple. Docker Desktop
  emulation runs it on an ARM Mac for the demo. Not a claim of native
  ARM performance.
- Why is the error detail in logs, not the browser? The brief asks for
  file and row details without naming the audience. Public API returns
  a generic 503. Logs are the operator channel. Commit d90b0aa, PR 17.
- What does AGENTS.md actually say? It is a pointer. It tells agents to
  follow .github/copilot-instructions.md, and review agents to also
  follow .github/agents/Review.agent.md. The real rules are in
  copilot-instructions, project context is project memory, and workflow
  orchestration is plan, execute, verify.
- What did you stop the tool doing? See the steering table in the deck.
  Lead with M6 split, Leaflet map, CI triggers, Docker stages, and
  error handling. Add co-author trailers stopped, and Node warning
  workaround rejected, if asked for more.
- Is the PDF completely gone from GitHub? No. It was removed from main
  and dev history, with development commits retained and the Markdown
  conversion kept. GitHub retained objects may still serve it through
  an old commit ID. That limitation was accepted, commit b43d4b9,
  PR 15. Do not claim complete erasure or an expiration date.
- Is public the same as production ready? No. Repo and GHCR package
  became public Oct 27, anonymous Compose download verified, but the
  app is unauthenticated and loopback only. Public distribution does not
  mean version 1.0 production ready.

