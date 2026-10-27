// Baseline findings remain readable and accessible independently of the map tiles.
import type { Network, Reason } from "./api";
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
  const critical = network.criticality.filter((item) => item.critical);
  if (network.nodes.length === 0)
    return <p role="status">No network data is available.</p>;
  return (
    <>
      <div className="workspace-columns">
        <div className="findings-grid">
          <section
            aria-labelledby="critical-heading"
            className="findings-panel"
          >
            <h3 id="critical-heading">Critical elements</h3>
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
              <details key={kind} open={kind === "link"}>
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
          <section aria-labelledby="traffic-heading" className="findings-panel">
            <h3 id="traffic-heading">Five most utilized links</h3>
            {network.baseline.top_five.length === 0 ? (
              <p>No link utilization results.</p>
            ) : (
              <div className="table-scroll">
                <table>
                  <caption>Baseline traffic, ranked by utilization</caption>
                  <thead>
                    <tr>
                      <th scope="col">Rank / link</th>
                      <th scope="col">Load / capacity</th>
                      <th scope="col">Utilization</th>
                    </tr>
                  </thead>
                  <tbody>
                    {network.baseline.top_five.map((item, index) => (
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
              Undeliverable: {network.baseline.undeliverable.length} demands.
              Overloaded: {network.baseline.overloaded.length} links.
            </p>
            {network.baseline.disconnected && (
              <p role="alert">The baseline network is disconnected.</p>
            )}
          </section>
        </div>
        <section aria-labelledby="map-heading" className="map-panel">
          <h3 id="map-heading">European network</h3>
          <p>
            Drag to pan; use +/− to zoom. Site positions are illustrative
            offsets near their attachments. Zoom in to separate nearby labels.
          </p>
          <NetworkMap network={network} />
          <ul className="map-legend" aria-label="Map legend">
            <li>{nodeSymbols.backbone} Backbone city</li>
            <li>{nodeSymbols["operations-site"]} Operations site</li>
            <li>{nodeSymbols["data-center"]} Data center</li>
            <li>{nodeSymbols["aggregation-hub"]} Aggregation hub</li>
            <li>* Critical node</li>
            <li>Dashed line: critical link</li>
            <li>Thick line + #1–#5: most utilized</li>
          </ul>
        </section>
      </div>
      <p className="scope-note">
        Baseline analysis only. Interactive failure and restore controls are
        coming next.
      </p>
    </>
  );
}
