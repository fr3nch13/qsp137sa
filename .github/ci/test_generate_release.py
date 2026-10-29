"""Test release-notes rendering from the RELEASE.md template."""

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from generate_release import TEMPLATE, main, render

SAMPLE = (
    "<!--\nUse {{VERSION}} here.\n-->\n\n## {{VERSION}} Notes\n\n{{RELEASE_NOTES}}\n"
)


class RenderTests(unittest.TestCase):
    def test_fills_placeholders_and_drops_comment(self):
        self.assertEqual(
            render(SAMPLE, "1.2.3", "- Fixed it.\n"), "## 1.2.3 Notes\n\n- Fixed it.\n"
        )

    def test_rejects_non_semver_version(self):
        for version in ("v1.2.3", "1.2", "main"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                render(SAMPLE, version, "notes")

    def test_rejects_empty_notes(self):
        with self.assertRaises(ValueError):
            render(SAMPLE, "1.2.3", " \n")

    def test_rejects_unknown_placeholder(self):
        with self.assertRaisesRegex(ValueError, "{{OTHER}}"):
            render(SAMPLE + "{{OTHER}}\n", "1.2.3", "notes")

    def test_repository_template_renders(self):
        rendered = render(TEMPLATE.read_text(), "1.2.3", "- Notes.")
        self.assertIn("ghcr.io/fr3nch13/qsp137sa:1.2.3", rendered)
        self.assertIn("127.0.0.1:2158", rendered)
        self.assertNotIn("<!--", rendered)


class MainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.template = self.tmp / "RELEASE.md"
        self.template.write_text(SAMPLE)
        self.notes = self.tmp / "notes.md"
        self.notes.write_text("- Fixed it.\n")
        self.output = self.tmp / "out.md"
        self.step_output = self.tmp / "github_output"

    def ci_env(self, **extra):
        return {
            "GITHUB_ACTIONS": "true",
            "GITHUB_OUTPUT": str(self.step_output),
            "RELEASE_TEMPLATE": str(self.template),
            **extra,
        }

    def test_tag_run_reads_inputs_from_environment(self):
        env = self.ci_env(
            GITHUB_REF_TYPE="tag",
            GITHUB_REF_NAME="1.2.3",
            RELEASE_NOTES_FILE=str(self.notes),
            RELEASE_OUTPUT=str(self.output),
        )
        self.assertEqual(main([], env), 0)
        self.assertEqual(self.output.read_text(), "## 1.2.3 Notes\n\n- Fixed it.\n")
        self.assertEqual(
            self.step_output.read_text(),
            f"version=1.2.3\nnotes_file={self.output.resolve()}\n",
        )

    def test_branch_ref_is_not_used_as_version(self):
        env = self.ci_env(GITHUB_REF_TYPE="branch", GITHUB_REF_NAME="main")
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exit:
            main(["--notes-file", str(self.notes)], env)
        self.assertEqual(exit.exception.code, 2)

    def test_arguments_override_environment(self):
        env = self.ci_env(RELEASE_VERSION="9.9.9")
        args = ["--version", "1.2.3", "--notes-file", str(self.notes)]
        args += ["--output", str(self.output)]
        self.assertEqual(main(args, env), 0)
        self.assertIn("## 1.2.3 Notes", self.output.read_text())

    def test_reads_notes_from_stdin(self):
        stdout = io.StringIO()
        with (
            patch("sys.stdin", io.StringIO("- From stdin.\n")),
            redirect_stdout(stdout),
        ):
            self.assertEqual(
                main(["--notes-file", "-"], self.ci_env(RELEASE_VERSION="1.2.3")), 0
            )
        self.assertIn("- From stdin.", stdout.getvalue())
        self.assertEqual(self.step_output.read_text(), "version=1.2.3\n")

    def test_invalid_input_emits_annotation(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(
                main(
                    ["--version", "v1.2.3", "--notes-file", str(self.notes)],
                    self.ci_env(),
                ),
                1,
            )
        self.assertTrue(stderr.getvalue().startswith("::error title=Release notes::"))
        self.assertFalse(self.step_output.exists())


if __name__ == "__main__":
    unittest.main()
