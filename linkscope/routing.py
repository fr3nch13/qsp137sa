"""Route undirected demands over equal-share minimum-hop paths."""

import math
from dataclasses import dataclass
from itertools import pairwise

import networkx as nx

from linkscope.topology import Demand, Link, Topology


@dataclass(frozen=True)
class LinkLoad:
    link: Link
    load: float

    @property
    def utilization_percent(self) -> float:
        return self.load / self.link.capacity * 100


@dataclass(frozen=True)
class RoutingResult:
    links: tuple[LinkLoad, ...]
    undeliverable: tuple[Demand, ...]

    @property
    def top_five(self) -> tuple[LinkLoad, ...]:
        return tuple(
            sorted(
                self.links,
                key=lambda item: (-item.utilization_percent, item.link.id),
            )[:5]
        )


def route_traffic(topology: Topology) -> RoutingResult:
    """Calculate link loads and explicitly retain demands with no legal path."""
    graph = nx.Graph()
    graph.add_nodes_from(node.id for node in topology.nodes)
    graph.add_edges_from(
        (link.source, link.target, {"id": link.id}) for link in topology.links
    )
    transit = {node.id for node in topology.nodes if node.transit}
    contributions: dict[str, list[float]] = {link.id: [] for link in topology.links}
    undeliverable = []
    for demand in sorted(topology.demands, key=lambda item: item.id):
        allowed = graph.subgraph(transit | {demand.source, demand.target})
        try:
            paths = sorted(nx.all_shortest_paths(allowed, demand.source, demand.target))
        except nx.NetworkXNoPath:
            undeliverable.append(demand)
            continue
        # Split across complete paths, not next hops with unequal path counts.
        share = demand.units / len(paths)
        for path in paths:
            for source, target in pairwise(path):
                contributions[graph[source][target]["id"]].append(share)
    return RoutingResult(
        links=tuple(
            LinkLoad(link, math.fsum(contributions[link.id]))
            for link in sorted(topology.links, key=lambda item: item.id)
        ),
        undeliverable=tuple(undeliverable),
    )
