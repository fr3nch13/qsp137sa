"""Analyze single failures without changing the original network."""

from dataclasses import dataclass
from typing import Literal

import networkx as nx

from linkscope.routing import LinkLoad, RoutingResult, route_traffic
from linkscope.topology import Demand, Topology


@dataclass(frozen=True)
class Failure:
    kind: Literal["node", "link"]
    id: str


@dataclass(frozen=True)
class FailureResult:
    failure: Failure
    routing: RoutingResult
    failed_endpoint_demands: tuple[Demand, ...]
    disconnected: bool

    @property
    def overloaded(self) -> tuple[LinkLoad, ...]:
        return tuple(
            item for item in self.routing.links if item.load > item.link.capacity
        )

    @property
    def reasons(self) -> tuple[str, ...]:
        reasons = []
        if self.disconnected:
            reasons.append("disconnected")
        if self.failed_endpoint_demands or self.routing.undeliverable:
            reasons.append("undeliverable")
        if self.overloaded:
            reasons.append("overloaded")
        return tuple(reasons)

    @property
    def critical(self) -> bool:
        return bool(self.reasons)


def analyze_failure(topology: Topology, failure: Failure) -> FailureResult:
    """Return rerouted traffic, separate failed endpoints, and criticality reasons."""
    if failure.kind not in ("node", "link"):
        raise ValueError(f"Unknown failure kind: {failure.kind}")
    elements = topology.nodes if failure.kind == "node" else topology.links
    if not any(element.id == failure.id for element in elements):
        raise ValueError(f"Unknown {failure.kind}: {failure.id}")

    failed_node = failure.id if failure.kind == "node" else None
    endpoints = tuple(
        sorted(
            (
                demand
                for demand in topology.demands
                if failed_node in (demand.source, demand.target)
            ),
            key=lambda demand: demand.id,
        )
    )
    remaining = Topology(
        nodes=tuple(node for node in topology.nodes if node.id != failed_node),
        links=tuple(
            link
            for link in topology.links
            if failed_node not in (link.source, link.target)
            and not (failure.kind == "link" and link.id == failure.id)
        ),
        demands=tuple(
            demand
            for demand in topology.demands
            if failed_node not in (demand.source, demand.target)
        ),
    )
    graph = nx.Graph()
    graph.add_nodes_from(node.id for node in remaining.nodes)
    graph.add_edges_from((link.source, link.target) for link in remaining.links)
    return FailureResult(
        failure=failure,
        routing=route_traffic(remaining),
        failed_endpoint_demands=endpoints,
        disconnected=nx.number_connected_components(graph) > 1,
    )


def analyze_all_failures(topology: Topology) -> tuple[FailureResult, ...]:
    """Evaluate every node and link once, in deterministic order."""
    return tuple(
        analyze_failure(topology, Failure(kind, element.id))
        for kind, elements in (("node", topology.nodes), ("link", topology.links))
        for element in sorted(elements, key=lambda element: element.id)
    )
