"""Verify the runtime warning guards embedded before JavaScript Actions."""

import os
import shutil
import subprocess
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


@unittest.skipUnless(shutil.which("node"), "Node is required for runtime guard tests")
class NodeWarningPolicyTests(unittest.TestCase):
    def test_workflow_guards_reject_warnings_but_allow_clean_commands(self):
        workflows = Path(__file__).resolve().parents[1] / "workflows"
        for name in ("ci.yml", "delete-image.yml"):
            source = (workflows / name).read_text()
            script = textwrap.dedent(
                source.split("<<'JS'\n", 1)[1].split("\n          JS", 1)[0]
            )
            with TemporaryDirectory() as directory:
                guard = Path(directory) / "guard.cjs"
                guard.write_text(script)
                environment = dict(os.environ, NODE_OPTIONS=f"--require={guard}")
                for command, expected in (
                    ("console.log('success')", 0),
                    ("process.emitWarning('test warning')", 1),
                    ("process.emitWarning('deprecated', 'DeprecationWarning')", 1),
                    ("process.emitWarning('experimental', 'ExperimentalWarning')", 1),
                    ("Buffer('deprecated constructor')", 1),
                ):
                    with self.subTest(workflow=name, command=command):
                        result = subprocess.run(
                            ["node", "-e", command],
                            env=environment,
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        self.assertEqual(result.returncode, expected, result.stderr)
                        if expected:
                            self.assertIn("Warning", result.stderr)
