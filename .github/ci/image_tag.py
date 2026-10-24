"""Choose a Docker tag and reject branch/release tag collisions."""

import json
import os
import re
import subprocess
from pathlib import Path

# Long-lived branches whose image tags are reserved and never auto-deleted.
PERSISTENT_BRANCHES = ("main", "dev")
# SemVer 2.0.0 without build metadata, because Docker tags cannot contain "+".
SEMVER = re.compile(
    r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(-(0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(\.(0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
)


def branch_tag(branch: str) -> str:
    """Normalize a Git branch name into a Docker-compatible tag."""
    return re.sub(r"[^a-z0-9_.-]+", "-", branch.lower()).lstrip(".-")


def image_tag(event: str, ref: str, branches: list[str], tags: list[str]) -> str | None:
    """Validate the image tag to publish, or return None for test-only runs."""
    if event == "pull_request":
        # `main` publishes from pushes; `dev` publishes only from its PRs.
        if ref == "main":
            return None
        if ref == "dev":
            return "dev"
        tag = branch_tag(ref)
        if tag in PERSISTENT_BRANCHES or tag in tags:
            raise ValueError(
                f"Branch {ref!r} conflicts with a persistent-branch/release image tag"
            )
        if any(branch != ref and branch_tag(branch) == tag for branch in branches):
            raise ValueError(f"Branch {ref!r} normalizes to another branch's image tag")
    else:
        tag = ref
        if event == "tag" and not SEMVER.fullmatch(tag):
            raise ValueError(f"Release tag {ref!r} is not a SemVer version like 1.2.3")
        if ref not in PERSISTENT_BRANCHES and any(
            branch_tag(branch) == tag for branch in branches
        ):
            raise ValueError(f"Release tag {ref!r} conflicts with a branch image tag")

    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}", tag):
        raise ValueError(f"{ref!r} cannot be published as a Docker tag")
    return tag


def main() -> None:
    """Read GitHub event metadata and write the validated job output."""
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    is_pr = os.environ["GITHUB_EVENT_NAME"] == "pull_request"
    ref = (
        event["pull_request"]["head"]["ref"] if is_pr else os.environ["GITHUB_REF_NAME"]
    )
    branches = [
        branch
        for branch in subprocess.check_output(
            [
                "git",
                "for-each-ref",
                "--format=%(refname:strip=3)",
                "refs/remotes/origin",
            ],
            text=True,
        ).splitlines()
        if branch != "HEAD"
    ]
    tags = subprocess.check_output(["git", "tag", "--list"], text=True).splitlines()
    kind = (
        "pull_request"
        if is_pr
        else ("tag" if os.environ["GITHUB_REF"].startswith("refs/tags/") else "push")
    )
    tag = image_tag(kind, ref, branches, tags)
    with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
        output.write(f"tag={tag or ''}\npublish={'true' if tag else 'false'}\n")


if __name__ == "__main__":
    main()
