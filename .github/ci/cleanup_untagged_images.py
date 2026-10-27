"""Delete untagged GHCR versions last updated at least 24 hours ago."""

import json
import subprocess
from datetime import UTC, datetime, timedelta

from delete_image_tag import PACKAGE

RETENTION = timedelta(days=1)


def eligible(version: dict, cutoff: datetime) -> bool:
    """Preserve tagged versions and those updated within the retention buffer."""
    return version["metadata"]["container"]["tags"] == [] and (
        datetime.fromisoformat(version["updated_at"]) <= cutoff
    )


def main() -> None:
    """Collect all pages before deleting, rechecking tags and age per candidate."""
    cutoff = datetime.now(UTC) - RETENTION
    candidates = []
    page = 1
    while True:
        versions = json.loads(
            subprocess.check_output(
                ["gh", "api", f"{PACKAGE}/versions?per_page=100&page={page}"],
                text=True,
            )
        )
        candidates.extend(
            version["id"] for version in versions if eligible(version, cutoff)
        )
        if len(versions) < 100:
            break
        page += 1

    deleted = 0
    for identifier in candidates:
        endpoint = f"{PACKAGE}/versions/{identifier}"
        version = json.loads(
            subprocess.check_output(["gh", "api", endpoint], text=True)
        )
        if not eligible(version, cutoff):
            print(f"Preserving GHCR version {identifier}: it has tags or was updated.")
            continue
        subprocess.run(["gh", "api", "--method", "DELETE", endpoint], check=True)
        deleted += 1
        print(f"Deleted untagged GHCR version {identifier}.")
    print(f"Deleted {deleted} untagged GHCR version(s).")


if __name__ == "__main__":
    main()
