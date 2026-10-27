"""Verify same-origin frontend serving and the minimal API with debug disabled."""

from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import Client, SimpleTestCase


class ServingTests(SimpleTestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "assets").mkdir()
        (self.root / "index.html").write_text(
            '<!doctype html><title>LinkScope</title><div id="root"></div>'
        )
        (self.root / "assets" / "app.js").write_text('console.log("fixture");')
        (self.root / "assets" / "app.css").write_text("body { margin: 0; }")
        (self.root / "assets" / "logo.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"></svg>'
        )
        self.override = self.settings(
            FRONTEND_DIR=self.root,
            STATIC_ROOT=self.root / "assets",
            DEBUG=False,
        )
        self.override.enable()
        self.addCleanup(self.override.disable)

    def test_home_serves_html_without_caching(self):
        response = self.client.get("/", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="root"', b"".join(response.streaming_content).decode())
        self.assertIn("text/html", response["Content-Type"])
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(response["X-Frame-Options"], "DENY")

    def test_assets_revalidate_and_observe_rebuilds(self):
        for asset, content_type in (("app.js", "javascript"), ("app.css", "text/css")):
            response = self.client.get(f"/assets/{asset}", HTTP_HOST="localhost")
            self.assertEqual(response.status_code, 200)
            self.assertIn(content_type, response["Content-Type"])
            self.assertIn("max-age=0", response["Cache-Control"])
            response.close()
        (self.root / "assets" / "app.js").write_text("updated")
        response = self.client.get("/assets/app.js", HTTP_HOST="localhost")
        self.assertEqual(b"".join(response.streaming_content), b"updated")

    def test_api_contract(self):
        for path in ("/api", "/api/"):
            response = self.client.get(path, HTTP_HOST="localhost")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"message": "Hello, world!"})
            self.assertEqual(response["Content-Type"], "application/json")
            self.assertIn("no-store", response["Cache-Control"])
        response = self.client.head("/api", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")

    def test_favicon_redirects_to_svg_asset(self):
        response = self.client.get("/favicon.ico", HTTP_HOST="localhost")
        self.assertRedirects(
            response, "/assets/logo.svg", fetch_redirect_response=False
        )
        response = self.client.get("/assets/logo.svg", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        self.assertIn("image/svg+xml", response["Content-Type"])
        response.close()

    def test_api_method_and_missing_endpoint_errors(self):
        response = self.client.post("/api", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {"error": "Method not allowed."})
        self.assertEqual(response["Allow"], "GET, HEAD")
        response = self.client.get("/api/unknown", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "API endpoint not found."})

    def test_api_rejects_unsupported_methods_with_csrf_enforced(self):
        client = Client(enforce_csrf_checks=True)
        for path in ("/api", "/api/"):
            for method in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS"):
                with self.subTest(path=path, method=method):
                    response = client.generic(method, path, HTTP_HOST="localhost")
                    self.assertEqual(response.status_code, 405)
                    self.assertEqual(response["Content-Type"], "application/json")
                    self.assertEqual(response.json(), {"error": "Method not allowed."})
                    self.assertEqual(response["Allow"], "GET, HEAD")
                    self.assertIn("no-store", response["Cache-Control"])

    def test_csrf_protection_remains_enabled_for_other_views(self):
        response = Client(enforce_csrf_checks=True).post("/", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 403)

    def test_missing_resources_never_return_frontend_html(self):
        for path in ("/assets/missing.js", "/unknown", "/assets/../index.html"):
            response = self.client.get(path, HTTP_HOST="localhost")
            self.assertEqual(response.status_code, 404)
            self.assertNotContains(response, 'id="root"', status_code=404)

    def test_missing_frontend_build_reports_failure(self):
        (self.root / "index.html").unlink()
        with self.assertLogs("linkscope.views", level="ERROR"):
            response = self.client.get("/", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 503)

    def test_unknown_host_is_rejected(self):
        response = self.client.get("/", HTTP_HOST="example.com")
        self.assertEqual(response.status_code, 400)

    def test_home_does_not_accept_post(self):
        response = self.client.post("/", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 405)
