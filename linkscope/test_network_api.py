"""Verify the analysis JSON contract, request isolation, and explicit failures."""

from pathlib import Path
from unittest.mock import patch

import networkx as nx
from django.test import Client, SimpleTestCase

from linkscope.topology import InputError


class NetworkAPITests(SimpleTestCase):
    def get(self, path, **parameters):
        return self.client.get(path, parameters, HTTP_HOST="localhost")

    def test_network_contract_and_baseline(self):
        response = self.get("/api/network")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertIn("no-store", response["Cache-Control"])
        data = response.json()
        self.assertEqual(
            set(data), {"nodes", "links", "demands", "baseline", "criticality"}
        )
        self.assertEqual(
            (len(data["nodes"]), len(data["links"]), len(data["demands"])),
            (37, 55, 391),
        )
        self.assertEqual(sum(d["units"] for d in data["demands"]), 2068)
        self.assertEqual(
            set(data["nodes"][0]), {"id", "kind", "longitude", "latitude", "transit"}
        )
        self.assertEqual(set(data["links"][0]), {"id", "source", "target", "capacity"})
        self.assertEqual(len(data["criticality"]), 92)
        self.assertEqual(
            set(data["criticality"][0]), {"kind", "id", "critical", "reasons"}
        )
        self.assertEqual(sum(r["critical"] for r in data["criticality"]), 43)
        baseline = data["baseline"]
        self.assertEqual(baseline, self.get("/api/analysis").json())
        self.assertEqual(
            set(baseline),
            {
                "failure",
                "links",
                "top_five",
                "undeliverable",
                "failed_endpoint_demands",
                "overloaded",
                "disconnected",
            },
        )
        self.assertIsNone(baseline["failure"])
        self.assertFalse(baseline["disconnected"])
        self.assertEqual(baseline["undeliverable"], [])
        self.assertEqual(baseline["failed_endpoint_demands"], [])
        self.assertEqual(baseline["overloaded"], [])
        self.assertEqual(
            [link["id"] for link in baseline["top_five"]],
            ["L12", "L3", "L26", "L30", "L13"],
        )
        self.assertEqual(
            set(baseline["links"][0]),
            {"id", "source", "target", "capacity", "load", "utilization_percent"},
        )

    def test_link_failure_and_node_endpoint_separation(self):
        response = self.get("/api/analysis", kind="link", id="L12")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["failure"], {"kind": "link", "id": "L12"})
        self.assertEqual(data["failed_endpoint_demands"], [])
        self.assertEqual(data["undeliverable"], [])
        self.assertNotIn("L12", [link["id"] for link in data["links"]])
        self.assertEqual([link["id"] for link in data["overloaded"]], ["L26"])
        self.assertAlmostEqual(
            data["overloaded"][0]["utilization_percent"], 128.295317, delta=0.000001
        )
        data = self.get("/api/analysis", kind="node", id="Hamburg").json()
        self.assertEqual(sum(d["units"] for d in data["failed_endpoint_demands"]), 162)
        self.assertEqual(data["undeliverable"], [])
        self.assertTrue(
            all("Hamburg" not in (e["source"], e["target"]) for e in data["links"])
        )
        data = self.get("/api/analysis", kind="node", id="HUB-EAST").json()
        self.assertTrue(data["disconnected"])
        self.assertEqual(data["failed_endpoint_demands"], [])
        self.assertEqual(sum(d["units"] for d in data["undeliverable"]), 20)
        self.assertEqual(
            set(data["undeliverable"][0]), {"id", "source", "target", "units"}
        )

    def test_restore_and_independent_clients(self):
        baseline = self.get("/api/analysis").json()
        self.get("/api/analysis", kind="node", id="Hamburg")
        self.assertEqual(
            Client().get("/api/analysis", HTTP_HOST="localhost").json(), baseline
        )
        self.get("/api/analysis", kind="link", id="L26")
        self.assertEqual(self.get("/api/analysis").json(), baseline)

    def test_invalid_queries(self):
        for path in (
            "/api/analysis?kind=node",
            "/api/analysis?id=Hamburg",
            "/api/analysis?kind=other&id=Hamburg",
            "/api/analysis?kind=node&id=",
            "/api/analysis?kind=node&kind=link&id=L12",
            "/api/analysis?kind=node&id=Hamburg&id=Berlin",
            "/api/analysis?unexpected=1",
            "/api/network?kind=node&id=Hamburg",
        ):
            with self.subTest(path=path):
                response = self.get(path)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(set(response.json()), {"error"})
        for kind in ("node", "link"):
            response = self.get("/api/analysis", kind=kind, id="missing")
            self.assertEqual(response.status_code, 404)
            self.assertIn("Unknown", response.json()["error"])

    def test_read_only_methods_even_with_csrf_enforced(self):
        client = Client(enforce_csrf_checks=True)
        for path in ("/api/network", "/api/analysis"):
            for method in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS"):
                with self.subTest(path=path, method=method):
                    with patch("linkscope.network_api.load_topology") as load:
                        response = client.generic(method, path, HTTP_HOST="localhost")
                    load.assert_not_called()
                    self.assertEqual(response.status_code, 405)
                    self.assertEqual(response.json(), {"error": "Method not allowed."})
                    self.assertEqual(response["Allow"], "GET, HEAD")
                    self.assertIn("no-store", response["Cache-Control"])
        response = client.head("/api/analysis", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")

    def test_load_and_analysis_errors_are_logged_json_not_empty_success(self):
        for path in ("/api/network", "/api/analysis"):
            with (
                patch(
                    "linkscope.network_api.load_topology",
                    side_effect=InputError(Path("sites.csv"), 3, "bad capacity"),
                ),
                self.assertLogs("linkscope.network_api", level="ERROR"),
            ):
                response = self.get(path)
            self.assertEqual(response.status_code, 503)
            self.assertIn("sites.csv: row 3:", response.json()["error"])
        with (
            patch(
                "linkscope.network_api.route_traffic",
                side_effect=nx.NetworkXError("bad"),
            ),
            self.assertLogs("linkscope.network_api", level="ERROR"),
        ):
            response = self.get("/api/analysis")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"error": "Network analysis failed."})
        with (
            patch(
                "linkscope.network_api.analyze_failure",
                side_effect=nx.NetworkXError("bad"),
            ),
            self.assertLogs("linkscope.network_api", level="ERROR"),
        ):
            response = self.get("/api/analysis", kind="link", id="L12")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"error": "Network analysis failed."})
