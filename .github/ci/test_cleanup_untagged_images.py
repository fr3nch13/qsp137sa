"""Verify untagged cleanup pagination, tagged-image protection, and API failures."""

import json
import subprocess
import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import call, patch

from cleanup_untagged_images import PACKAGE, eligible, main


def version(
    identifier: int, tags: list[str], updated_at: str = "2020-01-01T00:00:00Z"
) -> dict:
    return {
        "id": identifier,
        "metadata": {"container": {"tags": tags}},
        "updated_at": updated_at,
    }


class RetentionTests(unittest.TestCase):
    def test_exact_24_hour_boundary(self):
        now = datetime(2026, 10, 27, 12, tzinfo=UTC)
        cutoff = now - timedelta(days=1)
        for offset, expected in ((-1, True), (0, True), (1, False)):
            with self.subTest(offset=offset):
                updated_at = (cutoff + timedelta(seconds=offset)).isoformat()
                self.assertEqual(eligible(version(1, [], updated_at), cutoff), expected)

    def test_invalid_timestamp_fails_explicitly(self):
        with self.assertRaises(ValueError):
            eligible(version(1, [], "invalid"), datetime.now(UTC))


@patch("cleanup_untagged_images.subprocess.run")
@patch("cleanup_untagged_images.subprocess.check_output")
class CleanupTests(unittest.TestCase):
    def test_only_untagged_versions_are_deleted(self, api, delete):
        api.side_effect = [
            json.dumps(
                [
                    version(1, ["main"]),
                    version(2, ["dev"]),
                    version(3, ["feature-ui"]),
                    version(4, ["1.2.3"]),
                    version(5, ["main", "1.2.4"]),
                    version(6, []),
                ]
            ),
            json.dumps(version(6, [])),
        ]
        main()
        delete.assert_called_once_with(
            ["gh", "api", "--method", "DELETE", f"{PACKAGE}/versions/6"], check=True
        )

    def test_all_pages_are_collected_before_deletion(self, api, delete):
        api.side_effect = [
            json.dumps([version(identifier, []) for identifier in range(100)]),
            json.dumps([version(100, [])]),
            *(json.dumps(version(identifier, [])) for identifier in range(101)),
        ]

        def verify_listing_finished(*args, **kwargs):
            self.assertIn(
                call(
                    ["gh", "api", f"{PACKAGE}/versions?per_page=100&page=2"],
                    text=True,
                ),
                api.call_args_list,
            )

        delete.side_effect = verify_listing_finished
        main()
        self.assertEqual(delete.call_count, 101)
        self.assertEqual(
            delete.call_args_list[-1],
            call(
                ["gh", "api", "--method", "DELETE", f"{PACKAGE}/versions/100"],
                check=True,
            ),
        )

    def test_newly_tagged_version_is_preserved(self, api, delete):
        api.side_effect = [
            json.dumps([version(1, [])]),
            json.dumps(version(1, ["main"])),
        ]
        main()
        delete.assert_not_called()

    def test_recent_version_is_not_a_candidate(self, api, delete):
        api.return_value = json.dumps([version(1, [], datetime.now(UTC).isoformat())])
        main()
        api.assert_called_once()
        delete.assert_not_called()

    def test_recently_updated_candidate_is_preserved(self, api, delete):
        api.side_effect = [
            json.dumps([version(1, [])]),
            json.dumps(version(1, [], datetime.now(UTC).isoformat())),
        ]
        main()
        delete.assert_not_called()

    def test_no_candidates_is_noop(self, api, delete):
        for versions in ([], [version(1, ["main"])]):
            with self.subTest(versions=versions):
                api.return_value = json.dumps(versions)
                main()
                delete.assert_not_called()

    def test_listing_error_prevents_deletion(self, api, delete):
        api.side_effect = [
            json.dumps([version(identifier, []) for identifier in range(100)]),
            subprocess.CalledProcessError(1, "gh"),
        ]
        with self.assertRaises(subprocess.CalledProcessError):
            main()
        delete.assert_not_called()

    def test_recheck_error_prevents_deletion(self, api, delete):
        api.side_effect = [
            json.dumps([version(1, [])]),
            subprocess.CalledProcessError(1, "gh"),
        ]
        with self.assertRaises(subprocess.CalledProcessError):
            main()
        delete.assert_not_called()

    def test_delete_error_is_not_silenced(self, api, delete):
        api.side_effect = [
            json.dumps([version(1, [])]),
            json.dumps(version(1, [])),
        ]
        delete.side_effect = subprocess.CalledProcessError(1, "gh")
        with self.assertRaises(subprocess.CalledProcessError):
            main()


if __name__ == "__main__":
    unittest.main()
