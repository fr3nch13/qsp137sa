// Fetch the baseline network and validate the frontend's complete API contract.
export type NodeKind =
  | "backbone"
  | "operations-site"
  | "data-center"
  | "aggregation-hub";
export type Reason = "disconnected" | "undeliverable" | "overloaded";
export type NetworkNode = {
  id: string;
  kind: NodeKind;
  longitude: number;
  latitude: number;
  transit: boolean;
};
export type NetworkLink = {
  id: string;
  source: string;
  target: string;
  capacity: number;
};
export type LinkLoad = NetworkLink & {
  load: number;
  utilization_percent: number;
};
export type Demand = {
  id: string;
  source: string;
  target: string;
  units: number;
};
export type Criticality = {
  kind: "node" | "link";
  id: string;
  critical: boolean;
  reasons: Reason[];
};
export type Network = {
  nodes: NetworkNode[];
  links: NetworkLink[];
  demands: Demand[];
  baseline: {
    failure: null;
    links: LinkLoad[];
    top_five: LinkLoad[];
    undeliverable: Demand[];
    failed_endpoint_demands: Demand[];
    overloaded: LinkLoad[];
    disconnected: boolean;
  };
  criticality: Criticality[];
};

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
function text(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}
function numeric(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}
function link(value: unknown): value is NetworkLink {
  return (
    record(value) &&
    text(value.id) &&
    text(value.source) &&
    text(value.target) &&
    numeric(value.capacity) &&
    value.capacity > 0
  );
}
function load(value: unknown): value is LinkLoad {
  return (
    link(value) &&
    "load" in value &&
    numeric(value.load) &&
    value.load >= 0 &&
    "utilization_percent" in value &&
    numeric(value.utilization_percent) &&
    value.utilization_percent >= 0
  );
}
function demand(value: unknown): value is Demand {
  return (
    record(value) &&
    text(value.id) &&
    text(value.source) &&
    text(value.target) &&
    numeric(value.units) &&
    value.units > 0
  );
}
function node(value: unknown): value is NetworkNode {
  return (
    record(value) &&
    text(value.id) &&
    ["backbone", "operations-site", "data-center", "aggregation-hub"].includes(
      String(value.kind),
    ) &&
    numeric(value.longitude) &&
    Math.abs(value.longitude) <= 180 &&
    numeric(value.latitude) &&
    Math.abs(value.latitude) <= 90 &&
    typeof value.transit === "boolean"
  );
}
function criticality(value: unknown): value is Criticality {
  return (
    record(value) &&
    (value.kind === "node" || value.kind === "link") &&
    text(value.id) &&
    typeof value.critical === "boolean" &&
    Array.isArray(value.reasons) &&
    value.reasons.every(
      (reason: unknown) =>
        reason === "disconnected" ||
        reason === "undeliverable" ||
        reason === "overloaded",
    ) &&
    value.critical === value.reasons.length > 0
  );
}
function array<T>(
  value: unknown,
  guard: (item: unknown) => item is T,
): value is T[] {
  return Array.isArray(value) && value.every(guard);
}
function network(value: unknown): value is Network {
  if (
    !record(value) ||
    !array(value.nodes, node) ||
    !array(value.links, link) ||
    !array(value.demands, demand) ||
    !array(value.criticality, criticality) ||
    !record(value.baseline)
  )
    return false;
  const baseline = value.baseline;
  if (
    baseline.failure !== null ||
    !array(baseline.links, load) ||
    !array(baseline.top_five, load) ||
    baseline.top_five.length > 5 ||
    !array(baseline.undeliverable, demand) ||
    !array(baseline.failed_endpoint_demands, demand) ||
    !array(baseline.overloaded, load) ||
    typeof baseline.disconnected !== "boolean"
  )
    return false;
  const nodes = new Set(value.nodes.map((item) => item.id));
  const links = new Set(value.links.map((item) => item.id));
  return (
    nodes.size === value.nodes.length &&
    links.size === value.links.length &&
    [...value.links, ...value.demands].every(
      (item) => nodes.has(item.source) && nodes.has(item.target),
    ) &&
    baseline.links.length === links.size &&
    new Set(baseline.links.map((item) => item.id)).size === links.size &&
    [...baseline.links, ...baseline.top_five, ...baseline.overloaded].every(
      (item) =>
        links.has(item.id) && nodes.has(item.source) && nodes.has(item.target),
    ) &&
    value.criticality.every((item) =>
      (item.kind === "node" ? nodes : links).has(item.id),
    ) &&
    value.criticality.length === nodes.size + links.size &&
    new Set(value.criticality.map((item) => `${item.kind}:${item.id}`)).size ===
      nodes.size + links.size
  );
}

export async function fetchNetwork(signal: AbortSignal): Promise<Network> {
  const response = await fetch("/api/network", { signal });
  if (!response.ok)
    throw new Error(`API request failed (HTTP ${response.status}).`);
  if (!response.headers.get("content-type")?.includes("application/json")) {
    throw new Error("API returned a non-JSON response.");
  }
  const data: unknown = await response.json();
  if (!network(data)) throw new Error("API returned an invalid network.");
  return data;
}
