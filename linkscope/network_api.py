"""Read-only JSON endpoints for local network data and request-local simulations."""

import logging
from typing import Literal, TypedDict

import networkx as nx
from django.http import HttpRequest, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from linkscope.failures import Failure, analyze_all_failures, analyze_failure
from linkscope.routing import LinkLoad, RoutingResult, route_traffic
from linkscope.topology import Demand, InputError, load_topology

logger = logging.getLogger(__name__)


class DemandJSON(TypedDict):
    id: str
    source: str
    target: str
    units: float


class NodeJSON(TypedDict):
    id: str
    kind: str
    longitude: float
    latitude: float
    transit: bool


class LinkJSON(TypedDict):
    id: str
    source: str
    target: str
    capacity: float


class LoadJSON(LinkJSON):
    load: float
    utilization_percent: float


class FailureJSON(TypedDict):
    kind: Literal["node", "link"]
    id: str


class CriticalityJSON(FailureJSON):
    critical: bool
    reasons: list[str]


class AnalysisJSON(TypedDict):
    failure: FailureJSON | None
    links: list[LoadJSON]
    top_five: list[LoadJSON]
    undeliverable: list[DemandJSON]
    failed_endpoint_demands: list[DemandJSON]
    overloaded: list[LoadJSON]
    disconnected: bool


class NetworkJSON(TypedDict):
    nodes: list[NodeJSON]
    links: list[LinkJSON]
    demands: list[DemandJSON]
    baseline: AnalysisJSON
    criticality: list[CriticalityJSON]


def _demand(demand: Demand) -> DemandJSON:
    return {
        "id": demand.id,
        "source": demand.source,
        "target": demand.target,
        "units": demand.units,
    }


def _load(item: LinkLoad) -> LoadJSON:
    return {
        "id": item.link.id,
        "source": item.link.source,
        "target": item.link.target,
        "capacity": item.link.capacity,
        "load": item.load,
        "utilization_percent": item.utilization_percent,
    }


def _analysis(
    routing: RoutingResult,
    failure: Failure | None = None,
    endpoints: tuple[Demand, ...] = (),
    disconnected: bool = False,
) -> AnalysisJSON:
    return {
        "failure": {"kind": failure.kind, "id": failure.id} if failure else None,
        "links": [_load(item) for item in routing.links],
        "top_five": [_load(item) for item in routing.top_five],
        "undeliverable": [_demand(demand) for demand in routing.undeliverable],
        "failed_endpoint_demands": [_demand(demand) for demand in endpoints],
        "overloaded": [
            _load(item) for item in routing.links if item.load > item.link.capacity
        ],
        "disconnected": disconnected,
    }


# Strictly read-only: reject all unsafe methods before loading or analyzing data.
@csrf_exempt
@never_cache
def network_api(request: HttpRequest, resource: str) -> JsonResponse:
    """Return topology/baseline or one simulation without storing user state."""
    if request.method not in {"GET", "HEAD"}:
        response = JsonResponse({"error": "Method not allowed."}, status=405)
        response["Allow"] = "GET, HEAD"
        return response
    allowed = {"kind", "id"} if resource == "analysis" else set()
    if any(
        key not in allowed or len(request.GET.getlist(key)) != 1 for key in request.GET
    ):
        return JsonResponse(
            {"error": "Unknown or repeated query parameter."}, status=400
        )
    kind, identity = request.GET.get("kind"), request.GET.get("id")
    if (kind is not None or identity is not None) and (
        kind not in {"node", "link"} or not identity
    ):
        return JsonResponse(
            {"error": "Provide kind=node|link and a nonempty id together."}, status=400
        )
    try:
        topology = load_topology()
        if kind is not None and identity is not None:
            elements = topology.nodes if kind == "node" else topology.links
            if not any(element.id == identity for element in elements):
                return JsonResponse(
                    {"error": f"Unknown {kind}: {identity}"}, status=404
                )
            failure = Failure("node" if kind == "node" else "link", identity)
            result = analyze_failure(topology, failure)
            return JsonResponse(
                _analysis(
                    result.routing,
                    failure,
                    result.failed_endpoint_demands,
                    result.disconnected,
                )
            )
        graph = nx.Graph()
        graph.add_nodes_from(node.id for node in topology.nodes)
        graph.add_edges_from((link.source, link.target) for link in topology.links)
        baseline = _analysis(
            route_traffic(topology),
            disconnected=nx.number_connected_components(graph) > 1,
        )
        if resource == "analysis":
            return JsonResponse(baseline)
        criticality: list[CriticalityJSON] = [
            {
                "kind": result.failure.kind,
                "id": result.failure.id,
                "critical": result.critical,
                "reasons": list(result.reasons),
            }
            for result in analyze_all_failures(topology)
        ]
        payload: NetworkJSON = {
            "nodes": [
                {
                    "id": node.id,
                    "kind": node.kind,
                    "longitude": node.longitude,
                    "latitude": node.latitude,
                    "transit": node.transit,
                }
                for node in topology.nodes
            ],
            "links": [
                {
                    "id": link.id,
                    "source": link.source,
                    "target": link.target,
                    "capacity": link.capacity,
                }
                for link in topology.links
            ],
            "demands": [_demand(demand) for demand in topology.demands],
            "baseline": baseline,
            "criticality": criticality,
        }
        return JsonResponse(payload)
    except InputError:
        # File/row diagnostics are logged only; never expose them to clients.
        logger.exception("Network input could not be loaded.")
        return JsonResponse({"error": "Network data could not be loaded."}, status=503)
    except nx.NetworkXException:
        logger.exception("Network analysis failed.")
        return JsonResponse({"error": "Network analysis failed."}, status=500)
