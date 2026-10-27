// Simulate one request-local failure while retaining accessible findings and map state.
import { useEffect, useRef, useState } from "react";
import {
  type Analysis,
  type Failure,
  fetchAnalysis,
  type Network,
  type Reason,
} from "./api";
import { AnalysisReport, FailureControls } from "./FailureControls";
import { NetworkMap, nodeSymbols } from "./NetworkMap";

const reasons: Record<Reason, string> = {
  disconnected: "Disconnects network",
  undeliverable: "Demand undeliverable (may include failed-node endpoints)",
  overloaded: "Overloads a link",
};
const number = (value: number) =>
  value.toLocaleString("en-US", { maximumFractionDigits: 2 });

export function NetworkSummary({ network }: { network: Network }) {
  const critical = network.criticality.filter((item) => item.critical);
  return (
    <p className="network-summary">
      <strong>{network.nodes.length} nodes</strong> · {network.links.length}{" "}
      links · {network.demands.length} demands ·{" "}
      {number(network.demands.reduce((sum, item) => sum + item.units, 0))}{" "}
      demand units
      <span className="critical-summary">
        Critical: {critical.filter((item) => item.kind === "node").length} nodes
        · {critical.filter((item) => item.kind === "link").length} links
      </span>
    </p>
  );
}

export function NetworkWorkspace({ network }: { network: Network }) {
  const [selected, setSelected] = useState<Failure>({
    kind: "node",
    id: network.nodes[0]?.id ?? "",
  });
  const [state, setState] = useState<{
    analysis: Analysis;
    pending: Failure | null;
    error: string | null;
  }>({ analysis: network.baseline, pending: null, error: null });
  const request = useRef<AbortController | null>(null);
  useEffect(() => () => request.current?.abort(), []);
  function failSelected() {
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setState((previous) => ({ ...previous, pending: selected, error: null }));
    fetchAnalysis(network, selected, controller.signal).then(
      (analysis) => {
        if (!controller.signal.aborted)
          setState({ analysis, pending: null, error: null });
      },
      (error: unknown) => {
        if (!controller.signal.aborted)
          setState((previous) => ({
            ...previous,
            pending: null,
            error:
              error instanceof Error
                ? error.message
                : "Analysis request failed.",
          }));
      },
    );
  }
  function restore() {
    request.current?.abort();
    setState({ analysis: network.baseline, pending: null, error: null });
  }
  const { analysis, pending, error } = state;
  const critical = network.criticality.filter((item) => item.critical);
  if (network.nodes.length === 0)
    return <p role="status">No network data is available.</p>;
  return (
    <div className="workspace-columns">
      <div className="findings-grid">
        <section aria-labelledby="critical-heading" className="findings-panel">
          <h3 id="critical-heading">Critical elements (baseline)</h3>
          <p>
            {critical.filter((item) => item.kind === "node").length} nodes ·{" "}
            {critical.filter((item) => item.kind === "link").length} links
          </p>
          <p>
            Critical means loss disconnects the network, makes any demand
            undeliverable, or overloads a link. Losing a node's own endpoint
            demands counts too—not every critical node is a physical single
            point of disconnection.
          </p>
          {(["link", "node"] as const).map((kind) => (
            <details key={kind}>
              <summary>
                Critical {kind === "link" ? "links" : "nodes"} (
                {critical.filter((item) => item.kind === kind).length})
              </summary>
              <ul className="critical-list">
                {critical
                  .filter((item) => item.kind === kind)
                  .map((item) => {
                    const link =
                      kind === "link"
                        ? network.links.find((link) => link.id === item.id)
                        : undefined;
                    return (
                      <li key={item.id}>
                        <strong>
                          {link ? `${link.source} – ${link.target}` : item.id}
                        </strong>
                        {link && <small>{item.id}</small>}
                        <span>
                          {item.reasons
                            .map((reason) => reasons[reason])
                            .join(" · ")}
                        </span>
                      </li>
                    );
                  })}
              </ul>
            </details>
          ))}
          {critical.length === 0 && <p>No critical elements reported.</p>}
        </section>
        <FailureControls
          network={network}
          selected={selected}
          onSelect={setSelected}
          onFail={failSelected}
          onRestore={restore}
          analysis={analysis}
          pending={pending}
          error={error}
        />
      </div>
      <div className="map-column">
        <section aria-labelledby="map-heading" className="map-panel">
          <h3 id="map-heading">European network</h3>
          <p className="visually-hidden">
            Drag to pan; use +/− to zoom. Site positions are illustrative
            offsets near their attachments. Zoom in to separate nearby labels.
          </p>
          <p className="scenario-label">
            {analysis.failure
              ? `Failed ${analysis.failure.kind}: ${analysis.failure.id}`
              : "Baseline: all elements operational"}
          </p>
          <NetworkMap network={network} analysis={analysis} />
          <ul className="map-legend" aria-label="Map legend">
            <li>{nodeSymbols.backbone} Backbone city</li>
            <li>{nodeSymbols["operations-site"]} Operations site</li>
            <li>{nodeSymbols["data-center"]} Data center</li>
            <li>{nodeSymbols["aggregation-hub"]} Aggregation hub</li>
            <li>* Critical node</li>
            <li>Dashed line: critical link</li>
            <li>Thick line + #1–#5: most utilized</li>
            <li>× FAILED: failed node/link (incident links faded)</li>
            <li>! OVERLOAD: link above capacity</li>
          </ul>
        </section>
        <div className="findings-grid secondary-findings">
          <AnalysisReport analysis={analysis} />
          <section aria-labelledby="traffic-heading" className="findings-panel">
            <h3 id="traffic-heading">Five most utilized links</h3>
            {analysis.top_five.length === 0 ? (
              <p>No link utilization results.</p>
            ) : (
              <div className="table-scroll">
                <table>
                  <caption>
                    {analysis.failure ? "Failure scenario" : "Baseline"}{" "}
                    traffic, ranked by utilization
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Rank / link</th>
                      <th scope="col">Load / capacity</th>
                      <th scope="col">Utilization</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysis.top_five.map((item, index) => (
                      <tr key={item.id}>
                        <th scope="row">
                          #{index + 1} {item.source} – {item.target}
                          <small>{item.id}</small>
                        </th>
                        <td>
                          {number(item.load)} / {number(item.capacity)}
                        </td>
                        <td>{number(item.utilization_percent)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <p>
              Other undeliverable: {analysis.undeliverable.length} demands.
              Overloaded: {analysis.overloaded.length} links.
            </p>
            {analysis.disconnected && (
              <p role="alert">The displayed network is disconnected.</p>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
