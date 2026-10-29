"""Render GitHub release notes from the repository-root RELEASE.md template.

Usage:
    python .github/ci/generate_release.py --version VERSION --notes-file FILE
                                          [--output PATH] [--template PATH]

VERSION replaces {{VERSION}} and the contents of FILE ("-" for stdin) replace
{{RELEASE_NOTES}}. The template's leading instruction comment is
removed. The result goes to stdout, or to PATH when --output is given, ready for
`gh release create --notes-file`.

For CI jobs, each option may instead come from the environment:
    --version     RELEASE_VERSION, else GITHUB_REF_NAME on tag runs
                  (GITHUB_REF_TYPE=tag)
    --notes-file  RELEASE_NOTES_FILE
    --output      RELEASE_OUTPUT
    --template    RELEASE_TEMPLATE
When GITHUB_OUTPUT is set, `version` and (with --output) the absolute
`notes_file` path are written as step outputs. Under GitHub Actions, errors are
reported as `::error` annotations. Exit status is 0 on success, 1 on invalid
input, and 2 on usage errors.
"""

import argparse
import os
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from image_tag import SEMVER

TEMPLATE = Path(__file__).resolve().parents[2] / "RELEASE.md"
LEADING_COMMENT = re.compile(r"\A<!--.*?\n-->\n+", re.DOTALL)


def render(template: str, version: str, notes: str) -> str:
    """Fill the release template, rejecting invalid versions or unfilled placeholders."""
    if not SEMVER.fullmatch(version):
        raise ValueError(f"Version {version!r} is not a SemVer version like 1.2.3")
    if not notes.strip():
        raise ValueError("Release notes are empty")
    rendered = (
        LEADING_COMMENT.sub("", template)
        .replace("{{VERSION}}", version)
        .replace("{{RELEASE_NOTES}}", notes.strip())
    )
    leftover = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", rendered)))
    if leftover:
        raise ValueError(f"Unfilled template placeholders: {', '.join(leftover)}")
    return rendered


def default_version(env: Mapping[str, str]) -> str | None:
    """Return the version from RELEASE_VERSION, or the ref name on tag runs."""
    if env.get("RELEASE_VERSION"):
        return env["RELEASE_VERSION"]
    if env.get("GITHUB_REF_TYPE") == "tag":
        return env.get("GITHUB_REF_NAME") or None
    return None


def report_error(message: str, env: Mapping[str, str]) -> None:
    """Print an error, as a workflow annotation when running in GitHub Actions."""
    if env.get("GITHUB_ACTIONS") == "true":
        escaped = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::error title=Release notes::{escaped}", file=sys.stderr)
    else:
        print(f"error: {message}", file=sys.stderr)


def main(
    argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None
) -> int:
    """Render release notes from arguments or CI environment; return the exit status."""
    env = os.environ if env is None else env
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--version",
        default=default_version(env),
        help="SemVer release tag without a 'v' prefix",
    )
    parser.add_argument(
        "--notes-file",
        default=env.get("RELEASE_NOTES_FILE") or None,
        help="Markdown for {{RELEASE_NOTES}}, or '-' for stdin",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=env.get("RELEASE_OUTPUT") or None,
        help="Write here instead of stdout",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=env.get("RELEASE_TEMPLATE") or TEMPLATE,
        help="Release template (default: repository-root RELEASE.md)",
    )
    args = parser.parse_args(argv)
    if not args.version or not args.notes_file:
        parser.error("--version and --notes-file are required (as options or env)")

    try:
        notes = (
            sys.stdin.read()
            if args.notes_file == "-"
            else Path(args.notes_file).read_text()
        )
        rendered = render(Path(args.template).read_text(), args.version, notes)
        if args.output:
            output = Path(args.output).resolve()
            output.write_text(rendered)
        else:
            sys.stdout.write(rendered)
        if env.get("GITHUB_OUTPUT"):
            with open(env["GITHUB_OUTPUT"], "a") as step_output:
                step_output.write(f"version={args.version}\n")
                if args.output:
                    step_output.write(f"notes_file={output}\n")
    except (OSError, ValueError) as error:
        report_error(str(error), env)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
