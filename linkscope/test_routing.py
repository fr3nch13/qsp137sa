"""Hand-calculated routing cases and real-network reproducibility checks."""

from unittest import TestCase

from linkscope.routing import route_traffic
from linkscope.topology import Demand, Link, Node, Topology, load_topology


class RoutingTests(TestCase):
    def network(self, edges, demands, kinds=None, capacities=None, isolated=()):
        kinds = kinds or {}
        capacities = capacities or {}
        names = sorted({name for edge in edges for name in edge} | set(isolated))
        return Topology(
            tuple(Node(name, kinds.get(name, "backbone"), 0, 0) for name in names),
            tuple(
                Link(f"{a}-{b}", a, b, capacities.get(f"{a}-{b}", 100))
                for a, b in edges
            ),
            tuple(
                Demand(f"d{i}", a, b, units) for i, (a, b, units) in enumerate(demands)
            ),
        )

    def loads(self, result):
        return {item.link.id: item.load for item in result.links}

    def test_unique_route_is_minimum_hops_not_capacity_weighted(self):
        topology = self.network(
            [("A", "B"), ("A", "C"), ("C", "B")],
            [("A", "B", 12)],
            capacities={"A-B": 1},
        )
        result = route_traffic(topology)
        self.assertEqual(self.loads(result), {"A-B": 12, "A-C": 0, "C-B": 0})
        self.assertEqual(result.top_five[0].utilization_percent, 1200)
        self.assertEqual(result.undeliverable, ())

    def test_equal_paths_and_reverse_demands_share_undirected_load(self):
        topology = self.network(
            [("A", "B"), ("B", "T"), ("A", "C"), ("C", "T")],
            [("A", "T", 10), ("T", "A", 6)],
        )
        result = route_traffic(topology)
        self.assertTrue(all(item.load == 8 for item in result.links))
        self.assertEqual(sum(item.load for item in result.links), 16 * 2)

    def test_equal_complete_paths_not_equal_next_hops(self):
        # Three paths: A-B-D-T, A-B-E-T, A-C-F-T, each carrying 4 units.
        topology = self.network(
            [
                ("A", "B"),
                ("B", "D"),
                ("D", "T"),
                ("B", "E"),
                ("E", "T"),
                ("A", "C"),
                ("C", "F"),
                ("F", "T"),
            ],
            [("A", "T", 12)],
        )
        result = route_traffic(topology)
        self.assertEqual(
            self.loads(result),
            {
                "A-B": 8,
                "B-D": 4,
                "D-T": 4,
                "B-E": 4,
                "E-T": 4,
                "A-C": 4,
                "C-F": 4,
                "F-T": 4,
            },
        )
        self.assertEqual(sum(item.load for item in result.links), 12 * 3)
        self.assertEqual(self.loads(result)["A-B"] + self.loads(result)["A-C"], 12)
        fractional = Topology(
            topology.nodes, topology.links, (Demand("fractional", "A", "T", 10),)
        )
        fractional_result = route_traffic(fractional)
        self.assertAlmostEqual(self.loads(fractional_result)["A-B"], 20 / 3)
        self.assertAlmostEqual(self.loads(fractional_result)["A-C"], 10 / 3)
        self.assertAlmostEqual(sum(item.load for item in fractional_result.links), 30)

    def test_endpoint_nodes_cannot_transit_but_can_send_and_receive(self):
        for kind in ("operations-site", "data-center"):
            with self.subTest(kind=kind):
                topology = self.network(
                    [("A", "X"), ("X", "T"), ("A", "B"), ("B", "C"), ("C", "T")],
                    [("A", "T", 10), ("X", "A", 3), ("T", "X", 2)],
                    kinds={"X": kind},
                )
                self.assertEqual(
                    self.loads(route_traffic(topology)),
                    {"A-X": 3, "X-T": 2, "A-B": 10, "B-C": 10, "C-T": 10},
                )

    def test_aggregation_hub_can_transit(self):
        topology = self.network(
            [("A", "H"), ("H", "B")],
            [("A", "B", 10)],
            kinds={"H": "aggregation-hub"},
        )
        self.assertEqual(self.loads(route_traffic(topology)), {"A-H": 10, "H-B": 10})

    def test_unreachable_and_prohibited_transit_are_reported(self):
        topology = self.network(
            [("A", "X"), ("X", "T")],
            [("A", "T", 10), ("A", "Z", 5)],
            kinds={"X": "operations-site"},
            isolated=("Z",),
        )
        result = route_traffic(topology)
        self.assertEqual(result.undeliverable, topology.demands)
        self.assertTrue(all(item.load == 0 for item in result.links))

    def test_ranking_uses_utilization_with_id_tie_break_and_limit(self):
        topology = self.network(
            [("A", name) for name in "BCDEFG"],
            [("A", "B", 20), ("A", "C", 10), ("A", "D", 10)],
            capacities={"A-B": 100, "A-C": 20, "A-D": 20},
        )
        result = route_traffic(topology)
        self.assertEqual(
            [item.link.id for item in result.top_five],
            ["A-C", "A-D", "A-B", "A-E", "A-F"],
        )
        self.assertEqual(route_traffic(Topology((), (), ())).top_five, ())

    def test_real_baseline_is_reproducible_without_mutating_topology(self):
        topology = load_topology()
        result = route_traffic(topology)
        self.assertEqual(len(result.links), 55)
        self.assertEqual(result.undeliverable, ())
        self.assertEqual(len(result.top_five), 5)
        # Reproduced using simple-path enumeration bounded by the BFS hop count.
        expected = [
            ("L12", 390.546867, 71.008521),
            ("L3", 376.225021, 68.404549),
            ("L26", 341.693484, 62.126088),
            ("L30", 323.482456, 58.814992),
            ("L13", 278.462531, 50.629551),
        ]
        self.assertEqual(
            [item.link.id for item in result.top_five],
            [identity for identity, _, _ in expected],
        )
        for item, (_, load, utilization) in zip(result.top_five, expected, strict=True):
            self.assertAlmostEqual(item.load, load, delta=0.000001)
            self.assertAlmostEqual(
                item.utilization_percent, utilization, delta=0.000001
            )
        self.assertEqual(self.loads(result)["access:OPS-WEST:Dublin"], 20)
        self.assertAlmostEqual(
            sum(
                item.load
                for item in result.links
                if "DC-NORTH" in (item.link.source, item.link.target)
            ),
            110,
        )
        self.assertEqual(result, route_traffic(topology))
        reordered = Topology(
            tuple(reversed(topology.nodes)),
            tuple(reversed(topology.links)),
            tuple(reversed(topology.demands)),
        )
        self.assertEqual(result, route_traffic(reordered))
        self.assertEqual(topology, load_topology())
