# Workflow Orchestration

## Workflow

### 1. Plan Mode Default

- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately – don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy

- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One tack per subagent for focused execution

### 3. Self-Improvement Loop

- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done

- Never mark a task complete without proving it works
- Diff behavior between main or committed changes and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)

- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes – don't over-engineer
- Challenge your own work before presenting it
- Remember K.I.S.S.: Keep It Short and Simple
  - Focuses on meeting current requirements with clear, readable logic.
  - Uses plain, explicit structures (e.g., a simple if statement) over obfuscated or short-hand code this is hard for a human to track down.
- Remember D.R.Y: Don't Repeat Yourself.
  - Single Source of Truth: Every piece of knowledge, business rule, or logic must have a single, unambiguous representation in a system.
  - Reduce Duplication: Instead of copy-pasting code or hardcoding the same rule in multiple places, you centralize it into a single function, module, class, or environment variable.
  - Scalability: Makes large projects easier to manage as teams grow.

### 6. Autonomous Bug Fixing

- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests – then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how
  - This means making sure the test case is covered, not obfuscated just to get it to pass

## Task Management

1. **Plan First++**: Write plan to `tasks/todo.md` with checkable items
2. **Verify Plan++**: Check in before starting implementation
3. **Track Progress++**: Mark items complete as you go
4. **Explain Changes++**: High-level summary at each step
5. **Document Results++**: Add review section to `tasks/todo.md`
6. **Capture Lessons++**: Update `tasks/lessons.md` after corrections

## Core Principles

- **Simplicity First++**: Make every change as simple as possible. Impact minimal code.
- **No Laziness++**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact++**: Changes should only touch what's necessary. Avoid introducing bugs.
