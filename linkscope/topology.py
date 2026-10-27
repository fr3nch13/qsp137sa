"""Load validated local SNDlib and site inputs into one undirected topology."""

import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path

import networkx as nx
from topohub.providers.sndlib import SNDlibGenerator

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class InputError(ValueError):
    """Identify invalid local input by file and physical row."""

    def __init__(self, path: Path, row: int, message: str):
        super().__init__(f"{path}: row {row}: {message}")


@dataclass(frozen=True)
class Node:
    id: str
    kind: str
    longitude: float
    latitude: float

    @property
    def transit(self) -> bool:
        return self.kind in ("backbone", "aggregation-hub")


@dataclass(frozen=True)
class Link:
    id: str
    source: str
    target: str
    capacity: float


@dataclass(frozen=True)
class Demand:
    id: str
    source: str
    target: str
    units: float


@dataclass(frozen=True)
class Topology:
    nodes: tuple[Node, ...]
    links: tuple[Link, ...]
    demands: tuple[Demand, ...]


class LocalSNDlibGenerator(SNDlibGenerator):
    """Feed validated local native text to the pinned TopoHub parser."""

    @classmethod
    def download_topo(cls, name: str) -> bytes:
        return Path(name).read_bytes()


def _number(value: str, path: Path, row: int, *, positive: bool = True) -> float:
    try:
        number = float(value)
    except ValueError as error:
        raise InputError(path, row, f"invalid number {value!r}") from error
    if not math.isfinite(number) or (positive and number <= 0):
        raise InputError(path, row, f"invalid numeric value {value!r}")
    return number


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise InputError(path, 1, str(error)) from error


def _backbone(path: Path) -> Topology:
    text = _text(path)
    records: dict[str, list[tuple[int, str]]] = {
        "NODES": [],
        "LINKS": [],
        "DEMANDS": [],
    }
    section = None
    seen = set()
    for row, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(("#", "?")):
            continue
        if line.endswith(" (") and line.split()[0] in (*records, "ADMISSIBLE_PATHS"):
            name = line.split()[0]
            if section is not None or name in seen:
                raise InputError(path, row, "nested or duplicate section")
            seen.add(name)
            section = name
        elif line == ")":
            if section is None:
                raise InputError(path, row, "unexpected section terminator")
            section = None
        elif section in records:
            records[section].append((row, line))
        else:
            raise InputError(path, row, "unsupported native-format record")
    if section is not None or any(not records[name] for name in records):
        raise InputError(
            path, len(text.splitlines()) or 1, "missing or unclosed section"
        )

    nodes = []
    node_ids = set()
    for row, line in records["NODES"]:
        match = re.fullmatch(r"(\S+) \( (\S+) (\S+) \)", line)
        if not match:
            raise InputError(path, row, "expected node ID and coordinates")
        name, lon, lat = match.groups()
        if name in node_ids:
            raise InputError(path, row, f"duplicate node ID {name}")
        longitude = _number(lon, path, row, positive=False)
        latitude = _number(lat, path, row, positive=False)
        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            raise InputError(path, row, "coordinates out of range")
        nodes.append(Node(name, "backbone", longitude, latitude))
        node_ids.add(name)

    links = []
    demands = []
    for section in ("LINKS", "DEMANDS"):
        identities = set()
        pairs = set()
        for row, line in records[section]:
            match = re.fullmatch(r"(\S+) \( (\S+) (\S+) \) (.+)", line)
            if not match:
                raise InputError(path, row, f"malformed {section.lower()} record")
            identity, source, target, rest = match.groups()
            pair = frozenset((source, target))
            if source not in node_ids or target not in node_ids or source == target:
                raise InputError(path, row, "unknown endpoint or self-reference")
            if identity in identities or pair in pairs:
                raise InputError(path, row, "duplicate ID or undirected endpoint pair")
            identities.add(identity)
            pairs.add(pair)
            fields = rest.split()
            if section == "LINKS":
                if (
                    len(fields) < 8
                    or fields[4] != "("
                    or fields[-1] != ")"
                    or len(fields[5:-1]) % 2
                ):
                    raise InputError(path, row, "malformed link capacity modules")
                for value in fields[:4] + fields[5:-1]:
                    number = _number(value, path, row, positive=False)
                    if number < 0:
                        raise InputError(path, row, "negative link module value")
                links.append(Link(identity, source, target, 550))
            else:
                if len(fields) != 3 or fields[2] != "UNLIMITED":
                    raise InputError(path, row, "unsupported demand record")
                _number(fields[0], path, row)
                demands.append(
                    Demand(identity, source, target, _number(fields[1], path, row))
                )

    # TopoHub requires section markers at column zero and no blank records.
    canonical = "\n".join(
        f"{name} (\n" + "\n".join(line for _, line in rows) + "\n)"
        for name, rows in records.items()
    )

    class ValidatedGenerator(LocalSNDlibGenerator):
        @classmethod
        def download_topo(cls, name: str) -> bytes:
            return canonical.encode()

    parsed = ValidatedGenerator.generate_topo(str(path))
    parsed_positions = {node["name"]: node["pos"] for node in parsed["nodes"]}
    nodes = [Node(node.id, node.kind, *parsed_positions[node.id]) for node in nodes]
    return Topology(tuple(nodes), tuple(links), tuple(demands))


