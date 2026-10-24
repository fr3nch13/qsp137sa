"""Test host-side devcontainer initialization without requiring Docker."""

import json
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


class DevcontainerInitializationTests(unittest.TestCase):
    def initialize(self, workspace: Path):
        config = json.loads(
            (
                Path(__file__).resolve().parents[2] / ".devcontainer/devcontainer.json"
            ).read_text()
        )
        command = [
            argument.replace("${localWorkspaceFolder}", str(workspace))
            for argument in config["initializeCommand"]
        ]
        subprocess.run(command, check=True, capture_output=True)

    def test_fresh_checkout_creates_private_empty_env(self):
        with tempfile.TemporaryDirectory(prefix="linkscope workspace ") as directory:
            workspace = Path(directory)
            self.initialize(workspace)
            env = workspace / ".env"
            self.assertEqual(env.read_bytes(), b"")
            self.assertEqual(stat.S_IMODE(env.stat().st_mode), 0o600)

    def test_repeated_initialization_preserves_existing_env(self):
        with tempfile.TemporaryDirectory(prefix="linkscope workspace ") as directory:
            workspace = Path(directory)
            env = workspace / ".env"
            contents = b"DJANGO_SECRET_KEY=local-test-value\n"
            env.write_bytes(contents)
            env.chmod(0o640)
            self.initialize(workspace)
            self.initialize(workspace)
            self.assertEqual(env.read_bytes(), contents)
            self.assertEqual(stat.S_IMODE(env.stat().st_mode), 0o640)
