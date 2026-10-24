"""Remove GHCR versions for a deleted ref without deleting other image tags."""

import json
import os
import subprocess
from pathlib import Path

from image_tag import PERSISTENT_BRANCHES, branch_tag

PACKAGE = "users/fr3nch13/packages/container/qsp137sa"


def deletion_candidates(versions: list[dict], tag: str) -> list[int]:
    """Refuse deletion if a matching package version also has other tags."""
    candidates = []
    for version in versions:
        tags = version["metadata"]["container"]["tags"]
        if tag in tags:
            if set(tags) != {tag}:
                raise ValueError(
                    f"Refusing to delete {tag!r}: version {version['id']} "
                    f"also carries tags {tags!r}"
                )
            candidates.append(version["id"])
    return candidates


def main() -> None:
    """Look up all package versions and delete only exclusively matching ones."""
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    ref = event["ref"]
    tag = branch_tag(ref) if event["ref_type"] == "branch" else ref
    if tag in PERSISTENT_BRANCHES:
        raise ValueError(f"The {tag!r} image tag is protected from automatic deletion")

    # A package that has never been published is a normal no-op; other API failures are not.
    packages = json.loads(
        subprocess.check_output(
            [
                "gh",
                "api",
                "--paginate",
                "--slurp",
                "users/fr3nch13/packages?package_type=container&per_page=100",
            ],
            text=True,
        )
    )
    if not any(package["name"] == "qsp137sa" for page in packages for package in page):
        print("No qsp137sa package exists; nothing to delete.")
        return

    pages = json.loads(
        subprocess.check_output(
            ["gh", "api", "--paginate", "--slurp", f"{PACKAGE}/versions?per_page=100"],
            text=True,
        )
    )
    candidates = deletion_candidates(
        [version for page in pages for version in page], tag
    )
    for version in candidates:
        subprocess.run(
            ["gh", "api", "--method", "DELETE", f"{PACKAGE}/versions/{version}"],
            check=True,
        )
        print(f"Deleted GHCR version {version} for tag {tag!r}.")
    if not candidates:
        print(f"No published image has tag {tag!r}; nothing to delete.")


if __name__ == "__main__":
    main()
