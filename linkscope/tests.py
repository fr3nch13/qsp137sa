"""Smoke tests for the initial local-only Django application."""

from django.test import SimpleTestCase


class StartupTests(SimpleTestCase):
    def test_home_reports_implementation_status(self):
        response = self.client.get("/", HTTP_HOST="localhost")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "LinkScope is running.")
        self.assertContains(response, "not implemented yet")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")

    def test_unknown_host_is_rejected(self):
        response = self.client.get("/", HTTP_HOST="example.com")

        self.assertEqual(response.status_code, 400)

    def test_home_does_not_accept_post(self):
        response = self.client.post("/", HTTP_HOST="localhost")

        self.assertEqual(response.status_code, 405)
