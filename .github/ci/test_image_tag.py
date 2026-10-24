"""Test event tag selection and Docker tag collision protection."""

import unittest

from image_tag import image_tag


class ImageTagTests(unittest.TestCase):
    def test_main_push(self):
        self.assertEqual(image_tag("push", "main", ["main", "dev"], []), "main")

    def test_dev_pr_publishes_dev(self):
        self.assertEqual(image_tag("pull_request", "dev", ["main", "dev"], []), "dev")

    def test_main_pr_is_test_only(self):
        self.assertIsNone(image_tag("pull_request", "main", ["main", "dev"], []))

    def test_release(self):
        for version in ("2.4.11", "0.1.0", "1.0.0-rc.1", "1.0.0-alpha-2.x"):
            with self.subTest(version=version):
                self.assertEqual(
                    image_tag("tag", version, ["main"], [version]), version
                )

    def test_release_must_be_semver(self):
        for ref in (
            "main",
            "dev",
            "v1.2.3",
            "1.2",
            "01.2.3",
            "1.2.3+build",
            "release/1.2.3",
        ):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                image_tag("tag", ref, ["main", "dev"], [ref])

    def test_branch_normalization(self):
        self.assertEqual(
            image_tag("pull_request", "Feature/Web_UI", ["main", "Feature/Web_UI"], []),
            "feature-web_ui",
        )

    def test_reserved_branch_tags(self):
        for ref in ("MAIN", "Dev"):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                image_tag("pull_request", ref, [], [])

    def test_branch_collision(self):
        with self.assertRaises(ValueError):
            image_tag("pull_request", "feature/ui", ["feature-ui"], [])

    def test_release_collision(self):
        with self.assertRaises(ValueError):
            image_tag("pull_request", "v1.0", [], ["v1.0"])
        with self.assertRaises(ValueError):
            image_tag("push", "v1.0", ["v1.0"], ["v1.0"])

    def test_invalid_tags(self):
        for event, ref in [
            ("push", "release/1"),
            ("push", "-invalid"),
            ("push", "a" * 129),
            ("pull_request", "a" * 129),
        ]:
            with self.subTest(event=event, ref=ref), self.assertRaises(ValueError):
                image_tag(event, ref, [], [])
