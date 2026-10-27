// Fetch network and single-failure results with runtime API contract validation.
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
export type Failure = { kind: "node" | "link"; id: string };
export type Analysis = {
  failure: Failure | null;
  links: LinkLoad[];
  top_five: LinkLoad[];
  undeliverable: Demand[];
  failed_endpoint_demands: Demand[];
  overloaded: LinkLoad[];
  disconnected: boolean;
};
export type Network = {
  nodes: NetworkNode[];
  links: NetworkLink[];
  demands: Demand[];
  baseline: Analysis & { failure: null };
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
function analysis(value: unknown): value is Analysis {
  return (
    record(value) &&
    (value.failure === null ||
      (record(value.failure) &&
        (value.failure.kind === "node" || value.failure.kind === "link") &&
        text(value.failure.id))) &&
    array(value.links, load) &&
    array(value.top_five, load) &&
    value.top_five.length <= 5 &&
    array(value.undeliverable, demand) &&
    array(value.failed_endpoint_demands, demand) &&
    array(value.overloaded, load) &&
    typeof value.disconnected === "boolean"
  );
}
function network(value: unknown): value is Network {
  if (
    !record(value) ||
    !array(value.nodes, node) ||
    !array(value.links, link) ||
    !array(value.demands, demand) ||
    !array(value.criticality, criticality) ||
    !analysis(value.baseline)
  )
    return false;
  const baseline = value.baseline;
  if (baseline.failure !== null) return false;
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

// Server details (such as input file/row diagnostics) stay in the server logs.
function httpErrorMessage(status: number): string {
  if (status === 503)
    return "The server could not read its network data files. Check the server logs for details.";
  if (status >= 500) return "The server ran into a problem.";
  return "The server could not handle this request.";
}

async function fetchJSON(url: string, signal: AbortSignal): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(url, { signal });
  } catch (error) {
    if (signal.aborted) throw error;
    throw new Error("Could not reach the LinkScope server.");
  }
  if (!response.ok) throw new Error(httpErrorMessage(response.status));
  if (!response.headers.get("content-type")?.includes("application/json")) {
    throw new Error("API returned a non-JSON response.");
  }
  return response.json();
}

export async function fetchNetwork(signal: AbortSignal): Promise<Network> {
  const data = await fetchJSON("/api/network", signal);
  if (!network(data)) throw new Error("API returned an invalid network.");
  return data;
}

export async function fetchAnalysis(
  network: Network,
  failure: Failure,
  signal: AbortSignal,
): Promise<Analysis> {
  const query = new URLSearchParams(failure);
  const data = await fetchJSON(`/api/analysis?${query}`, signal);
  if (
    !analysis(data) ||
    data.failure?.kind !== failure.kind ||
    data.failure.id !== failure.id
  )
    throw new Error("API returned an invalid analysis.");
  const surviving = network.links.filter((item) =>
    failure.kind === "link"
      ? item.id !== failure.id
      : item.source !== failure.id && item.target !== failure.id,
  );
  const loads = new Map(data.links.map((item) => [item.id, item]));
  const demands = new Map(network.demands.map((item) => [item.id, item]));
  const sameLoad = (item: LinkLoad) => {
    const expected = loads.get(item.id);
    return (
      expected !== undefined &&
      expected.source === item.source &&
      expected.target === item.target &&
      expected.capacity === item.capacity &&
      expected.load === item.load &&
      expected.utilization_percent === item.utilization_percent
    );
  };
  const reported = [...data.failed_endpoint_demands, ...data.undeliverable];
  if (
    data.links.length !== surviving.length ||
    loads.size !== surviving.length ||
    !surviving.every((item) => {
      const result = loads.get(item.id);
      return (
        result?.source === item.source &&
        result.target === item.target &&
        result.capacity === item.capacity
      );
    }) ||
    ![...data.top_five, ...data.overloaded].every(sameLoad) ||
    new Set(data.top_five.map((item) => item.id)).size !==
      data.top_five.length ||
    new Set(data.overloaded.map((item) => item.id)).size !==
      data.overloaded.length ||
    data.overloaded.length !==
      data.links.filter((item) => item.load > item.capacity).length ||
    !data.overloaded.every((item) => item.load > item.capacity) ||
    new Set(reported.map((item) => item.id)).size !== reported.length ||
    !reported.every((item) => {
      const expected = demands.get(item.id);
      return (
        expected?.source === item.source &&
        expected.target === item.target &&
        expected.units === item.units
      );
    }) ||
    !data.failed_endpoint_demands.every(
      (item) =>
        failure.kind === "node" &&
        (item.source === failure.id || item.target === failure.id),
    ) ||
    data.failed_endpoint_demands.length !==
      network.demands.filter(
        (item) =>
          failure.kind === "node" &&
          (item.source === failure.id || item.target === failure.id),
      ).length ||
    data.undeliverable.some(
      (item) =>
        failure.kind === "node" &&
        (item.source === failure.id || item.target === failure.id),
    )
  )
    throw new Error("API analysis does not match the network.");
  return data;
}
