# Descision Notes

Scratch notes on the project design choices I made.

## 1. IDE Setup

I prefer to use VS Code. I came to it from it's predecessor Atom.

It also supports devcontainers which I like using for the following reasons:

- The project's environment is isolated from the workstation
- The image/container, and configuration of the devcontainer is committed as code to the project so other developers can create the same environment using the content contained in the project.
- The IDE/container can be rebuilt to a known and predictable state.

## 2. Agent Setup

- Create the Agent's project guidelines.
- `AGENTS.md` at the root of a project is a common file most agents look for when warming up to a project.
- I use Github Copilot for my personal projects and have a personal subscription to it, so that is what I cose to use as the agent harness/integration.
- Github Copilot prefers to use `.github/copilot-instructions.md` as its starting point for warming an agent, so the `AGENTS.md` just tells any agent reading it to read the `.github/copilot-instructions.md` instead.

### `.github/copilot-instructions.md`

- This is the actual starting point for the AI agents.
- It describes:
  - How it should organize its in-project memory/notes.
  - Things like `.github/tasks/lessons.md` and `.github/tasks/todo.md`, along with other markdown files either it creates, or I direct it to create

### `.github/workflow-orchestration.md`

- Defines how the agent 
- It describes:
  - How the agent should behave within the project
  - How it should plan, track, and agentically stear the token predictions.
- This was based on a publically available/published document that I have tweaked as needed.

### `.github/project-context.md`

- While the other 2 files define how the agent should behave and work, this file holds the context of the specific project itself.
- Its intended to be managed, updated and reviewed from the agent's perspective.
- Think of it as the commonly used `MEMORY.md` for this specific project.

## Agent's choices

- I had the agent come up with the name of the project `LinkScope` after reminding it the context of the company name, project/division name, and purpose of the application.

## Tech Stack

- Chose Django. Mentioned in job description, and can handle the project's needs.
  - Future Authentication
  - API responses for a react frontend
  - API can also be used with an option MCP server sidecar
- Chose docker image
  - container native for things like k8s
  - Dev image (for devcontainer) and prod image use the same Dockerfile for building both.

## Issues

- The SNDlib source files both return a 404 (intentional?)
- The SNDlib website's TLS certificate's CommonName and SAN don't match the given hostname (also intentional?).

## Agent Steering

- When creating the initial version of the Docker file, it wanted to make base, development, devcontainer, application-build, and production images. We don't need all of that. I had it reduce to just base, development and production. We can add other images later as needed.
- The agent created the application at /app in the Dockerfile and also make it the app user's home dir. I had it make a proper one.
- **CI triggers and budget:** The agent's first CI design ran on pushes to `dev`. I do most of my work on `dev`, so I limited runs to pushes to `main`, PRs (with `dev` publishing only from a `dev`-sourced PR), and SemVer release tags. I also blocked fork PRs from running jobs because I have a limited Actions budget.
- **Core application over infrastructure:** I noticed the actual assignment (R1-R11) had been compressed into three checklist items while the CI/container work got most of the attention. I had the agent reread the brief and split the application into milestones M6a-M6f, each with its own acceptance gate, and told it to keep things simple (KISS) with no speculative abstractions. Backend (M6a-M6d) and frontend (M6e-M6f) went into separate PRs, stopping for my review after each milestone.
- **CI warning handling:** The agent added a guard that failed CI on any Node/npm warning, and when `download-artifact` kept emitting an upstream `DEP0005` deprecation it proposed custom extraction workarounds and an npm upgrade. I rejected the workarounds and the npm upgrade: we keep Node's bundled npm, disable only its update notice, and leave third-party warnings visible in the logs without failing the job (`c3ccf58`, `74de28b`, `71c80b3`).
- **Real map instead of a diagram:** For R9 the agent initially proposed an SVG drawing. I chose an actual Leaflet/OpenStreetMap map so sites appear near what they attach to, on real geography (`6908828`).
- **Single platform image:** The agent started on multi-platform CI publishing. I chose a single `linux/amd64` image with the platform set explicitly in Compose, and used emulation on my ARM Mac, to keep CI simple (`6dfde04`).
- **Error details stay in the logs:** The API originally returned the file-and-row input error to the browser. I had the agent show a generic, user-friendly message in the frontend and keep file paths and row numbers out of the public API entirely; they are only written to the server logs (`d90b0aa`).
- **README audience:** The agent put status tracking and production-readiness detail in the README. I moved that into the interview preparation notes and kept the README focused on what the app does and how to run it.
- **Commit attribution:** The agent added AI co-author trailers to its commits. I stopped that; commits are mine.
- **External validation results:** An external validation agent reported the devcontainer check as "not run" and documented a Docker config workaround. I rebuilt the devcontainer myself, and the unmodified `docker compose up -d` from a downloaded `compose.yaml` worked for me without any workaround, so I closed those items based on my own checks.

## Git specific choices

- The original github project was set up as a private repository along with the docker images repository. After speaking with the recruiter, I was advised to make it public.
- **Visibility update (2026-10-27):** I made both the GitHub repository and GHCR image package public. Anonymous downloads of the Compose file and access to the `main`/`dev` image manifests were verified without account credentials. Public distribution does not make the unauthenticated application safe for public deployment; the local-only binding remains.
- Before making it public, I had AI agents perform a security/privacy audit. It found a person's name in the assignment PDF's Author metadata. I had the agent remove that PDF from the history of both `main` and `dev`, retaining all 70 development commits and the Markdown conversion. The rewrite changed commit hashes but no other file contents.
- **Accepted publication limitation (2026-10-27):** Rewriting branch history did not purge GitHub's retained objects. An authenticated check could still retrieve the PDF through an old commit ID; old PR references or cached views may leave it accessible after publication. GitHub documents no guaranteed expiration or self-service purge, and Support only assists with qualifying sensitive-data cases. In the interest of time, I chose to publish the existing repository with this residual-access risk accepted, rather than delay for Support or create a replacement repository. This is not a claim that the PDF was completely erased from GitHub.
