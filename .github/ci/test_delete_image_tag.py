"""Verify that image cleanup cannot delete unrelated image tags."""

import json
import subprocess
import unittest
from unittest.mock import patch

from delete_image_tag import deletion_candidates, main


def version(identifier: int, tags: list[str]) -> dict:
    return {"id": identifier, "metadata": {"container": {"tags": tags}}}


class DeletionTests(unittest.TestCase):
    def test_missing_tag(self):
        self.assertEqual(deletion_candidates([version(1, ["main"])], "feature"), [])

    def test_matching_versions(self):
        self.assertEqual(
            deletion_candidates(
                [
                    version(1, ["feature"]),
                    version(2, ["main"]),
                    version(3, ["feature"]),
                ],
                "feature",
            ),
            [1, 3],
        )

    def test_shared_version_is_protected(self):
        with self.assertRaises(ValueError):
            deletion_candidates([version(1, ["feature", "v1.0"])], "feature")


@patch.dict("os.environ", {"GITHUB_EVENT_PATH": "/tmp/event.json"})
class CleanupApiTests(unittest.TestCase):
    @patch("delete_image_tag.Path.read_text")
    @patch("delete_image_tag.subprocess.run")
    @patch("delete_image_tag.subprocess.check_output")
    def test_all_pages_are_checked(self, api, delete, event):
        event.return_value = json.dumps({"ref": "feature/ui", "ref_type": "branch"})
        api.side_effect = [
            json.dumps([[], [{"name": "qsp137sa"}]]),
            json.dumps([[version(1, ["main"])], [version(2, ["feature-ui"])]]),
        ]
        main()
        delete.assert_called_once_with(
            [
                "gh",
                "api",
                "--method",
                "DELETE",
                "users/fr3nch13/packages/container/qsp137sa/versions/2",
            ],
            check=True,
        )

    @patch("delete_image_tag.Path.read_text")
    @patch("delete_image_tag.subprocess.run")
    @patch("delete_image_tag.subprocess.check_output", return_value="[]")
    def test_missing_package_is_noop(self, api, delete, event):
        event.return_value = json.dumps({"ref": "v1.0", "ref_type": "tag"})
        main()
        api.assert_called_once()
        delete.assert_not_called()

    @patch("delete_image_tag.Path.read_text")
    @patch("delete_image_tag.subprocess.run")
    @patch("delete_image_tag.subprocess.check_output")
    def test_api_errors_propagate(self, api, delete, event):
        event.return_value = json.dumps({"ref": "v1.0", "ref_type": "tag"})
        api.side_effect = subprocess.CalledProcessError(1, "gh")
        with self.assertRaises(subprocess.CalledProcessError):
            main()
        delete.assert_not_called()

    @patch("delete_image_tag.Path.read_text")
    @patch("delete_image_tag.subprocess.run")
    @patch("delete_image_tag.subprocess.check_output")
    def test_no_delete_when_any_version_is_shared(self, api, delete, event):
        event.return_value = json.dumps({"ref": "feature", "ref_type": "branch"})
        api.side_effect = [
            json.dumps([[{"name": "qsp137sa"}]]),
            json.dumps([[version(1, ["feature"]), version(2, ["feature", "v1"])]]),
        ]
        with self.assertRaises(ValueError):
            main()
        delete.assert_not_called()

    @patch("delete_image_tag.Path.read_text")
    @patch("delete_image_tag.subprocess.check_output")
    def test_persistent_branches_are_protected(self, api, event):
        for ref in ("main", "dev"):
            with self.subTest(ref=ref):
                event.return_value = json.dumps({"ref": ref, "ref_type": "branch"})
                with self.assertRaises(ValueError):
                    main()
        api.assert_not_called()
