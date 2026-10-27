"""Independently calculated failure cases and real-network acceptance checks."""

from unittest import TestCase

from linkscope.failures import Failure, analyze_all_failures, analyze_failure
from linkscope.routing import route_traffic
from linkscope.topology import Demand, Link, Node, Topology, load_topology


class FailureTests(TestCase):
    def chain(self):
        return Topology(
            tuple(Node(name, "backbone", 0, 0) for name in "ABCD"),
            (
                Link("AB", "A", "B", 10),
                Link("BC", "B", "C", 10),
                Link("CD", "C", "D", 10),
            ),
            (Demand("AC", "A", "C", 7), Demand("BD", "B", "D", 3)),
        )

    def diamond(self, units=12):
        return Topology(
            tuple(Node(name, "backbone", 0, 0) for name in "ABCT"),
            (
                Link("AB", "A", "B", 10),
                Link("BT", "B", "T", 10),
                Link("AC", "A", "C", 10),
                Link("CT", "C", "T", 10),
            ),
            (Demand("AT", "A", "T", units),),
        )

    def test_node_failure_separates_endpoints_from_other_unreachable_demands(self):
        topology = self.chain()
        result = analyze_failure(topology, Failure("node", "B"))
        self.assertEqual(result.failed_endpoint_demands, (topology.demands[1],))
        self.assertEqual(result.routing.undeliverable, (topology.demands[0],))
        self.assertEqual([item.link.id for item in result.routing.links], ["CD"])
        self.assertTrue(result.disconnected)
        self.assertEqual(result.reasons, ("disconnected", "undeliverable"))
        self.assertTrue(result.critical)
        self.assertEqual(result.overloaded, ())

    def test_link_failure_reports_unreachable_without_failed_endpoint_demands(self):
        topology = self.chain()
        result = analyze_failure(topology, Failure("link", "BC"))
        self.assertEqual(result.failed_endpoint_demands, ())
        self.assertEqual(result.routing.undeliverable, topology.demands)
        self.assertTrue(result.disconnected)
        self.assertEqual(result.reasons, ("disconnected", "undeliverable"))

    def test_rerouting_reports_every_overloaded_remaining_link(self):
        topology = self.diamond()
        self.assertTrue(all(item.load == 6 for item in route_traffic(topology).links))
        for failure in (Failure("link", "AB"), Failure("node", "B")):
            with self.subTest(failure=failure):
                result = analyze_failure(topology, failure)
                self.assertEqual(
                    [item.link.id for item in result.overloaded], ["AC", "CT"]
                )
                self.assertTrue(all(item.load == 12 for item in result.overloaded))
                self.assertFalse(result.disconnected)
                self.assertEqual(result.routing.undeliverable, ())
                self.assertEqual(result.reasons, ("overloaded",))

    def test_exact_capacity_is_not_overload_but_any_excess_is(self):
        for units, critical in ((10, False), (10.000001, True)):
            with self.subTest(units=units):
                result = analyze_failure(self.diamond(units), Failure("link", "AB"))
                self.assertEqual(result.critical, critical)
                self.assertEqual(len(result.overloaded), 2 if critical else 0)

    def test_endpoint_loss_is_critical_even_when_remaining_network_is_connected(self):
        topology = self.chain()
        result = analyze_failure(topology, Failure("node", "A"))
        self.assertFalse(result.disconnected)
        self.assertEqual(result.failed_endpoint_demands, (topology.demands[0],))
        self.assertEqual(result.routing.undeliverable, ())
        self.assertEqual(result.reasons, ("undeliverable",))

    def test_disconnection_alone_is_critical_without_demands(self):
        topology = self.chain()
        topology = Topology(topology.nodes, topology.links, ())
        result = analyze_failure(topology, Failure("link", "BC"))
        self.assertEqual(result.reasons, ("disconnected",))

    def test_connected_network_can_lose_legal_routes_due_to_endpoint_transit_rule(self):
        topology = Topology(
            (
                Node("A", "backbone", 0, 0),
                Node("H", "aggregation-hub", 0, 0),
                Node("X", "operations-site", 0, 0),
                Node("T", "backbone", 0, 0),
            ),
            (
                Link("AH", "A", "H", 100),
                Link("HT", "H", "T", 100),
                Link("AX", "A", "X", 100),
                Link("XT", "X", "T", 100),
            ),
            (Demand("AT", "A", "T", 20),),
        )
        result = analyze_failure(topology, Failure("node", "H"))
        self.assertFalse(result.disconnected)
        self.assertEqual(result.failed_endpoint_demands, ())
        self.assertEqual(result.routing.undeliverable, topology.demands)
        self.assertEqual(result.reasons, ("undeliverable",))

    def test_single_remaining_node_and_empty_network_are_not_disconnected(self):
        topology = Topology(
            (Node("A", "backbone", 0, 0), Node("B", "backbone", 0, 0)),
            (Link("AB", "A", "B", 10),),
            (),
        )
        self.assertFalse(analyze_failure(topology, Failure("node", "A")).critical)
        single = Topology((topology.nodes[0],), (), ())
        self.assertFalse(analyze_failure(single, Failure("node", "A")).critical)
        self.assertEqual(analyze_all_failures(Topology((), (), ())), ())

    def test_invalid_failure_is_explicit(self):
        for failure in (Failure("node", "missing"), Failure("link", "missing")):
            with (
                self.subTest(failure=failure),
                self.assertRaisesRegex(ValueError, "Unknown"),
            ):
                analyze_failure(self.chain(), failure)

    def test_all_criticality_reasons_can_apply_together(self):
        chain = self.chain()
        topology = Topology(
            chain.nodes, chain.links, (*chain.demands, Demand("CD", "C", "D", 20))
        )
        result = analyze_failure(topology, Failure("node", "B"))
        self.assertEqual(
            result.reasons, ("disconnected", "undeliverable", "overloaded")
        )
        self.assertEqual([item.link.id for item in result.overloaded], ["CD"])

    def test_restoration_is_baseline_without_mutation_or_cross_request_state(self):
        topology = self.diamond()
        baseline = route_traffic(topology)
        first = analyze_failure(topology, Failure("link", "AB"))
        analyze_failure(topology, Failure("node", "C"))
        self.assertEqual(route_traffic(topology), baseline)
        self.assertEqual(analyze_failure(topology, Failure("link", "AB")), first)
        self.assertEqual(topology, self.diamond())

    def test_all_real_failures_are_complete_reproducible_and_partition_demands(self):
        topology = load_topology()
        baseline = route_traffic(topology)
        results = analyze_all_failures(topology)
        self.assertEqual(len(results), 92)
        self.assertEqual(len({result.failure for result in results}), 92)
        self.assertEqual(sum(r.failure.kind == "node" for r in results), 37)
        self.assertEqual(sum(r.failure.kind == "link" for r in results), 55)
        self.assertEqual(
            {r.failure.id for r in results if r.critical and r.failure.kind == "node"},
            {node.id for node in topology.nodes},
        )
        self.assertEqual(
            {r.failure.id for r in results if r.critical and r.failure.kind == "link"},
            {
                "L12",
                "L26",
                "access:HUB-EAST:Warsaw",
                "access:OPS-EAST-1:HUB-EAST",
                "access:OPS-SOUTHEAST:Athens",
                "access:OPS-WEST:Dublin",
            },
        )
        for result in results:
            endpoints = {d.id for d in result.failed_endpoint_demands}
            unreachable = {d.id for d in result.routing.undeliverable}
            self.assertFalse(endpoints & unreachable)
            self.assertTrue(
                all(item.load > item.link.capacity for item in result.overloaded)
            )
            self.assertEqual(result.critical, bool(result.reasons))
            if result.failure.kind == "node":
                self.assertTrue(
                    all(
                        result.failure.id in (d.source, d.target)
                        for d in result.failed_endpoint_demands
                    )
                )
            else:
                self.assertEqual(endpoints, set())
        self.assertEqual(analyze_all_failures(topology), results)
        self.assertEqual(route_traffic(topology), baseline)
        self.assertEqual(topology, load_topology())
