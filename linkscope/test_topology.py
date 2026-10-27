"""Verify real-input invariants and file/row diagnostics independently."""

import hashlib
import tempfile
from pathlib import Path
from unittest import TestCase

from linkscope.topology import InputError, load_topology

DATA = Path(__file__).resolve().parent.parent / "data"


class TopologyTests(TestCase):
    def test_real_baseline(self):
        topology = load_topology()
        self.assertEqual(len(topology.nodes), 37)
        self.assertEqual(len(topology.links), 55)
        self.assertEqual(len(topology.demands), 391)
        self.assertEqual(sum(d.units for d in topology.demands), 2068)
        self.assertEqual(len({n.id for n in topology.nodes}), 37)
        self.assertEqual(len({e.id for e in topology.links}), 55)
        self.assertEqual(len({d.id for d in topology.demands}), 391)
        self.assertEqual(
            hashlib.sha256((DATA / "nobel-eu.txt").read_bytes()).hexdigest(),
            "2170d1f8d2b481dca907b4c17c33e292fd06a05bfef279e0d31f2f1f659bdfd0",
        )
        backbone = [n for n in topology.nodes if n.kind == "backbone"]
        self.assertEqual(len(backbone), 28)
        self.assertTrue(all(n.transit for n in backbone))
        nodes = {n.id: n for n in topology.nodes}
        self.assertEqual(
            (nodes["Amsterdam"].longitude, nodes["Amsterdam"].latitude), (4.51, 52.20)
        )
        self.assertTrue(nodes["HUB-EAST"].transit)
        self.assertFalse(nodes["DC-NORTH"].transit)
        self.assertFalse(nodes["OPS-EAST-1"].transit)
        self.assertLess(
            abs(nodes["OPS-EAST-1"].longitude - nodes["HUB-EAST"].longitude), 1
        )
        self.assertEqual({e.capacity for e in topology.links[:41]}, {550})
        self.assertEqual(
            {e.capacity for e in topology.links if e.source == "DC-NORTH"}, {200}
        )
        extra = topology.demands[378:]
        self.assertEqual(len(extra), 13)
        self.assertEqual(sum(d.units for d in extra), 170)
        operations = {n.id for n in topology.nodes if n.kind == "operations-site"}
        self.assertEqual(len(operations), 6)
        self.assertEqual(
            {(d.source, d.target, d.units) for d in extra[:-1]},
            {
                (site, center, 10)
                for site in operations
                for center in ("DC-NORTH", "DC-SOUTH")
            },
        )
        self.assertEqual(
            (extra[-1].source, extra[-1].target, extra[-1].units),
            ("DC-NORTH", "DC-SOUTH", 50),
        )
        for record in (*topology.links, *topology.demands):
            self.assertIn(record.source, nodes)
            self.assertIn(record.target, nodes)

    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for name in ("nobel-eu.txt", "sites.csv"):
            (root / name).write_bytes((DATA / name).read_bytes())
        return root / "nobel-eu.txt", root / "sites.csv"

    def test_site_order_independent(self):
        backbone, sites = self.fixture()
        lines = sites.read_text().splitlines()
        sites.write_text("\n".join([lines[0], *reversed(lines[1:])]) + "\n")
        actual = load_topology(backbone, sites)
        expected = load_topology()
        self.assertEqual(
            {(e.source, e.target, e.capacity) for e in actual.links},
            {(e.source, e.target, e.capacity) for e in expected.links},
        )
        self.assertEqual(
            set(actual.nodes),
            set(expected.nodes),
        )

    def test_merge_never_modifies_either_input(self):
        backbone, sites = self.fixture()
        original = (backbone.read_bytes(), sites.read_bytes())
        first = load_topology(backbone, sites)
        self.assertEqual(first, load_topology(backbone, sites))
        self.assertEqual((backbone.read_bytes(), sites.read_bytes()), original)

    def test_small_network_has_independently_expected_merge(self):
        backbone, sites = self.fixture()
        backbone.write_text(
            "NODES (\nA ( 1 1 )\nB ( 2 2 )\n)\n"
            "LINKS (\nAB ( A B ) 0 0 0 0 ( 999 1 )\n)\n"
            "DEMANDS (\nD ( A B ) 1 7 UNLIMITED\n)\n"
        )
        sites.write_text(
            "site_id,site_type,attaches_to,access_capacity\n"
            "OPS,operations-site,HUB,40\n"
            "NORTH,data-center,A,200\n"
            "SOUTH,data-center,B,200\n"
            "HUB,aggregation-hub,A,80\n"
        )
        topology = load_topology(backbone, sites)
        self.assertEqual(len(topology.nodes), 6)
        self.assertEqual(len(topology.links), 5)
        self.assertEqual(len(topology.demands), 4)
        self.assertEqual(sum(d.units for d in topology.demands), 77)
        self.assertEqual(topology.links[0].capacity, 550)
        self.assertEqual(
            {(d.source, d.target, d.units) for d in topology.demands},
            {
                ("A", "B", 7),
                ("OPS", "NORTH", 10),
                ("OPS", "SOUTH", 10),
                ("NORTH", "SOUTH", 50),
            },
        )

    def test_invalid_sites_name_file_and_row(self):
        for original, replacement, row in (
            ("DC-NORTH,data-center", "Amsterdam,data-center", 2),
            ("DC-SOUTH,data-center", "DC-NORTH,data-center", 3),
            ("DC-NORTH,data-center", "DC-NORTH,unknown", 2),
            ("Hamburg;Copenhagen", "Hamburg;Missing", 2),
            ("Hamburg;Copenhagen", "Hamburg;Hamburg", 2),
            ("Hamburg;Copenhagen", "DC-NORTH", 2),
            ("Hamburg;Copenhagen", "", 2),
            ("Hamburg;Copenhagen", "Hamburg;", 2),
            (",200", ",nan", 2),
            (",200", ",0", 2),
            (",200", ",-1", 2),
            (",200", ",not-a-number", 2),
            ("site_id,site_type", "wrong,header", 1),
        ):
            with self.subTest(replacement=replacement):
                backbone, sites = self.fixture()
                sites.write_text(sites.read_text().replace(original, replacement, 1))
                with self.assertRaisesRegex(InputError, rf"sites.csv: row {row}:"):
                    load_topology(backbone, sites)

    def test_invalid_backbone_names_file_and_row(self):
        for original, replacement in (
            ("Amsterdam ( 4.51 52.20 )", "Amsterdam ( nan 52.20 )"),
            ("Amsterdam ( 4.51 52.20 )", "Amsterdam ( 4.51 100 )"),
            ("Athens ( 23.42 37.58 )", "Amsterdam ( 23.42 37.58 )"),
            ("L1 ( Amsterdam Brussels )", "L1 ( Amsterdam Missing )"),
            ("L1 ( Amsterdam Brussels )", "L1 ( Amsterdam Amsterdam )"),
            ("L2 ( Amsterdam Glasgow )", "L1 ( Amsterdam Glasgow )"),
            ("L2 ( Amsterdam Glasgow )", "L2 ( Brussels Amsterdam )"),
            ("1 6.00 UNLIMITED", "1 -6.00 UNLIMITED"),
            ("1 6.00 UNLIMITED", "1 nan UNLIMITED"),
            ("1 6.00 UNLIMITED", "broken"),
            (
                "AmsterdamBarcelona ( Amsterdam Barcelona )",
                "AmsterdamAthens ( Amsterdam Barcelona )",
            ),
            (
                "AmsterdamBarcelona ( Amsterdam Barcelona )",
                "AmsterdamBarcelona ( Athens Amsterdam )",
            ),
            ("0.00 0.00 0.00 0.00", "-1 0.00 0.00 0.00"),
        ):
            with self.subTest(replacement=replacement):
                backbone, sites = self.fixture()
                text = backbone.read_text()
                index = text.index(original)
                row = text[:index].count("\n") + 1
                backbone.write_text(text.replace(original, replacement, 1))
                with self.assertRaisesRegex(InputError, rf"nobel-eu.txt: row {row}:"):
                    load_topology(backbone, sites)

    def test_missing_and_truncated_files_are_explicit(self):
        backbone, sites = self.fixture()
        with self.assertRaisesRegex(InputError, "missing.txt: row 1:"):
            load_topology(backbone.with_name("missing.txt"), sites)
        backbone.write_text("NODES (\n A ( 1 1 )\n")
        with self.assertRaisesRegex(InputError, "nobel-eu.txt: row 2:"):
            load_topology(backbone, sites)

    def test_site_component_without_backbone_is_rejected(self):
        backbone, sites = self.fixture()
        sites.write_text(
            sites.read_text()
            .replace("Hamburg;Copenhagen", "OPS-WEST")
            .replace(
                "OPS-WEST,operations-site,Dublin",
                "OPS-WEST,operations-site,OPS-SOUTHEAST",
            )
            .replace(
                "OPS-SOUTHEAST,operations-site,Athens",
                "OPS-SOUTHEAST,operations-site,DC-NORTH",
            )
        )
        with self.assertRaisesRegex(InputError, "sites.csv: row 2:.*no backbone"):
            load_topology(backbone, sites)
