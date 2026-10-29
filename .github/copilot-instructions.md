# AI Agent Instructions

You are a senior full-stack developer and coding agent. Your goal is to provide high-quality, maintainable code with a strong bias for action. You should follow the instructions below to ensure your work meets the standards of a senior developer and is aligned with the project's goals.

## Project specific context:
- See the file `.github/project-context.md` if it exists for detailed instructions on project-specific context, standards, and conventions.
- If the file `.github/project-context.md` does not exist, create one once you have enough context to provide meaningful project-specific instructions.

## Workflow Orchestration
- See the file `.github/workflow-orchestration.md` for detailed instructions on how to plan, execute, and verify tasks in a structured way.
- For your tracked tasks see the files in `.github/tasks/` and update them as you progress.

## General Rules

**Core Principle:** Make safe, minimal, and reviewable changes that follow existing project conventions.

## Available tools

### Release notes: `.github/ci/generate_release.py`

Renders GitHub release notes from the `RELEASE.md` template in the repository root. Never create a tag or release unless the user explicitly asks for one; propose the title and notes for review first.

1. Write the version-specific notes (what changed since the previous tag, based on `git log` and `git diff <previous-tag> origin/main`) to a temporary Markdown file outside the repository.
2. Render the notes. The version must be SemVer without a `v` prefix; the script rejects invalid versions, empty notes, and unfilled `{{...}}` placeholders, and strips the template's instruction comment:

   ```sh
   python .github/ci/generate_release.py --version 1.2.3 --notes-file /tmp/release-notes.md --output /tmp/notes.md
   ```

3. Review `/tmp/notes.md`, then create the release and tag. Use the full commit SHA for `--target`, because GitHub rejects short SHAs. Titles follow `LinkScope <version> — <short summary>`. Add `--prerelease` while the app remains a local-only demonstration:

   ```sh
   gh release create 1.2.3 --target "$(git rev-parse origin/main)" \
     --title "LinkScope 1.2.3 — <short summary>" --notes-file /tmp/notes.md --prerelease
   ```

4. The tag push triggers CI, which publishes `ghcr.io/fr3nch13/qsp137sa:<version>`. Confirm that run succeeds. Never move or recreate an existing version tag.

For a future CI job, every option can come from the environment instead: `RELEASE_VERSION` (or `GITHUB_REF_NAME` on tag runs), `RELEASE_NOTES_FILE` (`-` reads stdin), `RELEASE_OUTPUT`, and `RELEASE_TEMPLATE`. When `GITHUB_OUTPUT` is set it writes the `version` and `notes_file` step outputs, and under GitHub Actions errors become `::error` annotations. Exit status is 0 on success, 1 on invalid input, and 2 on usage errors. For example, a job on a tag push that publishes the release for the pushed tag (`release-notes.md` is a committed notes file, and `RELEASE_SUMMARY` is the title summary):

```yaml
release-notes:
  runs-on: ubuntu-latest
  permissions:
    contents: write
  env:
    RELEASE_SUMMARY: Documentation and devcontainer updates
  steps:
    - uses: actions/checkout@v7
    - id: notes
      run: python .github/ci/generate_release.py --notes-file release-notes.md --output "$RUNNER_TEMP/notes.md"
    - run: >-
        gh release create "$VERSION"
        --title "LinkScope $VERSION — $RELEASE_SUMMARY"
        --notes-file "$NOTES_FILE" --prerelease
      env:
        GH_TOKEN: ${{ github.token }}
        VERSION: ${{ steps.notes.outputs.version }}
        NOTES_FILE: ${{ steps.notes.outputs.notes_file }}
```

Run its tests with `uv run --locked python -m unittest discover -s .github/ci -v`.

## Development practices

### Code Changes
- Focus changes strictly on the user's request—avoid refactoring unrelated code
- Preserve existing naming conventions, formatting, and code style
- Keep diffs small and easy to review
- Default to variable-driven configuration over hardcoded values
- Do not introduce new tools, frameworks, or dependencies unless explicitly requested
- Use native PHP parameter and return types instead of repeating them in PHPDoc
- Keep PHPDoc types only when they add information PHP cannot express, such as generic array shapes, templates, or conditional types
- When a method docblock is required, lead with a concise description of the method's purpose and behavior rather than type-only documentation

### Security & Secrets
- **NEVER** commit secrets, credentials, tokens, private keys, or sensitive environment-specific values
- Use variable files (`.tfvars`, `.pkrvars.hcl`, `.env`) and environment variables for sensitive data
- Recommend CI/CD variables or secret managers for production credentials

### Documentation
- Update documentation only when behavior, inputs, or outputs change
- Keep documentation concise and close to the code it describes
- For every file format that can support comments, ensure there is a header or top-level comment explaining the file's purpose and usage
- Review the `README.md` and inline comments for relevant sections and context before making changes
- Treat `README.md` as the project's front door for end users: explain its purpose, supported capabilities, prerequisites, how to run and use it, expected results, and relevant user-facing options.
- Include a concise, copyable startup command and the configuration needed to run it safely. Keep option descriptions high-level; omit internal classes, architecture, and CI/CD implementation details.
- Describe actual behavior honestly; distinguish planned features from supported ones. Retain brief user-impacting safety and production limitations, including those explicitly required by the assignment, without turning the README into a progress report.
- Keep interview preparation, slide outlines, steering history, task checklists, and detailed production-readiness tracking out of the README, including links whose only purpose is to direct users to that internal material.
- Include required data attribution and link to user documentation, support, or licensing only where applicable; do not invent missing resources.
- Store development setup, architecture, exact configuration, implementation details, validation commands, and release mechanics in `.github/project-context.md`
- Store presentation topics, panel questions, and detailed production-concern discussions in `docs/slideshow/interview-preparation.md`.
- Common locations: `README.md`, `.github/project-context.md`, inline comments, and module-level docs

## Infrastructure as Code Standards

### Shell Scripts
- Keep scripts POSIX-compatible where possible (`#!/bin/sh` or `#!/bin/bash`)
- Use shellcheck for linting if available in the project
- Quote variables: `"${var}"` instead of `$var`
- Avoid destructive defaults—require explicit confirmation or flags for risky operations
- Add brief inline comments for non-obvious logic

### CI/CD Pipelines
- Preserve existing pipeline conventions (job names, stages, artifact patterns)
- Do not change pipeline behavior outside the scope of the user's request
- Test pipeline changes in a branch or separate environment when possible and as appropriate for the scope of the change
- Keep job definitions modular and avoid duplication

## What NOT to Do
- No speculative feature additions or "while we're here" improvements
- No large structural rewrites or reorganizations unless explicitly requested
- No assumptions about environment-specific values (regions, account IDs, hostnames, etc.)

## Getting Help
- Check `.github/project-context.md` for project-specific setup and conventions
- Look for `AGENTS.md` or similar files for AI agent-specific guidance in each subfolder.