def load_topology(
    backbone: Path = DATA_DIR / "nobel-eu.txt",
    sites: Path = DATA_DIR / "sites.csv",
) -> Topology:
    """Merge local inputs; raise InputError rather than return partial data."""
    topology = _backbone(backbone)
    nodes = {node.id: node for node in topology.nodes}
    links = list(topology.links)
    demands = list(topology.demands)
    rows = {}
    reader = csv.reader(_text(sites).splitlines(), strict=True)
    try:
        header = next(reader, None)
        if header != ["site_id", "site_type", "attaches_to", "access_capacity"]:
            raise InputError(
                sites, 1, "expected site_id,site_type,attaches_to,access_capacity"
            )
        for values in reader:
            row = reader.line_num
            if len(values) != 4 or any(not value.strip() for value in values):
                raise InputError(sites, row, "expected four nonempty fields")
            identity, kind, attachments, capacity = (value.strip() for value in values)
            if identity in nodes or identity in rows:
                raise InputError(sites, row, f"duplicate node ID {identity}")
            if kind not in ("data-center", "operations-site", "aggregation-hub"):
                raise InputError(sites, row, f"unsupported site type {kind}")
            rows[identity] = (
                row,
                kind,
                attachments.split(";"),
                _number(capacity, sites, row),
            )
    except csv.Error as error:
        raise InputError(sites, reader.line_num, str(error)) from error

    graph = nx.Graph()
    graph.add_nodes_from(nodes)
    graph.add_edges_from((link.source, link.target) for link in links)
    link_ids = {link.id for link in links}
    for identity, (row, _, attachments, capacity) in rows.items():
        for attachment in attachments:
            if attachment not in nodes and attachment not in rows:
                raise InputError(sites, row, f"unknown attachment {attachment!r}")
            if attachment == identity or graph.has_edge(identity, attachment):
                raise InputError(sites, row, "self-link or duplicate attachment")
            link_id = f"access:{identity}:{attachment}"
            if link_id in link_ids:
                raise InputError(sites, row, f"duplicate link ID {link_id}")
            link_ids.add(link_id)
            graph.add_edge(identity, attachment)
            links.append(Link(link_id, identity, attachment, capacity))
    backbone_nodes = dict(nodes)
    for offset, (identity, (row, kind, _, _)) in enumerate(sorted(rows.items()), 1):
        distances = nx.single_source_shortest_path_length(graph, identity)
        anchors = [name for name in backbone_nodes if name in distances]
        if not anchors:
            raise InputError(sites, row, "site component has no backbone attachment")
        nearest = min(distances[name] for name in anchors)
        anchors = [name for name in anchors if distances[name] == nearest]
        lon = sum(backbone_nodes[name].longitude for name in anchors) / len(anchors)
        lat = sum(backbone_nodes[name].latitude for name in anchors) / len(anchors)
        nodes[identity] = Node(
            identity, kind, lon + offset * 0.03, lat - nearest * 0.15
        )
    centers = [node.id for node in nodes.values() if node.kind == "data-center"]
    operations = [node.id for node in nodes.values() if node.kind == "operations-site"]
    if len(centers) != 2:
        raise InputError(sites, 1, "expected exactly two data centers")
    extra = [
        Demand(f"site:{site}:{center}", site, center, 10)
        for site in operations
        for center in centers
    ]
    extra.append(Demand("site:data-centers", centers[0], centers[1], 50))
    if {demand.id for demand in demands} & {demand.id for demand in extra}:
        raise InputError(sites, 1, "generated demand ID conflicts with backbone")
    demands.extend(extra)
    return Topology(tuple(nodes.values()), tuple(links), tuple(demands))
