# Descision Notes

Scratch notes on the project design choices I make.
These are notes I wrote myself, without the AI agent's help or input.

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

## Issues

- The SNDlib source files both return a 404 (intentional?)
- The SNDlib website's TLS certificate's CommonName and SAN don't match the given hostname (also intentional?).
